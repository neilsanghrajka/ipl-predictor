"""
STUB — You implement this.

Fetches real IPL stats for all 186 players and outputs player_data.json.

See PRD.md for the full specification.

Input: player_templates.json (186 players with search queries)
Output: player_data.json (same schema, stats filled in)

Recommended approach:
1. Use iplt20.com player pages as primary source
2. Fall back to espncricinfo or Google search
3. Parallelize with asyncio or concurrent.futures (10-20 workers)
4. Rate limit to avoid getting blocked

URL patterns:
  iplt20.com:    https://www.iplt20.com/players/{firstname-lastname}/{id}
  espncricinfo:  https://www.espncricinfo.com/cricketers/{name}-{id}
"""

import json


def fetch_career_stats(full_name: str) -> dict:
    """
    Fetch IPL career stats for a player.

    Returns:
    {
        "career": {"matches": int, "innings_batted": int, "runs": int, "innings_bowled": int, "wickets": int},
        "season_2025": {"matches": int, "innings_batted": int, "runs": int, "innings_bowled": int, "wickets": int},
        "season_2024": {"matches": int, "innings_batted": int, "runs": int, "innings_bowled": int, "wickets": int},
        "source_url": str,
    }
    """
    # TODO: Implement — scrape iplt20.com or espncricinfo
    raise NotImplementedError


def fetch_injury_status(full_name: str) -> dict:
    """
    Check current injury/fitness status for a player.

    Returns:
    {
        "availability_modifier": float,  # 0.0 to 1.0
        "availability_note": str,        # Human-readable note
        "source_url": str,
    }
    """
    # TODO: Implement — Google search for injury updates
    raise NotImplementedError


def assign_playing_xi_tier(player: dict) -> str:
    """
    Determine the player's likely playing XI status.

    Uses: career stats, role, overseas status, team context.

    Returns one of: "GUARANTEED", "LIKELY", "ROTATION", "UNLIKELY"
    """
    # TODO: Implement — use heuristics based on career matches, runs, role
    # Suggested logic:
    #   - If career matches > 100 and runs > 2000 or wickets > 100 → GUARANTEED
    #   - If career matches > 50 → LIKELY
    #   - If career matches > 15 → ROTATION
    #   - Else → UNLIKELY
    # Override for known captains/stars
    raise NotImplementedError


def process_player(player_template: dict) -> dict:
    """
    Full pipeline for one player:
    1. Fetch stats
    2. Fetch injury status
    3. Assign tier
    4. Return filled-in player dict
    """
    player = player_template.copy()

    try:
        stats = fetch_career_stats(player["full_name"])
        player["career_stats"] = {
            "season": 0,
            **stats["career"],
        }
        player["season_2025"] = {
            "season": 2025,
            **stats["season_2025"],
        }
        player["season_2024"] = {
            "season": 2024,
            **stats["season_2024"],
        }
        player["stats_source"] = stats["source_url"]
        player["confidence"] = "High"
    except Exception as e:
        player["confidence"] = "Low"
        player["availability_note"] = f"Stats fetch failed: {e}"

    try:
        injury = fetch_injury_status(player["full_name"])
        player["availability_modifier"] = injury["availability_modifier"]
        player["availability_note"] = injury["availability_note"]
        player["availability_source"] = injury["source_url"]
    except Exception:
        player["availability_modifier"] = 1.0  # Default: assume available

    try:
        player["playing_xi_tier"] = assign_playing_xi_tier(player)
    except Exception:
        player["playing_xi_tier"] = "LIKELY"  # Default

    # Remove search_queries from output (not needed downstream)
    player.pop("search_queries", None)

    return player


def main():
    with open("player_templates.json") as f:
        templates = json.load(f)

    print(f"Processing {len(templates)} players...")

    # TODO: Parallelize this loop
    results = []
    for i, template in enumerate(templates):
        print(f"  [{i+1}/{len(templates)}] {template['full_name']} ({template['ipl_team']})")
        result = process_player(template)
        results.append(result)

    with open("player_data.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone! Saved {len(results)} players to player_data.json")

    # Summary
    tiers = {}
    for r in results:
        tier = r["playing_xi_tier"]
        tiers[tier] = tiers.get(tier, 0) + 1
    print(f"\nTier distribution: {tiers}")

    confidence = {}
    for r in results:
        c = r["confidence"]
        confidence[c] = confidence.get(c, 0) + 1
    print(f"Confidence distribution: {confidence}")


if __name__ == "__main__":
    main()
