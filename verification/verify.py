"""
Verification script for player_data.json

Runs 4 test suites:
  1. Schema validation — correct fields, types, enums
  2. Spot-check — 5 known players within ±tolerance of expected stats
  3. Sanity checks — no impossible values
  4. End-to-end — model produces valid rankings

Usage:
  python verification/verify.py
"""

import json
import sys
import os

VALID_TIERS = {"GUARANTEED", "LIKELY", "ROTATION", "UNLIKELY"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}
IPL_TEAMS = {"CSK", "MI", "SRH", "RCB", "PBKS", "RR", "DC", "KKR", "LSG", "GT"}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def test_schema(players):
    """Test 1: Every player has required fields with valid types."""
    errors = []
    required_fields = [
        ("nickname", str), ("full_name", str), ("ipl_team", str),
        ("fantasy_owner", str), ("role", str), ("is_overseas", bool),
        ("playing_xi_tier", str), ("availability_modifier", (int, float)),
        ("stats_source", str), ("confidence", str),
    ]
    season_fields = ["season", "matches", "innings_batted", "runs", "innings_bowled", "wickets"]

    for i, p in enumerate(players):
        for field, expected_type in required_fields:
            if field not in p:
                errors.append(f"Player {i} ({p.get('nickname', '?')}): missing field '{field}'")
            elif not isinstance(p[field], expected_type):
                errors.append(f"Player {i} ({p['nickname']}): '{field}' has wrong type {type(p[field])}")

        # Check tier values
        if p.get("playing_xi_tier") not in VALID_TIERS:
            errors.append(f"Player {i} ({p['nickname']}): invalid tier '{p.get('playing_xi_tier')}'")

        if p.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"Player {i} ({p['nickname']}): invalid confidence '{p.get('confidence')}'")

        # Check availability_modifier range
        am = p.get("availability_modifier", -1)
        if not (0.0 <= am <= 1.0):
            errors.append(f"Player {i} ({p['nickname']}): availability_modifier {am} out of range [0,1]")

        # Check season stat objects
        for season_key in ["season_2025", "season_2024", "career_stats"]:
            if season_key not in p:
                errors.append(f"Player {i} ({p['nickname']}): missing '{season_key}'")
            else:
                for sf in season_fields:
                    if sf not in p[season_key]:
                        errors.append(f"Player {i} ({p['nickname']}): {season_key} missing '{sf}'")
                    elif sf != "season" and p[season_key][sf] < 0:
                        errors.append(f"Player {i} ({p['nickname']}): {season_key}.{sf} is negative")

        # Check stats_source is non-empty
        if not p.get("stats_source", "").strip():
            errors.append(f"Player {i} ({p['nickname']}): stats_source is empty")

    return errors


def test_spot_checks(players, expected_samples):
    """Test 2: Known players' stats are within tolerance."""
    errors = []
    player_map = {p["full_name"]: p for p in players}

    for sample in expected_samples:
        name = sample["full_name"]
        if name not in player_map:
            errors.append(f"Spot-check: {name} not found in player_data.json")
            continue

        p = player_map[name]
        tol = sample["tolerance_pct"]

        checks = [
            ("career_stats.matches", p["career_stats"]["matches"], sample["career_matches_expected"]),
            ("career_stats.runs", p["career_stats"]["runs"], sample["career_runs_expected"]),
            ("career_stats.wickets", p["career_stats"]["wickets"], sample["career_wickets_expected"]),
            ("season_2025.runs", p["season_2025"]["runs"], sample["season_2025_runs_expected"]),
            ("season_2024.runs", p["season_2024"]["runs"], sample["season_2024_runs_expected"]),
        ]

        for field, actual, expected in checks:
            if expected == 0:
                if actual > 10:  # Allow small noise for zero-expected fields
                    errors.append(f"Spot-check {name}: {field} = {actual}, expected ~0")
            else:
                diff_pct = abs(actual - expected) / expected
                if diff_pct > tol:
                    errors.append(
                        f"Spot-check {name}: {field} = {actual}, expected ~{expected} "
                        f"(off by {diff_pct*100:.1f}%, tolerance {tol*100:.0f}%)"
                    )

    return errors


def test_sanity(players):
    """Test 3: No impossible values."""
    errors = []

    for p in players:
        name = p["full_name"]

        # No season should have >1000 runs (record is ~973)
        for key in ["season_2025", "season_2024"]:
            if p[key]["runs"] > 1000:
                errors.append(f"Sanity: {name} has {p[key]['runs']} runs in {key} (max ever ~973)")

        # No season should have >35 wickets
        for key in ["season_2025", "season_2024"]:
            if p[key]["wickets"] > 35:
                errors.append(f"Sanity: {name} has {p[key]['wickets']} wickets in {key} (max ever ~32)")

        # Career runs should be >= sum of individual seasons
        s25_runs = p["season_2025"]["runs"]
        s24_runs = p["season_2024"]["runs"]
        career_runs = p["career_stats"]["runs"]
        if career_runs > 0 and career_runs < (s25_runs + s24_runs) * 0.9:
            errors.append(f"Sanity: {name} career runs ({career_runs}) < sum of 2024+2025 ({s24_runs + s25_runs})")

        # IPL team should be valid
        if p["ipl_team"] not in IPL_TEAMS:
            errors.append(f"Sanity: {name} has invalid IPL team '{p['ipl_team']}'")

    # Check all teams have enough players
    team_counts = {}
    for p in players:
        team_counts[p["ipl_team"]] = team_counts.get(p["ipl_team"], 0) + 1

    for team, count in team_counts.items():
        if count < 10:
            errors.append(f"Sanity: {team} only has {count} players in dataset (expected 15+)")

    return errors


def test_model_e2e(players):
    """Test 4: Run the model and check output is reasonable."""
    errors = []

    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from collect_data import dict_to_player_data
        from model import predict_all

        player_objs = [dict_to_player_data(d) for d in players]
        results = predict_all(player_objs)

        # Check all 7 owners appear
        owners_found = {r["owner"] for r in results["rankings"]}
        expected_owners = {"Manan", "Akshit", "Saurabh", "Vyom", "Harsh", "Dharmik", "Dharmil"}
        if owners_found != expected_owners:
            errors.append(f"E2E: Missing owners: {expected_owners - owners_found}")

        # Check total points are reasonable (2000-10000 per owner)
        for owner in results["rankings"]:
            pts = owner["total_points"]
            if pts < 500:
                errors.append(f"E2E: {owner['owner']} has suspiciously low points: {pts}")
            if pts > 15000:
                errors.append(f"E2E: {owner['owner']} has suspiciously high points: {pts}")

    except Exception as e:
        errors.append(f"E2E: Model execution failed: {e}")

    return errors


def main():
    print("=" * 60)
    print("IPL Fantasy Predictor — Data Verification")
    print("=" * 60)

    # Load data
    try:
        players = load_json("player_data.json")
    except FileNotFoundError:
        print("\n❌ player_data.json not found. Run fetch_player_data.py first.")
        sys.exit(1)

    expected = load_json("verification/expected_samples.json")

    print(f"\nLoaded {len(players)} players from player_data.json")

    total_errors = 0

    # Test 1
    print(f"\n--- Test 1: Schema Validation ---")
    errors = test_schema(players)
    total_errors += len(errors)
    if errors:
        for e in errors[:10]:
            print(f"  ❌ {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")
    else:
        print(f"  ✅ All {len(players)} players pass schema validation")

    # Test 2
    print(f"\n--- Test 2: Spot-Check Known Players ---")
    errors = test_spot_checks(players, expected)
    total_errors += len(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ All {len(expected)} spot-checks pass")

    # Test 3
    print(f"\n--- Test 3: Sanity Checks ---")
    errors = test_sanity(players)
    total_errors += len(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ All sanity checks pass")

    # Test 4
    print(f"\n--- Test 4: End-to-End Model Run ---")
    errors = test_model_e2e(players)
    total_errors += len(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ Model runs successfully and produces valid rankings")

    # Summary
    print(f"\n{'=' * 60}")
    if total_errors == 0:
        print(f"✅ ALL TESTS PASSED")
    else:
        print(f"❌ {total_errors} ERRORS FOUND")
    print(f"{'=' * 60}")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
