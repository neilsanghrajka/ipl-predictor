"""
Run the full prediction model on collected player data.

Input: player_data.json (filled by fetch_player_data.py)
Output: predictions.json (rankings + per-player breakdowns)
"""

import json
from collect_data import dict_to_player_data, run_predictions


def main():
    with open("player_data.json") as f:
        players_raw = json.load(f)

    print(f"Loaded {len(players_raw)} players")

    players = [dict_to_player_data(d) for d in players_raw]

    from model import predict_all
    results = predict_all(players)

    with open("predictions.json", "w") as f:
        json.dump(results, f, indent=2)

    # Print rankings
    print("\n" + "=" * 60)
    print("IPL 2026 FANTASY DRAFT — PREDICTED RANKINGS")
    print("=" * 60)
    print(f"{'Rank':<6}{'Owner':<12}{'Total Pts':<12}{'Batting':<12}{'Bowling':<12}{'Players'}")
    print("-" * 60)

    for i, owner in enumerate(results["rankings"], 1):
        print(f"{i:<6}{owner['owner']:<12}{owner['total_points']:<12.0f}"
              f"{owner['total_batting_points']:<12.0f}{owner['total_bowling_points']:<12.0f}"
              f"{owner['player_count']}")

    print("\n" + "=" * 60)
    print("PREDICTED WINNER:", results["rankings"][0]["owner"])
    print("=" * 60)

    # Top 10 individual players
    all_preds = sorted(results["all_predictions"], key=lambda x: x["expected_total_points"], reverse=True)
    print(f"\n{'Rank':<6}{'Player':<25}{'Owner':<12}{'Team':<6}{'Exp Pts':<10}{'Matches':<10}{'Tier'}")
    print("-" * 75)
    for i, p in enumerate(all_preds[:20], 1):
        print(f"{i:<6}{p['full_name']:<25}{p['fantasy_owner']:<12}{p['ipl_team']:<6}"
              f"{p['expected_total_points']:<10.0f}{p['expected_matches']:<10.1f}{p['playing_xi_tier']}")


if __name__ == "__main__":
    main()
