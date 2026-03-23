#!/usr/bin/env python3

"""Builds the static Next.js data bundle from predictions.json + player_registry.csv."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "predictions.json"
CSV_SOURCE = ROOT / "player_registry.csv"
TARGET = ROOT / "ipl-fantasy-site" / "app" / "data.json"

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


def load_csv_stats() -> dict[str, dict]:
    """Load batting/bowling averages from the CSV registry, keyed by full_name."""
    stats: dict[str, dict] = {}
    with open(CSV_SOURCE, newline="") as f:
        for row in csv.DictReader(f):
            name = row["full_name"]
            stats[name] = {
                # Career batting
                "cBatInn": safe_int(row.get("career_batting_innings")),
                "cBatAvg": safe_float(row.get("career_batting_average")),
                "cBatSR": safe_float(row.get("career_batting_strike_rate")),
                "cBatHS": safe_int(row.get("career_batting_high_score")),
                "cBat4s": safe_int(row.get("career_batting_fours")),
                "cBat6s": safe_int(row.get("career_batting_sixes")),
                # Career bowling
                "cBowlInn": safe_int(row.get("career_bowling_innings")),
                "cBowlAvg": safe_float(row.get("career_bowling_average")),
                "cBowlEcon": safe_float(row.get("career_bowling_economy")),
                "cBowlSR": safe_float(row.get("career_bowling_strike_rate")),
                "cBowlBB": row.get("career_bowling_best_bowling", ""),
                # 2025 batting
                "s25BatInn": safe_int(row.get("season_2025_batting_innings")),
                "s25BatAvg": safe_float(row.get("season_2025_batting_average")),
                "s25BatSR": safe_float(row.get("season_2025_batting_strike_rate")),
                "s25BatHS": safe_int(row.get("season_2025_batting_high_score")),
                # 2025 bowling
                "s25BowlInn": safe_int(row.get("season_2025_bowling_innings")),
                "s25BowlAvg": safe_float(row.get("season_2025_bowling_average")),
                "s25BowlEcon": safe_float(row.get("season_2025_bowling_economy")),
                "s25BowlSR": safe_float(row.get("season_2025_bowling_strike_rate")),
                # 2024 batting
                "s24BatInn": safe_int(row.get("season_2024_batting_innings")),
                "s24BatAvg": safe_float(row.get("season_2024_batting_average")),
                "s24BatSR": safe_float(row.get("season_2024_batting_strike_rate")),
                "s24BatHS": safe_int(row.get("season_2024_batting_high_score")),
                # 2024 bowling
                "s24BowlInn": safe_int(row.get("season_2024_bowling_innings")),
                "s24BowlAvg": safe_float(row.get("season_2024_bowling_average")),
                "s24BowlEcon": safe_float(row.get("season_2024_bowling_economy")),
                "s24BowlSR": safe_float(row.get("season_2024_bowling_strike_rate")),
            }
    return stats


def safe_float(val: str | None) -> float | None:
    if not val or val.strip() == "":
        return None
    try:
        return round(float(val), 2)
    except ValueError:
        return None


def safe_int(val: str | None) -> int | None:
    if not val or val.strip() == "":
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def build_players(predictions: list[dict], csv_stats: dict[str, dict]) -> list[dict]:
    players = []
    for row in predictions:
        name = row["full_name"]
        cs = csv_stats.get(name, {})
        players.append(
            {
                "n": row["nickname"],
                "fn": name,
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
                # Enriched stats from CSV
                **{k: v for k, v in cs.items() if v is not None},
            }
        )
    return players


def main() -> None:
    payload = json.loads(SOURCE.read_text())
    csv_stats = load_csv_stats()
    output = {
        "rankings": build_rankings(payload["rankings"]),
        "players": build_players(payload["all_predictions"], csv_stats),
        "methodology": payload["methodology"],
    }
    TARGET.write_text(json.dumps(output, separators=(",", ":")))
    print(f"Wrote {TARGET.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
