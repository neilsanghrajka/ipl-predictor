"""
Run the full prediction model on canonical CSV data.

Input: player_registry.csv
Output: predictions.json
"""

from __future__ import annotations

import json

from collect_data import load_player_objects
from model import predict_all


def main() -> None:
    players = load_player_objects("player_registry.csv")
    print(f"Loaded {len(players)} players from player_registry.csv")

    results = predict_all(players)

    with open("predictions.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print("\n" + "=" * 60)
    print("IPL 2026 FANTASY DRAFT — PREDICTED RANKINGS")
    print("=" * 60)
    print(f"{'Rank':<6}{'Owner':<12}{'Total Pts':<12}{'Batting':<12}{'Bowling':<12}{'Players'}")
    print("-" * 60)

    for index, owner in enumerate(results["rankings"], 1):
        print(
            f"{index:<6}{owner['owner']:<12}{owner['total_points']:<12.0f}"
            f"{owner['total_batting_points']:<12.0f}{owner['total_bowling_points']:<12.0f}"
            f"{owner['player_count']}"
        )

    print("\n" + "=" * 60)
    print("PREDICTED WINNER:", results["rankings"][0]["owner"])
    print("=" * 60)

    all_predictions = sorted(
        results["all_predictions"],
        key=lambda prediction: prediction["expected_total_points"],
        reverse=True,
    )
    print(f"\n{'Rank':<6}{'Player':<25}{'Owner':<12}{'Team':<6}{'Exp Pts':<10}{'Matches':<10}{'Tier'}")
    print("-" * 75)
    for index, player in enumerate(all_predictions[:20], 1):
        print(
            f"{index:<6}{player['full_name']:<25}{player['fantasy_owner']:<12}{player['ipl_team']:<6}"
            f"{player['expected_total_points']:<10.0f}{player['expected_matches']:<10.1f}"
            f"{player['playing_xi_tier']}"
        )


if __name__ == "__main__":
    main()
