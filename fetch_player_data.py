"""
Fetch official IPL player stats and write them back into player_registry.csv.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from official_ipl import fetch_player_stats_feed, flatten_stat_row
from registry_csv import STATS_FIELDS, read_registry_csv, registry_key, write_registry_csv


def clear_stats(row: dict[str, str]) -> None:
    for field in STATS_FIELDS:
        row[field] = ""


def process_row(row: dict[str, str], raw_dir: Path) -> tuple[tuple[str, str, str], dict[str, str]]:
    result: dict[str, str] = {}
    timestamp = datetime.now(timezone.utc).isoformat()
    stats_feed_url = row.get("official_stats_feed_url", "")
    player_id = row.get("official_player_id", "")

    result["stats_source"] = stats_feed_url
    result["stats_fetched_at"] = timestamp

    if not player_id or not stats_feed_url:
        result["stats_status"] = "missing_mapping"
        result["confidence"] = "Low"
        return registry_key(row), result

    payload = fetch_player_stats_feed(
        player_id=player_id,
        stats_feed_url=stats_feed_url,
        raw_dir=raw_dir,
    )

    if payload is None:
        result["stats_status"] = "feed_missing"
        result["confidence"] = "Low"
        return registry_key(row), result

    for season_key in ("career", "season_2025", "season_2024"):
        result.update(flatten_stat_row(payload=payload, season_key=season_key))

    result["stats_status"] = "ok"
    result["confidence"] = "High"
    return registry_key(row), result


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch official IPL player stats into player_registry.csv.")
    parser.add_argument("--registry", default="player_registry.csv", help="Path to the canonical registry CSV.")
    parser.add_argument(
        "--raw-dir",
        default="data/raw/player_stats",
        help="Directory where latest raw official stats payloads should be stored.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of concurrent worker threads for official stats fetches.",
    )
    args = parser.parse_args()

    rows = read_registry_csv(args.registry)
    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    updates: dict[tuple[str, str, str], dict[str, str]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(process_row, row, raw_dir): row for row in rows}
        for future in as_completed(future_map):
            row = future_map[future]
            key = registry_key(row)
            try:
                resolved_key, update = future.result()
                updates[resolved_key] = update
            except Exception as exc:
                updates[key] = {
                    "stats_source": row.get("official_stats_feed_url", ""),
                    "stats_fetched_at": datetime.now(timezone.utc).isoformat(),
                    "stats_status": f"error:{type(exc).__name__}",
                    "confidence": "Low",
                }

    for row in rows:
        key = registry_key(row)
        clear_stats(row)
        update = updates[key]
        for field, value in update.items():
            if field in row:
                row[field] = value

    write_registry_csv(args.registry, rows)
    ok_count = sum(1 for row in rows if row["stats_status"] == "ok")
    print(f"Updated stats for {len(rows)} rows in {args.registry} (ok={ok_count})")


if __name__ == "__main__":
    main()
