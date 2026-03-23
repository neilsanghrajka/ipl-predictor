"""
Verification script for the CSV-first official IPL data pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from collect_data import load_players_from_registry_csv
from model import predict_all
from official_ipl import TEAM_NAMES, fetch_player_stats_feed, flatten_stat_row, parse_jsonp_payload
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
PLAYING_XI_BASIS = {"confirmed_role", "inferred_from_team_context", "conflicting_reports", "unknown"}
AVAILABILITY_BASIS = {
    "confirmed_available",
    "inferred_no_adverse_news",
    "injury_report",
    "late_joining",
    "tournament_conflict",
    "suspension",
    "conflicting_reports",
    "unknown",
}
RESEARCH_CONFIDENCE_VALUES = {"High", "Medium", "Low"}
RESEARCH_STATUS_VALUES = {"pending", "completed", "not_started"}
RAW_TEAM_DIR = Path("data/raw/team_research")
RAW_PLAYER_DIR = Path("data/raw/player_research")
RAW_FIXTURE_DIR = Path("data/raw/fixtures")
RAW_AVAILABILITY_REPAIR_DIR = Path("data/raw/availability_repair")
SOURCE_COLUMNS = [
    "playing_xi_source_urls",
    "availability_source_urls",
    "overseas_competition_source_urls",
]
SCHEDULE_ARTIFACT_MARKERS = (
    "published fixture",
    "published fixtures",
    "first-phase",
    "first phase",
    "part-1",
    "part 1",
    "only four fixtures",
    "only 4 fixtures",
    "schedule publication",
)
NO_CONCERN_BASIS = {"confirmed_available", "inferred_no_adverse_news", "unknown"}


def split_source_values(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def ensure_sources_present(field_value: str, field_name: str, index: int, errors: list[str]) -> None:
    sources = split_source_values(field_value)
    if not sources:
        errors.append(f"Row {index}: {field_name} must include at least one source URL")


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def ensure_artifact(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing raw artifact: {label} ({path})")


def load_json_file(path: Path, label: str, errors: list[str]) -> dict[str, object] | None:
    ensure_artifact(path, label, errors)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON in {label}: {exc}")
        return None


def expected_player_ids_by_team(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for row in rows:
        mapping.setdefault(row["ipl_team"], set()).add(row["official_player_id"])
    return mapping


def is_availability_repair_target(row: dict[str, str]) -> bool:
    if parse_float(row.get("availability_modifier"), 1.0) < 1.0:
        return True
    if parse_bool(row.get("needs_player_followup")):
        return True
    combined_text = " ".join(filter(None, [row.get("availability_note", ""), row.get("availability_comment", "")])).lower()
    return any(marker in combined_text for marker in SCHEDULE_ARTIFACT_MARKERS)


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


def test_phase2_fields(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []

    for index, row in enumerate(rows):
        research_status = (row.get("research_status", "").strip().lower() or "not_started")
        if research_status not in RESEARCH_STATUS_VALUES:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid research_status '{research_status}'")
            continue

        needs_followup = parse_bool(row.get("needs_player_followup"))
        if needs_followup is None:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): needs_player_followup must be boolean")
        elif needs_followup and research_status == "completed":
            if not row.get("followup_reason", "").strip():
                errors.append(f"Row {index} ({row.get('full_name', '?')}): followup_reason required when followup is true")
            if not row.get("followup_checked_at", "").strip():
                errors.append(f"Row {index} ({row.get('full_name', '?')}): followup_checked_at required for followups")

        if research_status != "completed":
            continue

        if row.get("research_confidence") not in RESEARCH_CONFIDENCE_VALUES:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid research_confidence")

        if row.get("playing_xi_basis") not in PLAYING_XI_BASIS:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid playing_xi_basis")

        ensure_sources_present(row.get("playing_xi_source_urls", ""), "playing_xi_source_urls", index, errors)

        if row.get("availability_basis") not in AVAILABILITY_BASIS:
            errors.append(f"Row {index} ({row.get('full_name', '?')}): invalid availability_basis")

        ensure_sources_present(row.get("availability_source_urls", ""), "availability_source_urls", index, errors)

        expected_matches = parse_int(row.get("availability_expected_matches_available"))
        if not (0 <= expected_matches <= 14):
            errors.append(
                f"Row {index} ({row.get('full_name', '?')}): availability_expected_matches_available must be 0-14"
            )

        if row.get("overseas_competition_basis") == "":
            errors.append(f"Row {index} ({row.get('full_name', '?')}): missing overseas_competition_basis")

        ensure_sources_present(
            row.get("overseas_competition_source_urls", ""), "overseas_competition_source_urls", index, errors
        )

        if not row.get("research_model", "").strip():
            errors.append(f"Row {index} ({row.get('full_name', '?')}): research_model is empty")

    return errors


def test_raw_artifacts(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    team_touched: dict[str, bool] = {}
    expected_ids = expected_player_ids_by_team(rows)

    for row in rows:
        team = row["ipl_team"]
        research_status = (row.get("research_status", "").strip().lower() or "not_started")
        if research_status in {"completed", "pending"}:
            team_touched[team] = True
        official_player_id = row.get("official_player_id", "")
        if row.get("followup_checked_at", "").strip() and official_player_id:
            ensure_artifact(RAW_PLAYER_DIR / f"{official_player_id}.json", f"player_research/{official_player_id}.json", errors)

    for team in IPL_TEAMS:
        if team_touched.get(team):
            ensure_artifact(RAW_TEAM_DIR / f"{team}.json", f"team_research/{team}.json", errors)
            ensure_artifact(RAW_FIXTURE_DIR / f"{team}.json", f"fixtures/{team}.json", errors)

    return errors


def test_raw_inputs(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    touched_teams = {
        row["ipl_team"]
        for row in rows
        if (row.get("research_status", "").strip().lower() or "not_started") in {"completed", "pending"}
    }
    if not touched_teams:
        return errors

    competition_path = RAW_FIXTURE_DIR / "competition.js"
    schedule_files = sorted(RAW_FIXTURE_DIR.glob("*-matchschedule.js"))
    ensure_artifact(competition_path, "fixtures/competition.js", errors)
    if not schedule_files:
        errors.append("Missing raw fixture schedule feed under data/raw/fixtures/*-matchschedule.js")
        return errors

    if not competition_path.exists():
        return errors

    try:
        competition_payload = parse_jsonp_payload(competition_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSONP in fixtures/competition.js: {exc}")
        return errors

    competitions = competition_payload.get("competition", []) if isinstance(competition_payload, dict) else []
    competition_2026 = None
    for item in competitions:
        if isinstance(item, dict) and str(item.get("CompetitionName", "")).endswith("2026"):
            competition_2026 = item
            break
    if competition_2026 is None:
        errors.append("Raw competition.js does not include IPL 2026")
        return errors

    competition_id = str(competition_2026.get("CompetitionID", "")).strip()
    if not competition_id:
        errors.append("IPL 2026 competition in competition.js has no CompetitionID")
        return errors

    schedule_path = RAW_FIXTURE_DIR / f"{competition_id}-matchschedule.js"
    ensure_artifact(schedule_path, f"fixtures/{competition_id}-matchschedule.js", errors)
    if not schedule_path.exists():
        return errors

    try:
        schedule_payload = parse_jsonp_payload(schedule_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSONP in fixtures/{competition_id}-matchschedule.js: {exc}")
        return errors

    matches = schedule_payload.get("Matchsummary", []) if isinstance(schedule_payload, dict) else []
    if not isinstance(matches, list) or not matches:
        errors.append("Schedule feed does not include Matchsummary rows")
        return errors

    expected_fixture_counts = {team: 0 for team in IPL_TEAMS}
    for match in matches:
        if not isinstance(match, dict):
            continue
        first_code = str(match.get("FirstBattingTeamCode", "")).upper()
        second_code = str(match.get("SecondBattingTeamCode", "")).upper()
        if first_code in expected_fixture_counts:
            expected_fixture_counts[first_code] += 1
        if second_code in expected_fixture_counts:
            expected_fixture_counts[second_code] += 1

    for team in touched_teams:
        fixture_path = RAW_FIXTURE_DIR / f"{team}.json"
        bundle = load_json_file(fixture_path, f"fixtures/{team}.json", errors)
        if bundle is None:
            continue
        if bundle.get("team") != team:
            errors.append(f"fixtures/{team}.json has mismatched team {bundle.get('team')!r}")
        if bundle.get("team_name") != TEAM_NAMES.get(team):
            errors.append(f"fixtures/{team}.json has mismatched team_name {bundle.get('team_name')!r}")
        if str(bundle.get("competition_id", "")).strip() != competition_id:
            errors.append(f"fixtures/{team}.json has competition_id {bundle.get('competition_id')!r}, expected {competition_id!r}")
        fixtures = bundle.get("fixtures", [])
        if not isinstance(fixtures, list):
            errors.append(f"fixtures/{team}.json fixtures must be a list")
            continue
        published_count = parse_int(bundle.get("published_fixture_count"))
        if published_count != len(fixtures):
            errors.append(f"fixtures/{team}.json published_fixture_count does not match fixtures length")
        if len(fixtures) != expected_fixture_counts.get(team, 0):
            errors.append(
                f"fixtures/{team}.json count {len(fixtures)} does not match schedule feed count {expected_fixture_counts.get(team, 0)}"
            )
        previous_date = ""
        for fixture in fixtures:
            if not isinstance(fixture, dict):
                errors.append(f"fixtures/{team}.json contains a non-object fixture")
                continue
            if fixture.get("team_code") != team:
                errors.append(f"fixtures/{team}.json fixture has team_code {fixture.get('team_code')!r}")
            if str(fixture.get("match_status", "")).strip() == "":
                errors.append(f"fixtures/{team}.json fixture missing match_status")
            match_date = str(fixture.get("match_date", ""))
            if not match_date:
                errors.append(f"fixtures/{team}.json fixture missing match_date")
            elif previous_date and match_date < previous_date:
                errors.append(f"fixtures/{team}.json fixtures are not sorted by match_date")
            previous_date = match_date

    expected_ids = expected_player_ids_by_team(rows)
    for team in touched_teams:
        team_path = RAW_TEAM_DIR / f"{team}.json"
        bundle = load_json_file(team_path, f"team_research/{team}.json", errors)
        if bundle is None:
            continue
        request = bundle.get("request")
        parsed = bundle.get("parsed")
        if not isinstance(request, dict) or not isinstance(parsed, dict):
            errors.append(f"team_research/{team}.json must include request and parsed objects")
            continue
        if str(request.get("model", "")).strip() == "":
            errors.append(f"team_research/{team}.json request is missing model")
        tools = request.get("tools", [])
        if not isinstance(tools, list) or not any(isinstance(tool, dict) and tool.get("type") == "web_search" for tool in tools):
            errors.append(f"team_research/{team}.json request does not include web_search")
        text_format = (((request.get("text") or {}) if isinstance(request.get("text"), dict) else {}).get("format"))
        if not isinstance(text_format, dict) or text_format.get("type") != "json_schema":
            errors.append(f"team_research/{team}.json request does not use structured json_schema output")
        parsed_team = str(parsed.get("team", "")).strip()
        if parsed_team not in {team, TEAM_NAMES.get(team, "")}:
            errors.append(f"team_research/{team}.json parsed team is {parsed.get('team')!r}")
        players = parsed.get("players", [])
        if not isinstance(players, list):
            errors.append(f"team_research/{team}.json parsed players must be a list")
            continue
        parsed_ids = {str(player.get("official_player_id", "")) for player in players if isinstance(player, dict)}
        if parsed_ids != expected_ids.get(team, set()):
            errors.append(f"team_research/{team}.json parsed player IDs do not match registry for {team}")

    for row in rows:
        if not row.get("followup_checked_at", "").strip():
            continue
        player_id = row["official_player_id"]
        bundle = load_json_file(RAW_PLAYER_DIR / f"{player_id}.json", f"player_research/{player_id}.json", errors)
        if bundle is None:
            continue
        request = bundle.get("request")
        parsed = bundle.get("parsed")
        if not isinstance(request, dict) or not isinstance(parsed, dict):
            errors.append(f"player_research/{player_id}.json must include request and parsed objects")
            continue
        tools = request.get("tools", [])
        if not isinstance(tools, list) or not any(isinstance(tool, dict) and tool.get("type") == "web_search" for tool in tools):
            errors.append(f"player_research/{player_id}.json request does not include web_search")
        if str(parsed.get("official_player_id", "")).strip() != player_id:
            errors.append(f"player_research/{player_id}.json parsed official_player_id mismatch")
        if str(parsed.get("full_name", "")).strip() != row["full_name"]:
            errors.append(f"player_research/{player_id}.json parsed full_name mismatch for {row['full_name']}")

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


def test_availability_contamination(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    row_by_name = {row["full_name"]: row for row in rows}

    for row in rows:
        availability_modifier = parse_float(row.get("availability_modifier"), 1.0)
        if availability_modifier >= 1.0:
            continue
        basis = row.get("availability_basis", "")
        combined_text = " ".join(
            filter(
                None,
                [
                    row.get("availability_note", ""),
                    row.get("availability_comment", ""),
                ],
            )
        ).lower()
        if basis in NO_CONCERN_BASIS and any(marker in combined_text for marker in SCHEDULE_ARTIFACT_MARKERS):
            errors.append(
                f"Availability contamination: {row['full_name']} has availability_modifier={availability_modifier:.2f} "
                f"with basis={basis!r} but explanation only references partial schedule publication"
            )

    for full_name in ("Sunil Narine", "Rinku Singh", "Varun Chakaravarthy", "Ajinkya Rahane"):
        row = row_by_name.get(full_name)
        if row is None or row.get("ipl_team") != "KKR":
            continue
        availability_modifier = parse_float(row.get("availability_modifier"), 1.0)
        basis = row.get("availability_basis", "")
        if availability_modifier < 1.0 and basis in NO_CONCERN_BASIS:
            errors.append(
                f"Availability contamination: KKR core player {full_name} still has availability_modifier={availability_modifier:.2f}"
            )

    for path in sorted(RAW_AVAILABILITY_REPAIR_DIR.glob("*.json")):
        bundle = load_json_file(path, f"availability_repair/{path.name}", errors)
        if bundle is None:
            continue
        request = bundle.get("request")
        parsed = bundle.get("parsed")
        if not isinstance(request, dict) or not isinstance(parsed, dict):
            errors.append(f"availability_repair/{path.name} must include request and parsed objects")
            continue
        tools = request.get("tools", [])
        if not isinstance(tools, list) or not any(isinstance(tool, dict) and tool.get("type") == "web_search" for tool in tools):
            errors.append(f"availability_repair/{path.name} request does not include web_search")
        text_format = (((request.get("text") or {}) if isinstance(request.get("text"), dict) else {}).get("format"))
        if not isinstance(text_format, dict) or text_format.get("type") != "json_schema":
            errors.append(f"availability_repair/{path.name} request does not use structured json_schema output")
        player_id = str(parsed.get("official_player_id", "")).strip()
        if path.stem != player_id:
            errors.append(f"availability_repair/{path.name} parsed official_player_id mismatch")

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
        ("Phase 2 Field Validation", test_phase2_fields),
        ("Spot-Check Against Official IPL Feeds", test_spot_checks),
        ("Sanity Checks", test_sanity),
        ("Availability Contamination Checks", test_availability_contamination),
        ("Raw Artifact Coverage", test_raw_artifacts),
        ("Raw Input Verification", test_raw_inputs),
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
