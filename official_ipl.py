from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path


TEAM_SLUGS = {
    "CSK": "chennai-super-kings",
    "MI": "mumbai-indians",
    "SRH": "sunrisers-hyderabad",
    "RCB": "royal-challengers-bengaluru",
    "PBKS": "punjab-kings",
    "RR": "rajasthan-royals",
    "DC": "delhi-capitals",
    "KKR": "kolkata-knight-riders",
    "LSG": "lucknow-super-giants",
    "GT": "gujarat-titans",
}

STATS_FEED_TEMPLATE = (
    "https://ipl-stats-sports-mechanic.s3.ap-south-1.amazonaws.com/"
    "ipl/feeds/stats/player/{player_id}-playerstats.js"
)

# Accepted final team-scoped mappings for nickname drift and duplicate nicknames.
OFFICIAL_NAME_OVERRIDES: dict[tuple[str, str], str] = {
    ("CSK", "Kartik"): "Kartik Sharma",
    ("CSK", "prashant"): "Prashant Veer",
    ("CSK", "Mhatre"): "Ayush Mhatre",
    ("MI", "Izhar"): "Mohammad Izhar",
    ("MI", "Tilak"): "N Tilak Varma",
    ("MI", "Sky"): "Surya Kumar Yadav",
    ("MI", "Ashwini"): "Ashwani Kumar",
    ("SRH", "Fuletra"): "Krains Fuletra",
    ("SRH", "Shivang"): "Shivang Kumar",
    ("SRH", "Salil"): "Salil Arora",
    ("RCB", "Rasikh"): "Rasikh Dar",
    ("RCB", "Mangesh"): "Mangesh Yadav",
    ("PBKS", "Suyansh"): "Suryansh Shedge",
    ("PBKS", "P Dube"): "Pravin Dubey",
    ("RR", "Burger"): "Nandre Burger",
    ("RR", "Puthur"): "Vignesh Puthur",
    ("RR", "Yudhvir"): "Yudhvir Singh Charak",
    ("DC", "Ngidi"): "Lungisani Ngidi",
    ("DC", "Aquib"): "Auqib Dar",
    ("DC", "Porel"): "Abishek Porel",
    ("DC", "Rizwi"): "Sameer Rizvi",
    ("KKR", "Tejaswi"): "Tejasvi Singh",
    ("KKR", "Vaibhav"): "Vaibhav Arora",
    ("LSG", "Digvesh Rathi"): "Digvesh Singh",
    ("LSG", "Shahbaz"): "Shahbaz Ahamad",
    ("LSG", "Mayank"): "Mayank Yadav",
    ("GT", "Sai Kishore"): "Sai Kishore",
    ("GT", "Arshad Khan"): "Mohd Arshad Khan",
}

DIRECT_PROFILE_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    (
        "RR",
        "Shanaka",
    ): {
        "official_name": "Dasun Shanaka",
        "official_player_id": "1095",
        "official_player_url": "https://www.iplt20.com/players/dasun-shanaka/1095",
        "official_stats_feed_url": STATS_FEED_TEMPLATE.format(player_id="1095"),
        "mapping_source": "direct_player_profile_override",
        "mapping_notes": "Mapped directly to the accepted official IPL player profile.",
    }
}

PLAYER_URL_RE = re.compile(r"https://www\.iplt20\.com/players/([^\"\s]+?)/(\d+)")
HEADING_RE = re.compile(r"<h2>([^<]+)</h2>")
CALLBACK_RE = re.compile(r"^[^(]+\((.*)\);\s*$", re.DOTALL)
XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


@dataclass(frozen=True)
class DraftEntry:
    fantasy_owner: str
    ipl_team: str
    nickname: str


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ipl-predictor/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def fetch_url_or_none(url: str) -> str | None:
    try:
        return fetch_url(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def save_snapshot(path: str | Path, content: str) -> None:
    snapshot_path = Path(path)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(content, encoding="utf-8")


def load_draft_entries(xlsx_path: Path) -> list[DraftEntry]:
    with zipfile.ZipFile(xlsx_path) as workbook:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            sst = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in sst:
                text = "".join(
                    node.text or ""
                    for node in item.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                )
                shared_strings.append(text)

        wb_root = ET.fromstring(workbook.read("xl/workbook.xml"))
        sheets = wb_root.find("main:sheets", XLSX_NS)
        if sheets is None or not list(sheets):
            raise ValueError("Workbook has no sheets")

        rel_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rel_root}
        first_sheet = list(sheets)[0]
        rel_id = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        sheet_xml = ET.fromstring(workbook.read(f"xl/{rel_map[rel_id]}"))
        sheet_data = sheet_xml.find("main:sheetData", XLSX_NS)
        if sheet_data is None:
            raise ValueError("Sheet has no sheetData")

        def cell_value(cell: ET.Element) -> str | None:
            value_node = cell.find("main:v", XLSX_NS)
            if value_node is None:
                return None
            value = value_node.text or ""
            if cell.attrib.get("t") == "s":
                return shared_strings[int(value)]
            return value

        owners: list[str] = []
        current_team: str | None = None
        entries: list[DraftEntry] = []

        for row in sheet_data:
            row_number = int(row.attrib["r"])
            values = {cell.attrib["r"][0]: cell_value(cell) for cell in row}
            if row_number == 1:
                owners = [(values.get(col) or "").strip() for col in "BCDEFGH"]
                continue

            team_value = (values.get("A") or "").strip()
            if team_value:
                current_team = team_value

            if current_team is None:
                continue

            for index, col in enumerate("BCDEFGH"):
                nickname = (values.get(col) or "").strip()
                if not nickname:
                    continue
                entries.append(
                    DraftEntry(
                        fantasy_owner=owners[index],
                        ipl_team=current_team,
                        nickname=nickname,
                    )
                )

    return entries


def fetch_team_roster(team_code: str, raw_dir: str | Path | None = None) -> list[dict[str, str]]:
    slug = TEAM_SLUGS[team_code]
    url = f"https://www.iplt20.com/teams/{slug}/squad"
    html = fetch_url(url)
    if raw_dir is not None:
        save_snapshot(Path(raw_dir) / f"{team_code}.html", html)

    players: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for match in PLAYER_URL_RE.finditer(html):
        player_slug, player_id = match.groups()
        if player_id in seen_ids:
            continue
        seen_ids.add(player_id)
        player_url = f"https://www.iplt20.com/players/{player_slug}/{player_id}"
        official_name = player_slug.replace("-", " ").title()

        segment = html[match.start(): match.start() + 1200]
        heading_match = HEADING_RE.search(segment)
        if heading_match:
            official_name = unescape(heading_match.group(1)).strip()

        players.append(
            {
                "official_name": official_name,
                "official_player_id": player_id,
                "official_player_url": player_url,
                "official_stats_feed_url": STATS_FEED_TEMPLATE.format(player_id=player_id),
            }
        )

    return players


def stats_feed_available(stats_feed_url: str) -> bool:
    request = urllib.request.Request(
        stats_feed_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ipl-predictor/1.0)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read(64)
        return True
    except Exception:
        return False


def resolve_official_player(
    *,
    team: str,
    nickname: str,
    full_name: str,
    roster: list[dict[str, str]],
) -> dict[str, str]:
    override_key = (team, nickname)

    direct_profile = DIRECT_PROFILE_OVERRIDES.get(override_key)
    if direct_profile is not None:
        return dict(direct_profile)

    override_name = OFFICIAL_NAME_OVERRIDES.get(override_key)
    target_name = override_name or full_name
    normalized_target = normalize_name(target_name)

    for player in roster:
        if normalize_name(player["official_name"]) == normalized_target:
            mapping_source = "registry_exact_team_match"
            mapping_notes = ""
            if override_name:
                mapping_source = "team_nickname_override"
                mapping_notes = f"Resolved via accepted team-scoped override to '{player['official_name']}'."
            return {
                **player,
                "mapping_source": mapping_source,
                "mapping_notes": mapping_notes,
            }

    raise ValueError(f"Could not resolve {team}/{nickname} against the official squad page")


def parse_stats_feed(raw_payload: str) -> dict[str, list[dict[str, object]]]:
    match = CALLBACK_RE.match(raw_payload.strip())
    if not match:
        raise ValueError("Unexpected player stats feed format")
    return json.loads(match.group(1))


def fetch_player_stats_feed(
    *,
    player_id: str,
    stats_feed_url: str | None = None,
    raw_dir: str | Path | None = None,
) -> dict[str, list[dict[str, object]]] | None:
    url = stats_feed_url or STATS_FEED_TEMPLATE.format(player_id=player_id)
    raw_payload = fetch_url_or_none(url)
    if raw_payload is None:
        return None
    if raw_dir is not None:
        save_snapshot(Path(raw_dir) / f"{player_id}-playerstats.js", raw_payload)
    return parse_stats_feed(raw_payload)


def find_stat_row(rows: list[dict[str, object]] | None, year_label: str) -> dict[str, object] | None:
    if not rows:
        return None
    for row in rows:
        if str(row.get("Year")) == year_label:
            return row
    return None


def string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def flatten_stat_row(
    *,
    payload: dict[str, list[dict[str, object]]],
    season_key: str,
) -> dict[str, str]:
    year_label = "AllTime" if season_key == "career" else season_key.split("_", 1)[1]
    batting_row = find_stat_row(payload.get("Batting") or [], year_label)
    bowling_row = find_stat_row(payload.get("Bowling") or [], year_label)

    return {
        f"{season_key}_batting_matches": string_value(batting_row.get("Matches") if batting_row else ""),
        f"{season_key}_batting_innings": string_value(batting_row.get("Innings") if batting_row else ""),
        f"{season_key}_batting_not_outs": string_value(batting_row.get("NotOuts") if batting_row else ""),
        f"{season_key}_batting_runs": string_value(batting_row.get("Runs") if batting_row else ""),
        f"{season_key}_batting_high_score": string_value(batting_row.get("HighestScore") if batting_row else ""),
        f"{season_key}_batting_average": string_value(batting_row.get("BattingAvg") if batting_row else ""),
        f"{season_key}_batting_balls_faced": string_value(batting_row.get("Balls") if batting_row else ""),
        f"{season_key}_batting_strike_rate": string_value(batting_row.get("StrikeRate") if batting_row else ""),
        f"{season_key}_batting_hundreds": string_value(batting_row.get("Hundreds") if batting_row else ""),
        f"{season_key}_batting_fifties": string_value(batting_row.get("Fifties") if batting_row else ""),
        f"{season_key}_batting_fours": string_value(batting_row.get("Fours") if batting_row else ""),
        f"{season_key}_batting_sixes": string_value(batting_row.get("Sixes") if batting_row else ""),
        f"{season_key}_batting_catches": string_value(batting_row.get("Catches") if batting_row else ""),
        f"{season_key}_batting_stumpings": string_value(batting_row.get("Stumpings") if batting_row else ""),
        f"{season_key}_bowling_matches": string_value(bowling_row.get("Matches") if bowling_row else ""),
        f"{season_key}_bowling_innings": string_value(bowling_row.get("Innings") if bowling_row else ""),
        f"{season_key}_bowling_balls": string_value(bowling_row.get("Balls") if bowling_row else ""),
        f"{season_key}_bowling_runs_conceded": string_value(bowling_row.get("Runs") if bowling_row else ""),
        f"{season_key}_bowling_wickets": string_value(bowling_row.get("Wickets") if bowling_row else ""),
        f"{season_key}_bowling_best_bowling": string_value(bowling_row.get("BBM") if bowling_row else ""),
        f"{season_key}_bowling_average": string_value(bowling_row.get("Average") if bowling_row else ""),
        f"{season_key}_bowling_economy": string_value(bowling_row.get("Econ") if bowling_row else ""),
        f"{season_key}_bowling_strike_rate": string_value(bowling_row.get("StrikeRate") if bowling_row else ""),
        f"{season_key}_bowling_four_wkts": string_value(bowling_row.get("FourWkts") if bowling_row else ""),
        f"{season_key}_bowling_five_wkts": string_value(bowling_row.get("FiveWkts") if bowling_row else ""),
    }
