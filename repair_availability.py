"""
Targeted repair pass for contaminated availability fields in player_registry.csv.

This script does not rerun lineup or overseas research. It only reassesses
availability for suspicious rows using the current availability-repair policy:
partial fixture publication is a schedule artifact, not player unavailability.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from grounded_research import (
    DEFAULT_MODEL,
    build_availability_repair_schema,
    call_structured_response,
    persist_raw_exchange,
    utc_now_iso,
    validate_availability_repair_response,
)
from registry_csv import (
    apply_owned_update,
    build_official_index,
    deserialize_url_list,
    parse_bool,
    read_registry_csv,
    serialize_url_list,
    write_registry_csv,
)


RAW_TEAM_DIRNAME = "team_research"
RAW_PLAYER_DIRNAME = "player_research"
RAW_FIXTURE_DIRNAME = "fixtures"
RAW_REPAIR_DIRNAME = "availability_repair"
SCHEDULE_PUBLICATION_MARKERS = (
    "published fixture",
    "published fixtures",
    "first-phase",
    "first phase",
    "part-1",
    "part 1",
    "only four fixtures",
    "only 4 fixtures",
    "fixtures are officially published so far",
)
PLAYER_SPECIFIC_BASES = {
    "injury_report",
    "late_joining",
    "tournament_conflict",
    "suspension",
    "conflicting_reports",
}

REPAIR_OWNED_COLUMNS = {
    "availability_modifier",
    "availability_expected_matches_available",
    "availability_note",
    "availability_comment",
    "availability_basis",
    "availability_source_urls",
    "availability_source",
    "availability_checked_at",
    "research_model",
    "research_run_id",
}

SYSTEM_PROMPT = """You are an IPL 2026 availability auditor fixing contaminated fantasy input data.

Your only job is to decide whether a player should have reduced availability for the 14-match league stage.

Core rule:
- Every IPL team plays 14 league matches.
- Partial fixture publication is not a player availability issue.
- Only reduce availability for player-specific reasons such as injury, delayed joining, tournament conflict, suspension, or credible workload management.

Use web search to verify evidence when needed, but keep the decision anchored to the provided raw audit context.
Return JSON only."""

AVAILABILITY_REPAIR_PROMPT = """You are assessing the availability of an IPL 2026 cricket player for a fantasy prediction model.

## Player Context
- Official Player ID: {official_player_id}
- Name: {full_name}
- IPL Team: {ipl_team}
- Role: {role}
- Overseas: {is_overseas}

## Raw Data Collected
Here is everything we found about this player's availability, injury status, and fitness:

<raw_availability_data>
{raw_availability_text}
</raw_availability_data>

## Your Task

Determine what fraction of the 14-match IPL 2026 league season this player will be AVAILABLE to be selected for.

**CRITICAL RULES:**
1. Every IPL team plays exactly 14 league stage matches.
2. Do not reduce availability just because only some fixtures have been published or announced. Partial schedule publication is NOT a player availability issue.
3. Only reduce availability for player-specific reasons:
   - confirmed injury with recovery timeline
   - international duty or tournament conflict that overlaps IPL dates
   - suspension or ban
   - withdrawal or late joining
   - credible workload management / conflicting reports
4. If there is NO evidence of player-specific absence, availability_modifier MUST be 1.0 and expected_matches_available MUST be 14.
5. "No news" means healthy.

Return the final answer as JSON only using this exact shape:
{{
  "official_player_id": "{official_player_id}",
  "availability_modifier": <float 0.0 to 1.0>,
  "expected_matches_available": <int 0 to 14>,
  "availability_note": "<one sentence>",
  "reasoning": "<2-3 audit-friendly sentences>",
  "has_real_concern": <true or false>,
  "availability_basis": "<one of confirmed_available, inferred_no_adverse_news, injury_report, late_joining, tournament_conflict, suspension, conflicting_reports, unknown>",
  "source_urls": ["<url1>", "<url2>"]
}}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair contaminated availability fields in player_registry.csv.")
    parser.add_argument("--registry", default="player_registry.csv", help="Path to the canonical registry CSV.")
    parser.add_argument("--teams", nargs="*", help="Optional IPL team codes to restrict the repair pass.")
    parser.add_argument("--player-ids", nargs="*", help="Optional official_player_id values to repair explicitly.")
    parser.add_argument("--force", action="store_true", help="Re-run even if a repair artifact already exists.")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent repair requests to run.")
    parser.add_argument("--raw-dir", default="data/raw", help="Root directory for raw input and repair artifacts.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model to use.")
    return parser.parse_args()


def selected_team_codes(rows: list[dict[str, str]], requested: list[str] | None) -> set[str]:
    available = {row["ipl_team"] for row in rows}
    if not requested:
        return available
    requested_codes = {team.strip().upper() for team in requested if team.strip()}
    invalid = sorted(requested_codes - available)
    if invalid:
        raise ValueError(f"Unknown teams requested: {', '.join(invalid)}")
    return requested_codes


def contains_schedule_publication_artifact(*texts: str) -> bool:
    combined = " ".join(text for text in texts if text).lower()
    return any(marker in combined for marker in SCHEDULE_PUBLICATION_MARKERS)


def build_repair_availability_prompt(
    *,
    official_player_id: str,
    full_name: str,
    ipl_team: str,
    role: str,
    is_overseas: bool,
    raw_availability_text: str,
) -> str:
    return AVAILABILITY_REPAIR_PROMPT.format(
        official_player_id=official_player_id,
        full_name=full_name,
        ipl_team=ipl_team,
        role=role,
        is_overseas=is_overseas,
        raw_availability_text=raw_availability_text or "No availability or injury information found for this player.",
    )


def is_suspicious_row(row: dict[str, str]) -> bool:
    if float(row.get("availability_modifier") or 1.0) < 1.0:
        return True
    if parse_bool(row.get("needs_player_followup")):
        return True
    return contains_schedule_publication_artifact(row.get("availability_comment", ""), row.get("availability_note", ""))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_team_player_map(team_bundle: dict[str, object], team_code: str) -> dict[str, dict[str, object]]:
    parsed = team_bundle.get("parsed")
    if not isinstance(parsed, dict):
        raise ValueError(f"{team_code} team bundle missing parsed object")
    players = parsed.get("players")
    if not isinstance(players, list):
        raise ValueError(f"{team_code} team bundle parsed.players must be a list")
    mapping: dict[str, dict[str, object]] = {}
    for item in players:
        if not isinstance(item, dict):
            continue
        player_id = str(item.get("official_player_id", "")).strip()
        if player_id:
            mapping[player_id] = item
    return mapping


def summarize_fixture_bundle(bundle: dict[str, object]) -> dict[str, object]:
    fixtures = bundle.get("fixtures", [])
    compact_fixtures = []
    if isinstance(fixtures, list):
        compact_fixtures = [
            {
                "match_date": fixture.get("match_date"),
                "opponent_code": fixture.get("opponent_code"),
                "venue": fixture.get("venue"),
                "match_status": fixture.get("match_status"),
            }
            for fixture in fixtures[:8]
            if isinstance(fixture, dict)
        ]
    return {
        "team": bundle.get("team"),
        "team_name": bundle.get("team_name"),
        "season": bundle.get("season"),
        "published_fixture_count": bundle.get("published_fixture_count"),
        "league_matches_expected": 14,
        "fixtures_preview": compact_fixtures,
    }


def build_raw_availability_text(
    row: dict[str, str],
    team_player_record: dict[str, object],
    followup_record: dict[str, object] | None,
    fixture_bundle: dict[str, object],
) -> str:
    current_csv_context = {
        "official_player_id": row["official_player_id"],
        "availability_modifier": row.get("availability_modifier"),
        "availability_expected_matches_available": row.get("availability_expected_matches_available"),
        "availability_basis": row.get("availability_basis"),
        "availability_note": row.get("availability_note"),
        "availability_comment": row.get("availability_comment"),
        "availability_source_urls": deserialize_url_list(row.get("availability_source_urls", "")),
    }
    sections = [
        "Current CSV availability fields:\n" + json.dumps(current_csv_context, indent=2, sort_keys=True),
        "Fixture publication context:\n" + json.dumps(summarize_fixture_bundle(fixture_bundle), indent=2, sort_keys=True),
        "Team-level research record:\n" + json.dumps(team_player_record, indent=2, sort_keys=True),
    ]
    if followup_record is not None:
        sections.append("Player follow-up research record:\n" + json.dumps(followup_record, indent=2, sort_keys=True))
    else:
        sections.append("Player follow-up research record:\nnull")
    sections.append(
        "Important interpretation rule:\n"
        "- Every team still plays 14 league matches.\n"
        "- Published fixture count is schedule completeness only.\n"
        "- Reduce availability only when there is player-specific absence evidence."
    )
    return "\n\n".join(sections)


def run_repair_request(
    *,
    row: dict[str, str],
    team_player_record: dict[str, object],
    followup_record: dict[str, object] | None,
    fixture_bundle: dict[str, object],
    model: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    user_prompt = build_repair_availability_prompt(
        official_player_id=row["official_player_id"],
        full_name=row["full_name"],
        ipl_team=row["ipl_team"],
        role=row["role"],
        is_overseas=parse_bool(row["is_overseas"]),
        raw_availability_text=build_raw_availability_text(row, team_player_record, followup_record, fixture_bundle),
    )
    parsed, response_payload, request_payload, request_id = call_structured_response(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema_name=f"availability_repair_{row['official_player_id']}",
        schema=build_availability_repair_schema(),
        model=model,
        max_output_tokens=2200,
        timeout_seconds=180,
    )
    validated = validate_availability_repair_response(parsed)
    if validated["official_player_id"] != row["official_player_id"]:
        raise ValueError(
            f"Availability repair returned {validated['official_player_id']} for expected {row['official_player_id']}"
        )
    if validated["availability_modifier"] < 1.0 and validated["availability_basis"] not in PLAYER_SPECIFIC_BASES:
        raise ValueError(
            f"Availability repair reduced {row['full_name']} without player-specific basis: "
            f"{validated['availability_basis']}"
        )
    return validated, response_payload, request_payload, request_id


def build_update(record: dict[str, object], *, checked_at: str, model: str, run_id: str) -> dict[str, str]:
    source_urls = list(record["source_urls"])
    return {
        "availability_modifier": f"{float(record['availability_modifier']):.4f}",
        "availability_expected_matches_available": str(int(record["expected_matches_available"])),
        "availability_note": str(record["availability_note"]),
        "availability_comment": str(record["reasoning"]),
        "availability_basis": str(record["availability_basis"]),
        "availability_source_urls": serialize_url_list(source_urls),
        "availability_source": source_urls[0] if source_urls else "",
        "availability_checked_at": checked_at,
        "research_model": model,
        "research_run_id": run_id,
    }


def persist_registry(path: str | Path, rows: list[dict[str, str]]) -> None:
    write_registry_csv(path, rows)


def main() -> None:
    args = parse_args()
    rows = read_registry_csv(args.registry)
    if not rows:
        raise ValueError(f"{args.registry} is missing or empty")

    team_codes = selected_team_codes(rows, args.teams)
    explicit_player_ids = {player_id.strip() for player_id in (args.player_ids or []) if player_id.strip()}
    official_index = build_official_index(rows)

    raw_root = Path(args.raw_dir)
    team_raw_dir = raw_root / RAW_TEAM_DIRNAME
    player_raw_dir = raw_root / RAW_PLAYER_DIRNAME
    fixture_dir = raw_root / RAW_FIXTURE_DIRNAME
    repair_dir = raw_root / RAW_REPAIR_DIRNAME

    team_player_cache: dict[str, dict[str, dict[str, object]]] = {}
    fixture_cache: dict[str, dict[str, object]] = {}

    def get_team_player_record(team_code: str, player_id: str) -> dict[str, object]:
        if team_code not in team_player_cache:
            bundle = load_json(team_raw_dir / f"{team_code}.json")
            team_player_cache[team_code] = build_team_player_map(bundle, team_code)
        try:
            return team_player_cache[team_code][player_id]
        except KeyError as exc:
            raise ValueError(f"team_research/{team_code}.json missing player {player_id}") from exc

    def get_fixture_bundle(team_code: str) -> dict[str, object]:
        if team_code not in fixture_cache:
            fixture_cache[team_code] = load_json(fixture_dir / f"{team_code}.json")
        return fixture_cache[team_code]

    targets: list[dict[str, str]] = []
    skipped_existing = 0
    for row in rows:
        player_id = row.get("official_player_id", "").strip()
        if not player_id:
            raise ValueError(f"Missing official_player_id for {row['full_name']} ({row['ipl_team']}/{row['nickname']})")
        if row["ipl_team"] not in team_codes:
            continue
        explicitly_selected = bool(explicit_player_ids) and player_id in explicit_player_ids
        if explicit_player_ids and not explicitly_selected:
            continue
        if not explicitly_selected and not is_suspicious_row(row):
            continue
        repair_path = repair_dir / f"{player_id}.json"
        if repair_path.exists() and not args.force:
            skipped_existing += 1
            continue
        targets.append(row)

    if not targets:
        print("Nothing to do. No matching availability repairs are needed. Use --force to rerun.")
        return

    run_id = utc_now_iso()
    futures = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        for row in targets:
            player_id = row["official_player_id"]
            team_code = row["ipl_team"]
            followup_path = player_raw_dir / f"{player_id}.json"
            followup_record = None
            if followup_path.exists():
                followup_bundle = load_json(followup_path)
                parsed_followup = followup_bundle.get("parsed")
                if isinstance(parsed_followup, dict):
                    followup_record = parsed_followup
            futures[
                executor.submit(
                    run_repair_request,
                    row=row,
                    team_player_record=get_team_player_record(team_code, player_id),
                    followup_record=followup_record,
                    fixture_bundle=get_fixture_bundle(team_code),
                    model=args.model,
                )
            ] = row

        repaired = 0
        for future in as_completed(futures):
            row = futures[future]
            validated, response_payload, request_payload, request_id = future.result()
            player_id = row["official_player_id"]
            persist_raw_exchange(
                path=repair_dir / f"{player_id}.json",
                request_payload=request_payload,
                response_payload=response_payload,
                parsed_payload=validated,
                request_id=request_id,
            )
            update = build_update(
                validated,
                checked_at=utc_now_iso(),
                model=args.model,
                run_id=run_id,
            )
            apply_owned_update(official_index[player_id], update, REPAIR_OWNED_COLUMNS)
            persist_registry(args.registry, rows)
            repaired += 1
            print(f"Repaired availability for {row['ipl_team']}/{row['full_name']}")

    print(
        f"Availability repair updated {args.registry} "
        f"(repaired={repaired}, skipped_existing={skipped_existing})"
    )


if __name__ == "__main__":
    main()
