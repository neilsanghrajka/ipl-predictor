"""
Phase-2 non-stats enrichment for player_registry.csv.

This script uses GPT-5.4 + web search + structured outputs to populate
playing-XI and availability audit metadata without touching phase-1 official
mapping or batting/bowling stats columns.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from official_ipl import DEFAULT_FIXTURE_SEASON, TEAM_NAMES, fetch_all_team_fixtures
from grounded_research import (
    DEFAULT_MODEL,
    build_player_response_schema,
    build_team_response_schema,
    call_structured_response,
    persist_raw_exchange,
    utc_now_iso,
    validate_player_response,
    validate_team_response,
)
from registry_csv import (
    apply_owned_update,
    build_official_index,
    parse_bool,
    phase2_owned_columns,
    read_registry_csv,
    serialize_url_list,
    write_registry_csv,
)


TEAM_SYSTEM_PROMPT = """You are an IPL 2026 squad availability and lineup analyst.

Your job is only to assess non-stats fields for one IPL squad:
- playing_xi_tier
- availability_modifier
- availability_note
- overseas_competition_note
- research_confidence
- source URLs for each aspect
- whether this player still needs a player-level follow-up

Use web search. Prefer evidence in this order:
1. Official IPL / franchise / BCCI sources
2. Reputable cricket reporting
3. Other high-signal recent coverage only when better sources are unavailable

Rules:
- Do not invent facts.
- Be conservative. If evidence is weak or conflicting, lower research_confidence.
- Do not fetch batting/bowling stats; those are handled elsewhere.
- playing_xi_tier must be one of: GUARANTEED, LIKELY, ROTATION, UNLIKELY
- playing_xi_basis must be one of: confirmed_role, inferred_from_team_context, conflicting_reports, unknown
- availability_basis must be one of: confirmed_available, inferred_no_adverse_news, injury_report, late_joining, tournament_conflict, suspension, conflicting_reports, unknown
- overseas_competition_basis must be one of: overseas_slot_pressure, role_depth_competition, domestic_player, confirmed_role, conflicting_reports, unknown
- research_confidence must be one of: High, Medium, Low
- Use actual published IPL 2026 fixtures in the prompt when estimating availability.
- availability_expected_matches_available must be an integer from 0 to 14.
- availability_modifier must equal availability_expected_matches_available / 14, rounded reasonably.
- If published fixtures are incomplete, say so in availability_comment and lower research_confidence where that materially affects the answer.
- availability_modifier = 1.0 is allowed only with an explicit basis and comment.
- Every player must have at least one URL in each of:
  - playing_xi_source_urls
  - availability_source_urls
  - overseas_competition_source_urls
- For domestic players with no overseas-slot issue, overseas_competition_note should still explain that the overseas cap is not the constraint.
- Keep comments short, factual, and audit-friendly.
- Return JSON only."""


PLAYER_SYSTEM_PROMPT = """You are doing a focused IPL 2026 player availability and lineup audit.

You are refining one player's non-stats fields after an initial team-level pass.
Use web search. Prefer official IPL / franchise / BCCI sources, then reputable cricket reporting.

Rules:
- Return JSON only.
- Keep the same schema as the team-level player object.
- Resolve ambiguity where possible using recent evidence.
- Keep comments short and audit-friendly.
- If evidence remains conflicting, say so explicitly and keep needs_player_followup=true.
- Every source URL array must contain at least one URL."""


def compact_player_context(row: dict[str, str]) -> dict[str, object]:
    return {
        "official_player_id": row["official_player_id"],
        "nickname": row["nickname"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_overseas": parse_bool(row["is_overseas"]),
        "official_player_url": row["official_player_url"],
        "season_2025_matches": row.get("season_2025_batting_matches") or row.get("season_2025_bowling_matches") or "",
        "season_2025_runs": row.get("season_2025_batting_runs", ""),
        "season_2025_wickets": row.get("season_2025_bowling_wickets", ""),
        "season_2024_matches": row.get("season_2024_batting_matches") or row.get("season_2024_bowling_matches") or "",
        "season_2024_runs": row.get("season_2024_batting_runs", ""),
        "season_2024_wickets": row.get("season_2024_bowling_wickets", ""),
    }


def compact_fixture_context(fixtures: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "match_date": fixture["match_date"],
            "match_time_local": fixture["match_time_local"],
            "opponent_code": fixture["opponent_code"],
            "opponent_name": fixture["opponent_name"],
            "venue": fixture["venue"],
            "city": fixture["city"],
            "is_home": fixture["is_home"],
            "match_status": fixture["match_status"],
        }
        for fixture in fixtures
    ]


def build_team_user_prompt(team_code: str, rows: list[dict[str, str]], fixtures: list[dict[str, object]]) -> str:
    payload = {
        "team_code": team_code,
        "team_name": TEAM_NAMES[team_code],
        "published_fixture_count": len(fixtures),
        "league_matches_expected": 14,
        "fixtures": compact_fixture_context(fixtures),
        "players": [compact_player_context(row) for row in rows],
    }
    return (
        "Assess this IPL 2026 squad and return the structured JSON.\n\n"
        f"{json.dumps(payload, indent=2, sort_keys=True)}"
    )


def build_player_user_prompt(
    team_code: str,
    row: dict[str, str],
    fixtures: list[dict[str, object]],
    baseline_player: dict[str, object],
) -> str:
    payload = {
        "team_code": team_code,
        "team_name": TEAM_NAMES[team_code],
        "published_fixture_count": len(fixtures),
        "league_matches_expected": 14,
        "fixtures": compact_fixture_context(fixtures),
        "player": compact_player_context(row),
        "team_level_baseline": baseline_player,
    }
    return (
        "Refine this single-player non-stats assessment and return the structured JSON.\n\n"
        f"{json.dumps(payload, indent=2, sort_keys=True)}"
    )


def baseline_team_complete(rows: list[dict[str, str]], team_raw_path: Path) -> bool:
    if not team_raw_path.exists():
        return False
    return all((row.get("research_status", "").strip().lower() or "not_started") in {"completed", "pending"} for row in rows)


def build_phase2_update(
    record: dict[str, object],
    *,
    checked_at: str,
    model: str,
    run_id: str,
    research_status: str,
    from_followup: bool,
) -> dict[str, str]:
    availability_sources = list(record["availability_source_urls"])
    update = {
        "playing_xi_tier": str(record["playing_xi_tier"]),
        "availability_modifier": f"{float(record['availability_modifier']):.4f}",
        "availability_note": str(record["availability_note"]),
        "overseas_competition_note": str(record["overseas_competition_note"]),
        "availability_source": availability_sources[0] if availability_sources else "",
        "research_confidence": str(record["research_confidence"]),
        "playing_xi_basis": str(record["playing_xi_basis"]),
        "playing_xi_comment": str(record["playing_xi_comment"]),
        "playing_xi_source_urls": serialize_url_list(list(record["playing_xi_source_urls"])),
        "playing_xi_checked_at": checked_at,
        "availability_basis": str(record["availability_basis"]),
        "availability_expected_matches_available": str(int(record["availability_expected_matches_available"])),
        "availability_comment": str(record["availability_comment"]),
        "availability_source_urls": serialize_url_list(availability_sources),
        "availability_checked_at": checked_at,
        "overseas_competition_basis": str(record["overseas_competition_basis"]),
        "overseas_competition_comment": str(record["overseas_competition_comment"]),
        "overseas_competition_source_urls": serialize_url_list(list(record["overseas_competition_source_urls"])),
        "needs_player_followup": "True" if bool(record["needs_player_followup"]) else "False",
        "followup_reason": str(record["followup_reason"]),
        "followup_checked_at": checked_at if from_followup else "",
        "research_status": research_status,
        "research_model": model,
        "research_run_id": run_id,
    }
    return update


def run_team_request(
    *,
    team_code: str,
    rows: list[dict[str, str]],
    fixtures: list[dict[str, object]],
    model: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    parsed, response_payload, request_payload, request_id = call_structured_response(
        system_prompt=TEAM_SYSTEM_PROMPT,
        user_prompt=build_team_user_prompt(team_code, rows, fixtures),
        schema_name=f"{team_code.lower()}_team_enrichment",
        schema=build_team_response_schema(),
        model=model,
        max_output_tokens=9000,
        timeout_seconds=240,
    )
    validated = validate_team_response(parsed)
    expected_ids = {row["official_player_id"] for row in rows}
    actual_ids = {str(item["official_player_id"]) for item in validated["players"]}
    if expected_ids != actual_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise ValueError(f"{team_code} team response player mismatch: missing={missing}, extra={extra}")
    return validated, response_payload, request_payload, request_id


def run_player_followup_request(
    *,
    team_code: str,
    row: dict[str, str],
    fixtures: list[dict[str, object]],
    baseline_player: dict[str, object],
    model: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    parsed, response_payload, request_payload, request_id = call_structured_response(
        system_prompt=PLAYER_SYSTEM_PROMPT,
        user_prompt=build_player_user_prompt(team_code, row, fixtures, baseline_player),
        schema_name=f"{team_code.lower()}_{row['official_player_id']}_followup",
        schema=build_player_response_schema(),
        model=model,
        max_output_tokens=2500,
        timeout_seconds=180,
    )
    validated = validate_player_response(parsed)
    if str(validated["official_player_id"]) != row["official_player_id"]:
        raise ValueError(
            f"Follow-up response returned {validated['official_player_id']} for expected {row['official_player_id']}"
        )
    return validated, response_payload, request_payload, request_id


def selected_team_codes(rows_by_team: dict[str, list[dict[str, str]]], requested: list[str] | None) -> list[str]:
    available = sorted(rows_by_team)
    if not requested:
        return available
    requested_codes = [team.strip().upper() for team in requested if team.strip()]
    invalid = [team for team in requested_codes if team not in rows_by_team]
    if invalid:
        raise ValueError(f"Unknown teams requested: {', '.join(invalid)}")
    return requested_codes


def validate_registry_rows(rows: list[dict[str, str]], teams: list[str]) -> None:
    for row in rows:
        if row["ipl_team"] not in teams:
            continue
        if not row.get("official_player_id", "").strip():
            raise ValueError(f"Missing official_player_id for {row['full_name']} ({row['ipl_team']}/{row['nickname']})")
        if not row.get("official_player_url", "").strip():
            raise ValueError(f"Missing official_player_url for {row['full_name']} ({row['ipl_team']}/{row['nickname']})")


def persist_registry(path: str | Path, rows: list[dict[str, str]]) -> None:
    write_registry_csv(path, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate player_registry.csv with GPT-5.4 non-stats enrichment.")
    parser.add_argument("--registry", default="player_registry.csv", help="Path to the canonical registry CSV.")
    parser.add_argument("--teams", nargs="*", help="Optional list of IPL team codes to enrich.")
    parser.add_argument("--force", action="store_true", help="Re-run team-level enrichment even if a team already has results.")
    parser.add_argument(
        "--force-followups",
        action="store_true",
        help="Re-run player-level follow-ups even if followup_checked_at already exists.",
    )
    parser.add_argument("--workers", type=int, default=1, help="Concurrent team/player requests to run.")
    parser.add_argument("--raw-dir", default="data/raw", help="Root directory for raw fixture/team/player artifacts.")
    parser.add_argument("--season", default=DEFAULT_FIXTURE_SEASON, help="Official IPL season to use for fixtures.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model to use for non-stats enrichment.")
    args = parser.parse_args()

    rows = read_registry_csv(args.registry)
    rows_by_team: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        rows_by_team.setdefault(row["ipl_team"], []).append(row)

    team_codes = selected_team_codes(rows_by_team, args.teams)
    validate_registry_rows(rows, team_codes)
    official_index = build_official_index(rows)
    owned_columns = phase2_owned_columns()

    raw_root = Path(args.raw_dir)
    fixture_dir = raw_root / "fixtures"
    team_raw_dir = raw_root / "team_research"
    player_raw_dir = raw_root / "player_research"

    fixtures_by_team = fetch_all_team_fixtures(season_name=args.season, raw_dir=fixture_dir)
    run_id = utc_now_iso()

    teams_to_run: list[str] = []
    followup_targets: dict[str, list[tuple[dict[str, str], dict[str, object]]]] = {}
    for team_code in team_codes:
        team_rows = rows_by_team[team_code]
        team_raw_path = team_raw_dir / f"{team_code}.json"
        if args.force or not baseline_team_complete(team_rows, team_raw_path):
            teams_to_run.append(team_code)
        elif args.force_followups:
            current_targets: list[tuple[dict[str, str], dict[str, object]]] = []
            for row in team_rows:
                if parse_bool(row.get("needs_player_followup")):
                    current_targets.append(
                        (
                            row,
                            {
                                "official_player_id": row["official_player_id"],
                                "full_name": row["full_name"],
                                "playing_xi_tier": row["playing_xi_tier"],
                                "playing_xi_basis": row["playing_xi_basis"],
                                "playing_xi_comment": row["playing_xi_comment"],
                                "playing_xi_source_urls": row["playing_xi_source_urls"].split("|") if row["playing_xi_source_urls"] else [],
                                "availability_modifier": float(row["availability_modifier"] or 1.0),
                                "availability_basis": row["availability_basis"],
                                "availability_expected_matches_available": int(
                                    row["availability_expected_matches_available"] or 14
                                ),
                                "availability_note": row["availability_note"],
                                "availability_comment": row["availability_comment"],
                                "availability_source_urls": row["availability_source_urls"].split("|")
                                if row["availability_source_urls"]
                                else [],
                                "overseas_competition_note": row["overseas_competition_note"],
                                "overseas_competition_basis": row["overseas_competition_basis"],
                                "overseas_competition_comment": row["overseas_competition_comment"],
                                "overseas_competition_source_urls": row["overseas_competition_source_urls"].split("|")
                                if row["overseas_competition_source_urls"]
                                else [],
                                "research_confidence": row["research_confidence"],
                                "needs_player_followup": True,
                                "followup_reason": row["followup_reason"],
                            },
                        )
                    )
            followup_targets[team_code] = current_targets

    if teams_to_run:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            future_map = {
                executor.submit(
                    run_team_request,
                    team_code=team_code,
                    rows=rows_by_team[team_code],
                    fixtures=fixtures_by_team.get(team_code, []),
                    model=args.model,
                ): team_code
                for team_code in teams_to_run
            }
            for future in as_completed(future_map):
                team_code = future_map[future]
                validated, response_payload, request_payload, request_id = future.result()
                persist_raw_exchange(
                    path=team_raw_dir / f"{team_code}.json",
                    request_payload=request_payload,
                    response_payload=response_payload,
                    parsed_payload=validated,
                    request_id=request_id,
                )
                player_map = {str(item["official_player_id"]): item for item in validated["players"]}
                current_followups: list[tuple[dict[str, str], dict[str, object]]] = []
                for row in rows_by_team[team_code]:
                    record = player_map[row["official_player_id"]]
                    research_status = "pending" if bool(record["needs_player_followup"]) else "completed"
                    update = build_phase2_update(
                        record,
                        checked_at=utc_now_iso(),
                        model=args.model,
                        run_id=run_id,
                        research_status=research_status,
                        from_followup=False,
                    )
                    apply_owned_update(official_index[row["official_player_id"]], update, owned_columns)
                    if bool(record["needs_player_followup"]):
                        current_followups.append((official_index[row["official_player_id"]], record))
                followup_targets[team_code] = current_followups
                persist_registry(args.registry, rows)
                print(f"Saved team-level enrichment for {team_code} ({len(rows_by_team[team_code])} players)")

    followup_jobs: list[tuple[str, dict[str, str], dict[str, object]]] = []
    for team_code in team_codes:
        for row, baseline_record in followup_targets.get(team_code, []):
            if (not args.force_followups) and row.get("followup_checked_at", "").strip() and row.get("research_status") == "completed":
                continue
            followup_jobs.append((team_code, row, baseline_record))

    if followup_jobs:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            future_map = {
                executor.submit(
                    run_player_followup_request,
                    team_code=team_code,
                    row=row,
                    fixtures=fixtures_by_team.get(team_code, []),
                    baseline_player=baseline_record,
                    model=args.model,
                ): (team_code, row)
                for team_code, row, baseline_record in followup_jobs
            }
            for future in as_completed(future_map):
                team_code, row = future_map[future]
                validated, response_payload, request_payload, request_id = future.result()
                persist_raw_exchange(
                    path=player_raw_dir / f"{row['official_player_id']}.json",
                    request_payload=request_payload,
                    response_payload=response_payload,
                    parsed_payload=validated,
                    request_id=request_id,
                )
                update = build_phase2_update(
                    validated,
                    checked_at=utc_now_iso(),
                    model=args.model,
                    run_id=run_id,
                    research_status="completed",
                    from_followup=True,
                )
                apply_owned_update(official_index[row["official_player_id"]], update, owned_columns)
                persist_registry(args.registry, rows)
                print(f"Saved player follow-up for {team_code}/{row['full_name']}")

    if not teams_to_run and not followup_jobs:
        print("Nothing to do. All requested teams already have phase-2 data. Use --force or --force-followups to rerun.")
        return

    completed = sum(1 for row in rows if row.get("research_status") == "completed")
    pending = sum(1 for row in rows if row.get("research_status") == "pending")
    print(f"Phase 2 enrichment updated {args.registry} (completed={completed}, pending={pending})")


if __name__ == "__main__":
    main()
