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

PHASE2_FIELDS = [
    "playing_xi_tier",
    "availability_modifier",
    "availability_note",
    "overseas_competition_note",
    "availability_source",
    "confidence",
    "research_confidence",
]

PHASE2_AUDIT_FIELDS = [
    "playing_xi_basis",
    "playing_xi_comment",
    "playing_xi_source_urls",
    "playing_xi_checked_at",
    "availability_basis",
    "availability_expected_matches_available",
    "availability_comment",
    "availability_source_urls",
    "availability_checked_at",
    "overseas_competition_basis",
    "overseas_competition_comment",
    "overseas_competition_source_urls",
    "needs_player_followup",
    "followup_reason",
    "followup_checked_at",
    "research_status",
    "research_model",
    "research_run_id",
]

AVAILABILITY_REPAIR_FIELDS = [
    "availability_modifier",
    "availability_note",
    "availability_source",
    "availability_basis",
    "availability_expected_matches_available",
    "availability_comment",
    "availability_source_urls",
    "availability_checked_at",
    "research_model",
    "research_run_id",
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
    + PHASE2_FIELDS
    + PHASE2_AUDIT_FIELDS
    + STATS_FIELDS
    + STATS_METADATA_FIELDS
)


def blank_registry_row() -> dict[str, str]:
    row = {field: "" for field in FIELDNAMES}
    row["is_overseas"] = "False"
    row["playing_xi_tier"] = "LIKELY"
    row["playing_xi_basis"] = "unknown"
    row["availability_modifier"] = "1.0"
    row["confidence"] = "Medium"
    row["availability_basis"] = "unknown"
    row["overseas_competition_basis"] = "unknown"
    row["research_confidence"] = "Medium"
    row["needs_player_followup"] = "False"
    row["research_status"] = "not_started"
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


def official_key(row: dict[str, str]) -> str:
    return row.get("official_player_id", "")


def owned_columns() -> set[str]:
    return set([field for field in PHASE2_FIELDS if field != "confidence"] + PHASE2_AUDIT_FIELDS)


def protected_columns() -> set[str]:
    return set(MANUAL_FIELDS + OFFICIAL_FIELDS + STATS_FIELDS + STATS_METADATA_FIELDS + ["confidence"])


def phase2_owned_columns() -> set[str]:
    return owned_columns()


def phase2_protected_columns() -> set[str]:
    return protected_columns()


def availability_repair_owned_columns() -> set[str]:
    return set(AVAILABILITY_REPAIR_FIELDS)


def build_official_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        player_id = official_key(row).strip()
        if not player_id:
            raise ValueError(f"Missing official_player_id for {registry_key(row)}")
        if player_id in index:
            raise ValueError(f"Duplicate official_player_id {player_id} in player_registry.csv")
        index[player_id] = row
    return index


def apply_owned_update(row: dict[str, str], update: dict[str, str], allowed_columns: set[str] | None = None) -> None:
    allowed = allowed_columns or owned_columns()
    for field, value in update.items():
        if field not in allowed or field not in row:
            continue
        row[field] = "" if value is None else str(value)


def serialize_url_list(urls: list[str]) -> str:
    return "|".join(urls)


def deserialize_url_list(value: str) -> list[str]:
    return [u for u in value.split("|") if u]
