"""
Verification script for the CSV-first official IPL data pipeline.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from collect_data import load_players_from_registry_csv
from model import predict_all
from official_ipl import fetch_player_stats_feed, flatten_stat_row
from registry_csv import FIELDNAMES, parse_float, parse_int, read_registry_csv, season_matches_from_row


IPL_TEAMS = {"CSK", "MI", "SRH", "RCB", "PBKS", "RR", "DC", "KKR", "LSG", "GT"}
VALID_TIERS = {"GUARANTEED", "LIKELY", "ROTATION", "UNLIKELY"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}
SPOT_CHECK_PLAYERS = [
    "Virat Kohli",
    "Jasprit Bumrah",
    "Ravindra Jadeja",
    "Sunil Narine",
    "Rishabh Pant",
]


def test_schema(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for index, row in enumerate(rows):
        key = (row["fantasy_owner"], row["ipl_team"], row["nickname"])
        if key in seen_keys:
            errors.append(f"Duplicate draft slot detected: {key}")
        seen_keys.add(key)

        missing_columns = [field for field in FIELDNAMES if field not in row]
        if missing_columns:
            errors.append(f"Row {index} missing expected columns: {missing_columns}")

        if row.get("ipl_team") not in IPL_TEAMS:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid IPL team '{row.get('ipl_team')}'")

        if row.get("playing_xi_tier") not in VALID_TIERS:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid playing_xi_tier")

        if row.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid confidence")

        availability_modifier = parse_float(row.get("availability_modifier"), -1.0)
        if not (0.0 <= availability_modifier <= 1.0):
            errors.append(f"Row {index} ({row.get('full_name', '?')}): availability_modifier out of range")

        for field in ("official_player_id", "official_player_url", "official_stats_feed_url"):
            if not row.get(field, "").strip():
                errors.append(f"Row {index} ({row.get('full_name', '?')}): missing {field}")

        for field in ("stats_source", "stats_fetched_at", "stats_status"):
            if not row.get(field, "").strip():
                errors.append(f"Row {index} ({row.get('full_name', '?')}): empty {field}")

    return errors


def test_sanity(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    team_counts: dict[str, int] = {}

    for row in rows:
        full_name = row["full_name"]
        team_counts[row["ipl_team"]] = team_counts.get(row["ipl_team"], 0) + 1

        for season_key in ("season_2025", "season_2024"):
            batting_runs = parse_int(row.get(f"{season_key}_batting_runs"))
            wickets = parse_int(row.get(f"{season_key}_bowling_wickets"))
            if batting_runs > 1000:
                errors.append(f"Sanity: {full_name} has {batting_runs} runs in {season_key}")
            if wickets > 35:
                errors.append(f"Sanity: {full_name} has {wickets} wickets in {season_key}")

        career_runs = parse_int(row.get("career_batting_runs"))
        recent_runs = parse_int(row.get("season_2025_batting_runs")) + parse_int(row.get("season_2024_batting_runs"))
        if career_runs > 0 and career_runs < recent_runs:
            errors.append(f"Sanity: {full_name} career runs ({career_runs}) < 2024+2025 runs ({recent_runs})")

        career_matches = season_matches_from_row(row, "career")
        recent_matches = season_matches_from_row(row, "season_2025") + season_matches_from_row(row, "season_2024")
        if career_matches > 0 and career_matches < recent_matches:
            errors.append(f"Sanity: {full_name} career matches ({career_matches}) < 2024+2025 matches ({recent_matches})")

    for team, count in team_counts.items():
        if count < 10:
            errors.append(f"Sanity: {team} only has {count} players in the registry")

    return errors


def test_spot_checks(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    row_by_name = {row["full_name"]: row for row in rows}

    for full_name in SPOT_CHECK_PLAYERS:
        row = row_by_name.get(full_name)
        if row is None:
            errors.append(f"Spot-check: {full_name} not found in player_registry.csv")
            continue

        payload = fetch_player_stats_feed(
            player_id=row["official_player_id"],
            stats_feed_url=row["official_stats_feed_url"],
            raw_dir=None,
        )
        if payload is None:
            errors.append(f"Spot-check: official stats feed missing for {full_name}")
            continue

        expected = {}
        for season_key in ("career", "season_2025", "season_2024"):
            expected.update(flatten_stat_row(payload=payload, season_key=season_key))

        for field in (
            "career_batting_matches",
            "career_batting_runs",
            "career_bowling_wickets",
            "season_2025_batting_runs",
            "season_2024_batting_runs",
        ):
            if row.get(field, "") != expected.get(field, ""):
                errors.append(
                    f"Spot-check {full_name}: {field}={row.get(field, '')!r} "
                    f"does not match official={expected.get(field, '')!r}"
                )

    return errors


def test_model_e2e() -> list[str]:
    errors: list[str] = []
    try:
        players = load_players_from_registry_csv("player_registry.csv")
        results = predict_all(players)

        owners_found = {item["owner"] for item in results["rankings"]}
        expected_owners = {"Manan", "Akshit", "Saurabh", "Vyom", "Harsh", "Dharmik", "Dharmil"}
        if owners_found != expected_owners:
            errors.append(f"E2E: owner mismatch {owners_found} != {expected_owners}")

        for owner in results["rankings"]:
            total_points = owner["total_points"]
            if total_points < 500:
                errors.append(f"E2E: {owner['owner']} has suspiciously low points: {total_points}")
            if total_points > 15000:
                errors.append(f"E2E: {owner['owner']} has suspiciously high points: {total_points}")
    except Exception as exc:
        errors.append(f"E2E: model execution failed: {exc}")
    return errors


def main() -> None:
    print("=" * 60)
    print("IPL Fantasy Predictor — CSV Verification")
    print("=" * 60)

    rows = read_registry_csv("player_registry.csv")
    if not rows:
        print("\n❌ player_registry.csv not found or empty. Run build_registry_csv.py first.")
        sys.exit(1)

    print(f"\nLoaded {len(rows)} rows from player_registry.csv")

    total_errors = 0
    for label, check in [
        ("Schema Validation", test_schema),
        ("Spot-Check Against Official IPL Feeds", test_spot_checks),
        ("Sanity Checks", test_sanity),
    ]:
        print(f"\n--- {label} ---")
        errors = check(rows)
        total_errors += len(errors)
        if errors:
            for error in errors[:20]:
                print(f"  ❌ {error}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more")
        else:
            print("  ✅ Passed")

    print("\n--- End-to-End Model Run ---")
    errors = test_model_e2e()
    total_errors += len(errors)
    if errors:
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("  ✅ Passed")

    print(f"\n{'=' * 60}")
    if total_errors == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {total_errors} ERRORS FOUND")
    print(f"{'=' * 60}")
    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
