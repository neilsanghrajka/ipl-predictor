from __future__ import annotations

import argparse
import csv
from pathlib import Path

from official_ipl import load_draft_entries
from player_registry import resolve_registry_entry
from registry_csv import make_registry_row, registry_key, write_registry_csv


def load_crosswalk_rows(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    if not path.exists():
        return {}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {
            (row["fantasy_owner"], row["ipl_team"], row["nickname"]): row
            for row in reader
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the canonical player_registry.csv file.")
    parser.add_argument("--draft", default="data/Fantasy Draft.xlsx", help="Path to the fantasy draft workbook.")
    parser.add_argument(
        "--crosswalk",
        default="official_player_crosswalk.csv",
        help="Optional migration input from the older official crosswalk CSV.",
    )
    parser.add_argument(
        "--out",
        default="player_registry.csv",
        help="Path to the canonical output CSV.",
    )
    args = parser.parse_args()

    draft_entries = load_draft_entries(Path(args.draft))
    crosswalk_rows = load_crosswalk_rows(Path(args.crosswalk))

    rows: list[dict[str, str]] = []
    for entry in draft_entries:
        full_name, role, is_overseas = resolve_registry_entry(entry.ipl_team, entry.nickname)
        row = make_registry_row(
            fantasy_owner=entry.fantasy_owner,
            ipl_team=entry.ipl_team,
            nickname=entry.nickname,
            full_name=full_name,
            role=role,
            is_overseas=is_overseas,
        )

        crosswalk = crosswalk_rows.get(registry_key(row))
        if crosswalk:
            row["official_name"] = crosswalk.get("official_name", "")
            row["official_player_id"] = (
                crosswalk.get("official_player_id")
                or crosswalk.get("player_id", "")
            )
            row["official_player_url"] = (
                crosswalk.get("official_player_url")
                or crosswalk.get("player_url", "")
            )
            row["official_stats_feed_url"] = (
                crosswalk.get("official_stats_feed_url")
                or crosswalk.get("stats_feed_url", "")
            )
            row["mapping_source"] = (
                crosswalk.get("mapping_source")
                or crosswalk.get("resolution_method", "")
            )
            row["mapping_notes"] = (
                crosswalk.get("mapping_notes")
                or crosswalk.get("notes", "")
            )

        rows.append(row)

    write_registry_csv(args.out, rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
