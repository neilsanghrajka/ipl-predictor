from __future__ import annotations

import argparse
from pathlib import Path

from official_ipl import TEAM_SLUGS, fetch_team_roster, resolve_official_player, stats_feed_available
from registry_csv import load_registry_rows, write_registry_rows


def populate_rows(csv_path: Path, raw_dir: Path) -> list[dict[str, str]]:
    rows = load_registry_rows(csv_path)
    roster_dir = raw_dir / "team_rosters"
    rosters = {team: fetch_team_roster(team, roster_dir) for team in TEAM_SLUGS}

    for row in rows:
        mapping = resolve_official_player(
            team=row["ipl_team"],
            nickname=row["nickname"],
            full_name=row["full_name"],
            roster=rosters[row["ipl_team"]],
        )
        row["official_name"] = mapping["official_name"]
        row["official_player_id"] = mapping["official_player_id"]
        row["official_player_url"] = mapping["official_player_url"]
        row["official_stats_feed_url"] = mapping["official_stats_feed_url"]
        row["mapping_source"] = mapping["mapping_source"]
        row["mapping_notes"] = mapping["mapping_notes"]

        if row["official_name"]:
            row["full_name"] = row["official_name"]

        if row["official_stats_feed_url"] and not stats_feed_available(row["official_stats_feed_url"]):
            note = "Official stats feed not available for this player ID."
            if note not in row["mapping_notes"]:
                row["mapping_notes"] = f"{row['mapping_notes']} {note}".strip()

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate official IPL player IDs and URLs into player_registry.csv.")
    parser.add_argument("--csv", default="player_registry.csv", help="Path to the canonical registry CSV.")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory for latest raw official squad snapshots.")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    rows = populate_rows(csv_path, Path(args.raw_dir))
    write_registry_rows(csv_path, rows)
    resolved = sum(1 for row in rows if row["official_player_id"])
    print(f"Updated {csv_path} with official mappings for {resolved}/{len(rows)} rows")


if __name__ == "__main__":
    main()
