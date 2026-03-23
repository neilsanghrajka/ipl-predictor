"""
CSV adapters for the IPL fantasy predictor.

The canonical input is player_registry.csv. This module translates flattened
CSV rows into the in-memory PlayerData contract used by model.py.
"""

from __future__ import annotations

from pathlib import Path

from model import PlayerData, PlayerRole, PlayingXITier, SeasonStats, predict_all
from registry_csv import parse_bool, parse_float, read_registry_csv, season_payload_from_row


ROLE_MAP = {
    "BAT": PlayerRole.BATTER,
    "BOWL": PlayerRole.BOWLER,
    "AR": PlayerRole.ALL_ROUNDER,
    "WK": PlayerRole.WICKETKEEPER_BATTER,
}

TIER_MAP = {
    "GUARANTEED": PlayingXITier.GUARANTEED,
    "LIKELY": PlayingXITier.LIKELY,
    "ROTATION": PlayingXITier.ROTATION,
    "UNLIKELY": PlayingXITier.UNLIKELY,
}


def _season_from_row(row: dict[str, str], prefix: str) -> SeasonStats:
    return SeasonStats(**season_payload_from_row(row, prefix))


def registry_row_to_dict(row: dict[str, str]) -> dict:
    return {
        "nickname": row["nickname"],
        "full_name": row["full_name"],
        "ipl_team": row["ipl_team"],
        "fantasy_owner": row["fantasy_owner"],
        "role": row["role"],
        "is_overseas": parse_bool(row["is_overseas"]),
        "official_name": row["official_name"],
        "official_player_id": row["official_player_id"],
        "official_player_url": row["official_player_url"],
        "official_stats_feed_url": row["official_stats_feed_url"],
        "mapping_source": row["mapping_source"],
        "mapping_notes": row["mapping_notes"],
        "season_2025": season_payload_from_row(row, "season_2025"),
        "season_2024": season_payload_from_row(row, "season_2024"),
        "career_stats": season_payload_from_row(row, "career"),
        "playing_xi_tier": row["playing_xi_tier"] or "LIKELY",
        "availability_modifier": parse_float(row["availability_modifier"], 1.0),
        "availability_note": row["availability_note"],
        "overseas_competition_note": row["overseas_competition_note"],
        "stats_source": row["stats_source"],
        "availability_source": row["availability_source"],
        "stats_fetched_at": row["stats_fetched_at"],
        "stats_status": row["stats_status"],
        "confidence": row["confidence"] or "Medium",
    }


def dict_to_player_data(data: dict) -> PlayerData:
    def to_season(season: dict) -> SeasonStats:
        return SeasonStats(
            season=season["season"],
            matches=season["matches"],
            innings_batted=season["innings_batted"],
            runs=season["runs"],
            innings_bowled=season["innings_bowled"],
            wickets=season["wickets"],
        )

    if "season_2025" not in data:
        data = registry_row_to_dict(data)

    return PlayerData(
        nickname=data["nickname"],
        full_name=data["full_name"],
        ipl_team=data["ipl_team"],
        fantasy_owner=data["fantasy_owner"],
        role=ROLE_MAP.get(data["role"], PlayerRole.BATTER),
        is_overseas=data["is_overseas"],
        season_2025=to_season(data["season_2025"]),
        season_2024=to_season(data["season_2024"]),
        career_stats=to_season(data["career_stats"]),
        playing_xi_tier=TIER_MAP.get(data["playing_xi_tier"], PlayingXITier.LIKELY),
        availability_modifier=data["availability_modifier"],
        availability_note=data.get("availability_note", ""),
        overseas_competition_note=data.get("overseas_competition_note", ""),
        stats_source=data.get("stats_source", ""),
        availability_source=data.get("availability_source", ""),
        confidence=data.get("confidence", "Medium"),
    )


def load_registry_rows(path: str | Path = "player_registry.csv") -> list[dict[str, str]]:
    return read_registry_csv(path)


def load_player_dicts(path: str | Path = "player_registry.csv") -> list[dict]:
    return [registry_row_to_dict(row) for row in load_registry_rows(path)]


def load_player_objects(path: str | Path = "player_registry.csv") -> list[PlayerData]:
    return [dict_to_player_data(player) for player in load_player_dicts(path)]


def load_players_from_registry_csv(path: str | Path = "player_registry.csv") -> list[PlayerData]:
    return load_player_objects(path)


def run_predictions(player_registry_file: str | Path = "player_registry.csv") -> dict:
    return predict_all(load_player_objects(player_registry_file))
