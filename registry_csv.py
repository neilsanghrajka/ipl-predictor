from __future__ import annotations

import csv
from pathlib import Path


MANUAL_FIELDS = [
    "fantasy_owner",
    "ipl_team",
    "nickname",
    "full_name",
    "role",
    "is_overseas",
]

OFFICIAL_FIELDS = [
    "official_name",
    "official_player_id",
    "official_player_url",
    "official_stats_feed_url",
    "mapping_source",
    "mapping_notes",
]

MODEL_CONTROL_FIELDS = [
    "playing_xi_tier",
    "availability_modifier",
    "availability_note",
    "overseas_competition_note",
    "availability_source",
    "confidence",
]

STATS_METADATA_FIELDS = [
    "stats_source",
    "stats_fetched_at",
    "stats_status",
]

SEASON_COLUMN_MAP = {
    "career": 0,
    "season_2025": 2025,
    "season_2024": 2024,
}

BATTING_FIELDS = [
    "matches",
    "innings",
    "not_outs",
    "runs",
    "high_score",
    "average",
    "balls_faced",
    "strike_rate",
    "hundreds",
    "fifties",
    "fours",
    "sixes",
    "catches",
    "stumpings",
]

BOWLING_FIELDS = [
    "matches",
    "innings",
    "balls",
    "runs_conceded",
    "wickets",
    "best_bowling",
    "average",
    "economy",
    "strike_rate",
    "four_wkts",
    "five_wkts",
]


def build_stats_fields() -> list[str]:
    fields: list[str] = []
    for season_key in SEASON_COLUMN_MAP:
        for metric in BATTING_FIELDS:
            fields.append(f"{season_key}_batting_{metric}")
        for metric in BOWLING_FIELDS:
            fields.append(f"{season_key}_bowling_{metric}")
    return fields


STATS_FIELDS = build_stats_fields()

FIELDNAMES = (
    MANUAL_FIELDS
    + OFFICIAL_FIELDS
    + MODEL_CONTROL_FIELDS
    + STATS_FIELDS
    + STATS_METADATA_FIELDS
)


def blank_registry_row() -> dict[str, str]:
    row = {field: "" for field in FIELDNAMES}
    row["is_overseas"] = "False"
    row["playing_xi_tier"] = "LIKELY"
    row["availability_modifier"] = "1.0"
    row["confidence"] = "Medium"
    return row


def make_registry_row(
    *,
    fantasy_owner: str,
    ipl_team: str,
    nickname: str,
    full_name: str,
    role: str,
    is_overseas: bool,
) -> dict[str, str]:
    row = blank_registry_row()
    row.update(
        {
            "fantasy_owner": fantasy_owner,
            "ipl_team": ipl_team,
            "nickname": nickname,
            "full_name": full_name,
            "role": role,
            "is_overseas": format_bool(is_overseas),
        }
    )
    return row


def format_bool(value: bool) -> str:
    return "True" if value else "False"


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_int(value: str | int | float | None) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def parse_float(value: str | int | float | None, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def read_registry_csv(path: str | Path) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for raw in reader:
            row = blank_registry_row()
            for field in reader.fieldnames or []:
                if field in row:
                    row[field] = raw.get(field, "")
            rows.append(row)
    return rows


def write_registry_csv(path: str | Path, rows: list[dict[str, str]]) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for raw in rows:
            row = blank_registry_row()
            row.update(
                {
                    key: str(value) if value is not None else ""
                    for key, value in raw.items()
                    if key in row
                }
            )
            writer.writerow(row)


def load_registry_rows(path: str | Path) -> list[dict[str, str]]:
    return read_registry_csv(path)


def write_registry_rows(path: str | Path, rows: list[dict[str, str]]) -> None:
    write_registry_csv(path, rows)


def season_matches_from_row(row: dict[str, str], season_key: str) -> int:
    batting_matches = row.get(f"{season_key}_batting_matches", "")
    bowling_matches = row.get(f"{season_key}_bowling_matches", "")
    if batting_matches not in ("", None):
        return parse_int(batting_matches)
    if bowling_matches not in ("", None):
        return parse_int(bowling_matches)
    return 0


def season_payload_from_row(row: dict[str, str], season_key: str) -> dict[str, int]:
    return {
        "season": SEASON_COLUMN_MAP[season_key],
        "matches": season_matches_from_row(row, season_key),
        "innings_batted": parse_int(row.get(f"{season_key}_batting_innings")),
        "runs": parse_int(row.get(f"{season_key}_batting_runs")),
        "innings_bowled": parse_int(row.get(f"{season_key}_bowling_innings")),
        "wickets": parse_int(row.get(f"{season_key}_bowling_wickets")),
    }


def registry_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row["fantasy_owner"], row["ipl_team"], row["nickname"])
