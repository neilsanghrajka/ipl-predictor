from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4"
VALID_TIERS = {"GUARANTEED", "LIKELY", "ROTATION", "UNLIKELY"}
VALID_RESEARCH_CONFIDENCE = {"High", "Medium", "Low"}
VALID_PLAYING_XI_BASIS = {
    "confirmed_role",
    "inferred_from_team_context",
    "conflicting_reports",
    "unknown",
}
VALID_AVAILABILITY_BASIS = {
    "confirmed_available",
    "inferred_no_adverse_news",
    "injury_report",
    "late_joining",
    "tournament_conflict",
    "suspension",
    "conflicting_reports",
    "unknown",
}
VALID_OVERSEAS_BASIS = {
    "overseas_slot_pressure",
    "role_depth_competition",
    "domestic_player",
    "confirmed_role",
    "conflicting_reports",
    "unknown",
}
VALID_AVAILABILITY_REPAIR_BASIS = VALID_AVAILABILITY_BASIS
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
TEAM_PLAYER_FIELDS = [
    "official_player_id",
    "full_name",
    "playing_xi_tier",
    "playing_xi_basis",
    "playing_xi_comment",
    "playing_xi_source_urls",
    "availability_modifier",
    "availability_basis",
    "availability_expected_matches_available",
    "availability_note",
    "availability_comment",
    "availability_source_urls",
    "overseas_competition_note",
    "overseas_competition_basis",
    "overseas_competition_comment",
    "overseas_competition_source_urls",
    "research_confidence",
    "needs_player_followup",
    "followup_reason",
]
AVAILABILITY_REPAIR_FIELDS = [
    "official_player_id",
    "availability_modifier",
    "expected_matches_available",
    "availability_basis",
    "availability_note",
    "reasoning",
    "has_real_concern",
    "source_urls",
]
AVAILABILITY_REPAIR_FIELDS = [
    "official_player_id",
    "availability_modifier",
    "expected_matches_available",
    "availability_note",
    "reasoning",
    "has_real_concern",
    "availability_basis",
    "source_urls",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_team_response_schema() -> dict[str, object]:
    player_schema = build_player_response_schema()
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "team": {"type": "string"},
            "players": {
                "type": "array",
                "items": player_schema,
            },
        },
        "required": ["team", "players"],
    }


def build_player_response_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "official_player_id": {"type": "string"},
            "full_name": {"type": "string"},
            "playing_xi_tier": {"type": "string", "enum": sorted(VALID_TIERS)},
            "playing_xi_basis": {"type": "string", "enum": sorted(VALID_PLAYING_XI_BASIS)},
            "playing_xi_comment": {"type": "string"},
            "playing_xi_source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "availability_modifier": {"type": "number"},
            "availability_basis": {"type": "string", "enum": sorted(VALID_AVAILABILITY_BASIS)},
            "availability_expected_matches_available": {"type": "integer"},
            "availability_note": {"type": "string"},
            "availability_comment": {"type": "string"},
            "availability_source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "overseas_competition_note": {"type": "string"},
            "overseas_competition_basis": {"type": "string", "enum": sorted(VALID_OVERSEAS_BASIS)},
            "overseas_competition_comment": {"type": "string"},
            "overseas_competition_source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "research_confidence": {"type": "string", "enum": sorted(VALID_RESEARCH_CONFIDENCE)},
            "needs_player_followup": {"type": "boolean"},
            "followup_reason": {"type": "string"},
        },
        "required": TEAM_PLAYER_FIELDS,
    }


def build_availability_repair_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "official_player_id": {"type": "string"},
            "availability_modifier": {"type": "number"},
            "expected_matches_available": {"type": "integer"},
            "availability_note": {"type": "string"},
            "reasoning": {"type": "string"},
            "has_real_concern": {"type": "boolean"},
            "availability_basis": {"type": "string", "enum": sorted(VALID_AVAILABILITY_REPAIR_BASIS)},
            "source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "required": [
            "official_player_id",
            "availability_modifier",
            "expected_matches_available",
            "availability_note",
            "reasoning",
            "has_real_concern",
            "availability_basis",
            "source_urls",
        ],
    }


def build_availability_repair_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "official_player_id": {"type": "string"},
            "availability_modifier": {"type": "number"},
            "expected_matches_available": {"type": "integer"},
            "availability_basis": {"type": "string", "enum": sorted(VALID_AVAILABILITY_BASIS)},
            "availability_note": {"type": "string"},
            "reasoning": {"type": "string"},
            "has_real_concern": {"type": "boolean"},
            "source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "required": AVAILABILITY_REPAIR_FIELDS,
    }


def build_availability_repair_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "official_player_id": {"type": "string"},
            "availability_modifier": {"type": "number"},
            "expected_matches_available": {"type": "integer"},
            "availability_note": {"type": "string"},
            "reasoning": {"type": "string"},
            "has_real_concern": {"type": "boolean"},
            "availability_basis": {"type": "string", "enum": sorted(VALID_AVAILABILITY_BASIS)},
            "source_urls": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "required": AVAILABILITY_REPAIR_FIELDS,
    }


def _extract_output_text(response_payload: dict[str, object]) -> str:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in response_payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]

    raise ValueError("Responses API payload did not include output text")


def _request_json(
    *,
    api_key: str,
    payload: dict[str, object],
    request_id: str,
    timeout_seconds: int,
) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": request_id,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def call_structured_response(
    *,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: dict[str, object],
    model: str = DEFAULT_MODEL,
    max_output_tokens: int = 5000,
    timeout_seconds: int = 180,
    retries: int = 4,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    request_id = str(uuid.uuid4())
    payload = {
        "model": model,
        "tools": [{"type": "web_search"}],
        "max_output_tokens": max_output_tokens,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
    }

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response_payload = _request_json(
                api_key=api_key,
                payload=payload,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
            )
            text = _extract_output_text(response_payload)
            parsed = json.loads(text)
            return parsed, response_payload, payload, request_id
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "ignore")
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == retries:
                raise RuntimeError(f"OpenAI Responses API failed with {exc.code}: {body}") from exc
            last_error = exc
            time.sleep(2 ** attempt)
        except urllib.error.URLError as exc:
            if attempt == retries:
                raise RuntimeError(f"OpenAI Responses API network failure: {exc}") from exc
            last_error = exc
            time.sleep(2 ** attempt)
        except (ConnectionResetError, TimeoutError, OSError) as exc:
            if attempt == retries:
                raise RuntimeError(f"OpenAI Responses API connection failure: {exc}") from exc
            last_error = exc
            time.sleep(2 ** attempt)
        except json.JSONDecodeError as exc:
            if attempt == retries:
                raise RuntimeError("OpenAI Responses API returned invalid JSON text") from exc
            last_error = exc
            time.sleep(2 ** attempt)

    raise RuntimeError(f"OpenAI Responses API failed after retries: {last_error}")


def _normalize_url_list(values: object, *, field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _normalize_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise ValueError(f"{field_name} must be a boolean")


def _normalize_player_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in TEAM_PLAYER_FIELDS if field not in record]
    if missing:
        raise ValueError(f"Structured response missing fields: {missing}")

    availability_modifier = float(record["availability_modifier"])
    if not (0.0 <= availability_modifier <= 1.0):
        raise ValueError("availability_modifier must be between 0 and 1")

    expected_matches = int(record["availability_expected_matches_available"])
    if not (0 <= expected_matches <= 14):
        raise ValueError("availability_expected_matches_available must be between 0 and 14")

    playing_xi_tier = str(record["playing_xi_tier"]).strip()
    if playing_xi_tier not in VALID_TIERS:
        raise ValueError(f"Invalid playing_xi_tier {playing_xi_tier}")

    playing_xi_basis = str(record["playing_xi_basis"]).strip()
    if playing_xi_basis not in VALID_PLAYING_XI_BASIS:
        raise ValueError(f"Invalid playing_xi_basis {playing_xi_basis}")

    availability_basis = str(record["availability_basis"]).strip()
    if availability_basis not in VALID_AVAILABILITY_BASIS:
        raise ValueError(f"Invalid availability_basis {availability_basis}")

    overseas_basis = str(record["overseas_competition_basis"]).strip()
    if overseas_basis not in VALID_OVERSEAS_BASIS:
        raise ValueError(f"Invalid overseas_competition_basis {overseas_basis}")

    research_confidence = str(record["research_confidence"]).strip()
    if research_confidence not in VALID_RESEARCH_CONFIDENCE:
        raise ValueError(f"Invalid research_confidence {research_confidence}")

    official_player_id = str(record["official_player_id"]).strip()
    if not official_player_id:
        raise ValueError("official_player_id is required")

    playing_xi_sources = _normalize_url_list(record["playing_xi_source_urls"], field_name="playing_xi_source_urls")
    if not playing_xi_sources:
        raise ValueError("playing_xi_source_urls must contain at least one URL")

    availability_sources = _normalize_url_list(
        record["availability_source_urls"],
        field_name="availability_source_urls",
    )
    if not availability_sources:
        raise ValueError("availability_source_urls must contain at least one URL")

    overseas_sources = _normalize_url_list(
        record["overseas_competition_source_urls"],
        field_name="overseas_competition_source_urls",
    )
    if not overseas_sources:
        raise ValueError("overseas_competition_source_urls must contain at least one URL")

    needs_followup = _normalize_bool(record["needs_player_followup"], field_name="needs_player_followup")
    followup_reason = str(record["followup_reason"]).strip()
    if needs_followup and not followup_reason:
        raise ValueError("followup_reason is required when needs_player_followup is true")

    return {
        "official_player_id": official_player_id,
        "full_name": str(record["full_name"]).strip(),
        "playing_xi_tier": playing_xi_tier,
        "playing_xi_basis": playing_xi_basis,
        "playing_xi_comment": str(record["playing_xi_comment"]).strip(),
        "playing_xi_source_urls": playing_xi_sources,
        "availability_modifier": availability_modifier,
        "availability_basis": availability_basis,
        "availability_expected_matches_available": expected_matches,
        "availability_note": str(record["availability_note"]).strip(),
        "availability_comment": str(record["availability_comment"]).strip(),
        "availability_source_urls": availability_sources,
        "overseas_competition_note": str(record["overseas_competition_note"]).strip(),
        "overseas_competition_basis": overseas_basis,
        "overseas_competition_comment": str(record["overseas_competition_comment"]).strip(),
        "overseas_competition_source_urls": overseas_sources,
        "research_confidence": research_confidence,
        "needs_player_followup": needs_followup,
        "followup_reason": followup_reason,
    }


def validate_team_response(payload: dict[str, object]) -> dict[str, object]:
    team = str(payload.get("team") or "").strip()
    players = payload.get("players")
    if not team:
        raise ValueError("Team response missing team name")
    if not isinstance(players, list) or not players:
        raise ValueError("Team response must include players")

    normalized_players: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for raw_player in players:
        if not isinstance(raw_player, dict):
            raise ValueError("Team response player entries must be objects")
        player = _normalize_player_record(raw_player)
        player_id = str(player["official_player_id"])
        if not player_id:
            raise ValueError("Team response player missing official_player_id")
        if player_id in seen_ids:
            raise ValueError(f"Duplicate official_player_id {player_id} in team response")
        seen_ids.add(player_id)
        normalized_players.append(player)

    return {"team": team, "players": normalized_players}


def validate_player_response(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("Player response must be an object")
    return _normalize_player_record(payload)


def validate_availability_repair_response(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("Availability repair response must be an object")

    official_player_id = str(payload.get("official_player_id", "")).strip()
    if not official_player_id:
        raise ValueError("Availability repair response missing official_player_id")

    availability_modifier = float(payload.get("availability_modifier", 1.0))
    if not (0.0 <= availability_modifier <= 1.0):
        raise ValueError("availability_modifier must be between 0 and 1")

    expected_matches = int(payload.get("expected_matches_available", 14))
    if not (0 <= expected_matches <= 14):
        raise ValueError("expected_matches_available must be between 0 and 14")

    if abs(availability_modifier - (expected_matches / 14 if 14 else 0.0)) > 0.03:
        raise ValueError("availability_modifier must align with expected_matches_available / 14")

    availability_basis = str(payload.get("availability_basis", "")).strip()
    if availability_basis not in VALID_AVAILABILITY_REPAIR_BASIS:
        raise ValueError(f"Invalid availability_basis {availability_basis}")

    has_real_concern = _normalize_bool(payload.get("has_real_concern"), field_name="has_real_concern")
    if (not has_real_concern) and (expected_matches != 14 or availability_modifier < 0.999):
        raise ValueError("Rows without a real concern must return full availability")
    if availability_basis in {"confirmed_available", "inferred_no_adverse_news", "unknown"} and (
        expected_matches != 14 or availability_modifier < 0.999
    ):
        raise ValueError("Healthy/unknown availability_basis values must return full availability")

    availability_note = str(payload.get("availability_note", "")).strip()
    if not availability_note:
        raise ValueError("availability_note is required")

    reasoning = str(payload.get("reasoning", "")).strip()
    if not reasoning:
        raise ValueError("reasoning is required")

    source_urls = _normalize_url_list(payload.get("source_urls"), field_name="source_urls")
    if not source_urls:
        raise ValueError("source_urls must contain at least one URL")

    return {
        "official_player_id": official_player_id,
        "availability_modifier": availability_modifier,
        "expected_matches_available": expected_matches,
        "availability_note": availability_note,
        "reasoning": reasoning,
        "has_real_concern": has_real_concern,
        "availability_basis": availability_basis,
        "source_urls": source_urls,
    }


def validate_availability_repair_response(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("Availability repair response must be an object")

    missing = [field for field in AVAILABILITY_REPAIR_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Availability repair response missing fields: {missing}")

    availability_modifier = float(payload["availability_modifier"])
    if not (0.0 <= availability_modifier <= 1.0):
        raise ValueError("availability_modifier must be between 0 and 1")

    expected_matches = int(payload["expected_matches_available"])
    if not (0 <= expected_matches <= 14):
        raise ValueError("expected_matches_available must be between 0 and 14")
    if abs(availability_modifier - (expected_matches / 14.0)) > 0.03:
        raise ValueError("availability_modifier must align with expected_matches_available / 14")

    availability_basis = str(payload["availability_basis"]).strip()
    if availability_basis not in VALID_AVAILABILITY_BASIS:
        raise ValueError(f"Invalid availability_basis {availability_basis}")

    official_player_id = str(payload["official_player_id"]).strip()
    if not official_player_id:
        raise ValueError("official_player_id is required")

    source_urls = _normalize_url_list(payload["source_urls"], field_name="source_urls")
    if not source_urls:
        raise ValueError("source_urls must contain at least one URL")

    has_real_concern = _normalize_bool(payload["has_real_concern"], field_name="has_real_concern")
    if not has_real_concern and (availability_modifier < 1.0 or expected_matches < 14):
        raise ValueError("has_real_concern=false requires full availability")

    return {
        "official_player_id": official_player_id,
        "availability_modifier": availability_modifier,
        "expected_matches_available": expected_matches,
        "availability_basis": availability_basis,
        "availability_note": str(payload["availability_note"]).strip(),
        "reasoning": str(payload["reasoning"]).strip(),
        "has_real_concern": has_real_concern,
        "source_urls": source_urls,
    }


def validate_availability_repair_response(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("Availability repair response must be an object")

    missing = [field for field in AVAILABILITY_REPAIR_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Availability repair response missing fields: {missing}")

    official_player_id = str(payload["official_player_id"]).strip()
    if not official_player_id:
        raise ValueError("Availability repair response missing official_player_id")

    availability_modifier = float(payload["availability_modifier"])
    if not (0.0 <= availability_modifier <= 1.0):
        raise ValueError("availability_modifier must be between 0 and 1")

    expected_matches = int(payload["expected_matches_available"])
    if not (0 <= expected_matches <= 14):
        raise ValueError("expected_matches_available must be between 0 and 14")

    availability_basis = str(payload["availability_basis"]).strip()
    if availability_basis not in VALID_AVAILABILITY_BASIS:
        raise ValueError(f"Invalid availability_basis {availability_basis}")

    source_urls = _normalize_url_list(payload["source_urls"], field_name="source_urls")
    if not source_urls:
        raise ValueError("source_urls must contain at least one URL")

    has_real_concern = _normalize_bool(payload["has_real_concern"], field_name="has_real_concern")
    reasoning = str(payload["reasoning"]).strip()
    if not reasoning:
        raise ValueError("reasoning is required")

    return {
        "official_player_id": official_player_id,
        "availability_modifier": availability_modifier,
        "expected_matches_available": expected_matches,
        "availability_note": str(payload["availability_note"]).strip(),
        "reasoning": reasoning,
        "has_real_concern": has_real_concern,
        "availability_basis": availability_basis,
        "source_urls": source_urls,
    }


def persist_raw_exchange(
    *,
    path: str | Path,
    request_payload: dict[str, object],
    response_payload: dict[str, object],
    parsed_payload: dict[str, object] | None,
    request_id: str,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "saved_at": utc_now_iso(),
        "request_id": request_id,
        "request": request_payload,
        "response": response_payload,
        "parsed": parsed_payload,
    }
    target.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
