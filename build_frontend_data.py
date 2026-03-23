#!/usr/bin/env python3

"""Builds the static Next.js data bundle from predictions.json."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "predictions.json"
TARGET = ROOT / "app" / "data.json"

ROLE_MAP = {
    "Wicketkeeper": "WK",
    "Batter": "BAT",
    "Bowler": "BOWL",
    "All-Rounder": "AR",
}

TIER_MAP = {
    "Guaranteed Starter": "GUARANTEED",
    "Likely Starter": "LIKELY",
    "Rotation/Fringe": "ROTATION",
    "Unlikely to Play": "UNLIKELY",
}


def rounded(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def build_rankings(rankings: list[dict]) -> list[dict]:
    return [
        {
            "name": row["owner"],
            "total": rounded(row["total_points"], 1),
            "bat": rounded(row["total_batting_points"], 1),
            "bowl": rounded(row["total_bowling_points"], 1),
            "count": int(row["player_count"]),
            "rank": index,
        }
        for index, row in enumerate(rankings, start=1)
    ]


def build_players(predictions: list[dict]) -> list[dict]:
    players = []
    for row in predictions:
        players.append(
            {
                "n": row["nickname"],
                "fn": row["full_name"],
                "team": row["ipl_team"],
                "owner": row["fantasy_owner"],
                "role": ROLE_MAP.get(row["role"], row["role"]),
                "overseas": bool(row["is_overseas"]),
                "tier": TIER_MAP.get(row["playing_xi_tier"], row["playing_xi_tier"]),
                "avail": rounded(row["availability_modifier"]),
                "availNote": row["availability_note"],
                "conf": row["confidence"],
                "careerM": int(row["career_stats"]["matches"]),
                "careerR": int(row["career_stats"]["runs"]),
                "careerW": int(row["career_stats"]["wickets"]),
                "s25M": int(row["season_2025"]["matches"]),
                "s25R": int(row["season_2025"]["runs"]),
                "s25W": int(row["season_2025"]["wickets"]),
                "s24M": int(row["season_2024"]["matches"]),
                "s24R": int(row["season_2024"]["runs"]),
                "s24W": int(row["season_2024"]["wickets"]),
                "expMatches": rounded(row["expected_matches"]),
                "expBat": rounded(row["expected_batting_points"], 1),
                "expBowl": rounded(row["expected_bowling_points"], 1),
                "expTotal": rounded(row["expected_total_points"], 1),
                "runsPerM": rounded(row["weighted_runs_per_match"]),
                "wktsPerM": rounded(row["weighted_wickets_per_match"], 3),
                "debutant": bool(row["is_debutant"]),
            }
        )
    return players


def main() -> None:
    payload = json.loads(SOURCE.read_text())
    output = {
        "rankings": build_rankings(payload["rankings"]),
        "players": build_players(payload["all_predictions"]),
        "methodology": payload["methodology"],
    }
    TARGET.write_text(json.dumps(output, separators=(",", ":")))
    print(f"Wrote {TARGET.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
