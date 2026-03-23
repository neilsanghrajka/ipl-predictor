"""
Data Collection Script for IPL Fantasy Predictor
=================================================

This script defines the search strategy for each player.
It will be executed by calling web search APIs for each player
to populate the model with real data.

The output is a JSON file: player_data.json
Each player entry contains all the fields needed by model.py
"""

import json
from player_registry import PLAYER_REGISTRY
from model import (
    PlayerData, PlayerRole, PlayingXITier, SeasonStats,
    load_draft_from_excel, predict_all
)

ROLE_MAP = {
    "BAT": PlayerRole.BATTER,
    "BOWL": PlayerRole.BOWLER,
    "AR": PlayerRole.ALL_ROUNDER,
    "WK": PlayerRole.WICKETKEEPER_BATTER,
}


def create_blank_player_data(nickname: str, ipl_team: str, fantasy_owner: str) -> dict:
    """
    Creates a blank player data template that needs to be filled by web search.
    This defines exactly what data we need for each player.
    """
    if nickname in PLAYER_REGISTRY:
        full_name, role_str, is_overseas = PLAYER_REGISTRY[nickname]
    else:
        full_name = nickname
        role_str = "BAT"
        is_overseas = False

    return {
        "nickname": nickname,
        "full_name": full_name,
        "ipl_team": ipl_team,
        "fantasy_owner": fantasy_owner,
        "role": role_str,
        "is_overseas": is_overseas,

        # To be filled by web search
        "season_2025": {
            "season": 2025,
            "matches": 0,
            "innings_batted": 0,
            "runs": 0,
            "innings_bowled": 0,
            "wickets": 0,
        },
        "season_2024": {
            "season": 2024,
            "matches": 0,
            "innings_batted": 0,
            "runs": 0,
            "innings_bowled": 0,
            "wickets": 0,
        },
        "career_stats": {
            "season": 0,
            "matches": 0,
            "innings_batted": 0,
            "runs": 0,
            "innings_bowled": 0,
            "wickets": 0,
        },

        # To be assessed from web search
        "playing_xi_tier": "LIKELY",  # Default, to be overridden
        "availability_modifier": 1.0,
        "availability_note": "",
        "overseas_competition_note": "",
        "stats_source": "",
        "availability_source": "",
        "confidence": "Medium",

        # Web search queries to run
        "search_queries": {
            "stats": f"{full_name} IPL career statistics runs wickets matches espncricinfo",
            "form_2025": f"{full_name} IPL 2025 stats runs wickets",
            "injury": f"{full_name} injury fitness update IPL 2026",
        }
    }


def generate_all_player_templates(draft_file: str) -> list[dict]:
    """Parse the draft and generate blank templates for every player."""
    draft = load_draft_from_excel(draft_file)
    all_players = []

    for owner, players in draft.items():
        for p in players:
            template = create_blank_player_data(
                nickname=p["nickname"],
                ipl_team=p["ipl_team"],
                fantasy_owner=owner,
            )
            all_players.append(template)

    return all_players


def dict_to_player_data(d: dict) -> PlayerData:
    """Convert a filled-in dict back to a PlayerData for the model."""
    role = ROLE_MAP.get(d["role"], PlayerRole.BATTER)

    tier_map = {
        "GUARANTEED": PlayingXITier.GUARANTEED,
        "LIKELY": PlayingXITier.LIKELY,
        "ROTATION": PlayingXITier.ROTATION,
        "UNLIKELY": PlayingXITier.UNLIKELY,
    }

    def to_season(s: dict) -> SeasonStats:
        return SeasonStats(
            season=s["season"],
            matches=s["matches"],
            innings_batted=s["innings_batted"],
            runs=s["runs"],
            innings_bowled=s["innings_bowled"],
            wickets=s["wickets"],
        )

    return PlayerData(
        nickname=d["nickname"],
        full_name=d["full_name"],
        ipl_team=d["ipl_team"],
        fantasy_owner=d["fantasy_owner"],
        role=role,
        is_overseas=d["is_overseas"],
        season_2025=to_season(d["season_2025"]),
        season_2024=to_season(d["season_2024"]),
        career_stats=to_season(d["career_stats"]),
        playing_xi_tier=tier_map.get(d["playing_xi_tier"], PlayingXITier.LIKELY),
        availability_modifier=d["availability_modifier"],
        availability_note=d.get("availability_note", ""),
        overseas_competition_note=d.get("overseas_competition_note", ""),
        stats_source=d.get("stats_source", ""),
        availability_source=d.get("availability_source", ""),
        confidence=d.get("confidence", "Medium"),
    )


def run_predictions(player_data_file: str) -> dict:
    """Load filled player data and run the full prediction model."""
    with open(player_data_file) as f:
        players_raw = json.load(f)

    players = [dict_to_player_data(d) for d in players_raw]
    return predict_all(players)


if __name__ == "__main__":
    # Step 1: Generate blank templates
    draft_file = '/sessions/adoring-intelligent-galileo/mnt/uploads/Teamwise Players-2 (1).xlsx'
    templates = generate_all_player_templates(draft_file)

    print(f"Generated {len(templates)} player templates")
    print(f"\nFantasy owners: {set(t['fantasy_owner'] for t in templates)}")
    print(f"IPL teams: {set(t['ipl_team'] for t in templates)}")

    # Save blank templates
    with open('/sessions/adoring-intelligent-galileo/ipl-predictor/player_templates.json', 'w') as f:
        json.dump(templates, f, indent=2)

    print(f"\nSaved to player_templates.json")
    print(f"\nSample player template:")
    print(json.dumps(templates[0], indent=2))

    # Show all search queries that need to be run
    print(f"\n\n=== TOTAL SEARCH QUERIES NEEDED ===")
    total_queries = sum(len(t["search_queries"]) for t in templates)
    print(f"Players: {len(templates)}")
    print(f"Queries per player: 3 (stats, recent form, injury)")
    print(f"Total queries: {total_queries}")
