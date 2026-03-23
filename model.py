"""
IPL 2026 Fantasy Draft Prediction Model
========================================
Methodology:
- Scoring: 1 run = 1 point, 1 wicket = 25 points
- Expected Points = Expected_Matches × (Avg_Runs_Per_Match + Avg_Wickets_Per_Match × 25)
- Expected_Matches = 14 × Playing_XI_Probability × Availability_Modifier
- Stats weighted: 50% last season, 30% season before, 20% career average
"""

import json
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class PlayerRole(Enum):
    BATTER = "Batter"
    BOWLER = "Bowler"
    ALL_ROUNDER = "All-Rounder"
    WICKETKEEPER_BATTER = "Wicketkeeper-Batter"


class PlayingXITier(Enum):
    GUARANTEED = "Guaranteed Starter"    # 90-95%
    LIKELY = "Likely Starter"            # 70-80%
    ROTATION = "Rotation/Fringe"         # 30-50%
    UNLIKELY = "Unlikely to Play"        # 5-15%


# Playing XI probability by tier
TIER_PROBABILITIES = {
    PlayingXITier.GUARANTEED: 0.92,
    PlayingXITier.LIKELY: 0.75,
    PlayingXITier.ROTATION: 0.40,
    PlayingXITier.UNLIKELY: 0.10,
}

LEAGUE_MATCHES = 14
WICKET_POINTS = 25


@dataclass
class SeasonStats:
    """Stats for a single IPL season."""
    season: int
    matches: int = 0
    innings_batted: int = 0
    runs: int = 0
    innings_bowled: int = 0
    wickets: int = 0

    @property
    def runs_per_match(self) -> float:
        if self.matches == 0:
            return 0.0
        return self.runs / self.matches

    @property
    def wickets_per_match(self) -> float:
        if self.matches == 0:
            return 0.0
        return self.wickets / self.matches


@dataclass
class PlayerData:
    """All data needed to predict a player's fantasy points."""
    # Identity
    nickname: str                          # As shown in the draft sheet
    full_name: str = ""
    ipl_team: str = ""                     # CSK, MI, SRH, etc.
    fantasy_owner: str = ""                # Manan, Akshit, etc.
    role: PlayerRole = PlayerRole.BATTER
    is_overseas: bool = False

    # Historical stats (per season)
    season_2025: Optional[SeasonStats] = None   # Most recent
    season_2024: Optional[SeasonStats] = None   # Previous
    career_stats: Optional[SeasonStats] = None  # Career aggregate

    # Availability & selection
    playing_xi_tier: PlayingXITier = PlayingXITier.LIKELY
    availability_modifier: float = 1.0     # 0.0 (ruled out) to 1.0 (fully available)
    availability_note: str = ""            # e.g. "Recovering from knee injury, expected back by match 5"

    # Overseas slot pressure (only for overseas players)
    overseas_competition_note: str = ""    # e.g. "Team has 6 strong overseas options, will rotate"

    # Data source tracking
    stats_source: str = ""                 # URL or description of where stats came from
    availability_source: str = ""          # URL or description of injury/availability info
    confidence: str = "Medium"             # High / Medium / Low — how confident are we in the data


def compute_weighted_runs_per_match(player: PlayerData) -> float:
    """
    Weighted average runs per match: 50% last season, 30% previous, 20% career.
    Falls back gracefully if seasons are missing.
    """
    values = []
    weights = []

    if player.season_2025 and player.season_2025.matches > 0:
        values.append(player.season_2025.runs_per_match)
        weights.append(0.50)

    if player.season_2024 and player.season_2024.matches > 0:
        values.append(player.season_2024.runs_per_match)
        weights.append(0.30)

    if player.career_stats and player.career_stats.matches > 0:
        values.append(player.career_stats.runs_per_match)
        weights.append(0.20)

    if not values:
        return 0.0

    # Normalize weights to sum to 1
    total_weight = sum(weights)
    return sum(v * (w / total_weight) for v, w in zip(values, weights))


def compute_weighted_wickets_per_match(player: PlayerData) -> float:
    """
    Weighted average wickets per match: 50% last season, 30% previous, 20% career.
    """
    values = []
    weights = []

    if player.season_2025 and player.season_2025.matches > 0:
        values.append(player.season_2025.wickets_per_match)
        weights.append(0.50)

    if player.season_2024 and player.season_2024.matches > 0:
        values.append(player.season_2024.wickets_per_match)
        weights.append(0.30)

    if player.career_stats and player.career_stats.matches > 0:
        values.append(player.career_stats.wickets_per_match)
        weights.append(0.20)

    if not values:
        return 0.0

    total_weight = sum(weights)
    return sum(v * (w / total_weight) for v, w in zip(values, weights))


def compute_expected_matches(player: PlayerData) -> float:
    """Expected matches = 14 × Playing XI % × Availability Modifier"""
    xi_prob = TIER_PROBABILITIES[player.playing_xi_tier]
    return LEAGUE_MATCHES * xi_prob * player.availability_modifier


def predict_player_points(player: PlayerData) -> dict:
    """
    Full prediction for a single player.
    Returns a dict with all intermediate calculations for auditability.
    """
    weighted_runs = compute_weighted_runs_per_match(player)
    weighted_wickets = compute_weighted_wickets_per_match(player)
    expected_matches = compute_expected_matches(player)

    batting_points = weighted_runs * expected_matches
    bowling_points = weighted_wickets * WICKET_POINTS * expected_matches
    total_points = batting_points + bowling_points

    return {
        # Player identity
        "nickname": player.nickname,
        "full_name": player.full_name,
        "ipl_team": player.ipl_team,
        "fantasy_owner": player.fantasy_owner,
        "role": player.role.value,
        "is_overseas": player.is_overseas,

        # Intermediate calculations (for audit trail)
        "weighted_runs_per_match": round(weighted_runs, 2),
        "weighted_wickets_per_match": round(weighted_wickets, 3),
        "playing_xi_probability": TIER_PROBABILITIES[player.playing_xi_tier],
        "playing_xi_tier": player.playing_xi_tier.value,
        "availability_modifier": player.availability_modifier,
        "availability_note": player.availability_note,
        "expected_matches": round(expected_matches, 2),

        # Points breakdown
        "expected_batting_points": round(batting_points, 1),
        "expected_bowling_points": round(bowling_points, 1),
        "expected_total_points": round(total_points, 1),

        # Raw stats for reference
        "season_2025": asdict(player.season_2025) if player.season_2025 else None,
        "season_2024": asdict(player.season_2024) if player.season_2024 else None,
        "career_stats": asdict(player.career_stats) if player.career_stats else None,

        # Confidence & sources
        "confidence": player.confidence,
        "stats_source": player.stats_source,
        "availability_source": player.availability_source,
        "overseas_competition_note": player.overseas_competition_note,
    }


def predict_all(players: list[PlayerData]) -> dict:
    """
    Run predictions for all players, aggregate by fantasy owner.
    Returns full results with per-player breakdowns and owner totals.
    """
    predictions = [predict_player_points(p) for p in players]

    # Aggregate by fantasy owner
    owner_totals = {}
    for pred in predictions:
        owner = pred["fantasy_owner"]
        if owner not in owner_totals:
            owner_totals[owner] = {
                "owner": owner,
                "total_points": 0,
                "total_batting_points": 0,
                "total_bowling_points": 0,
                "player_count": 0,
                "players": [],
            }
        owner_totals[owner]["total_points"] += pred["expected_total_points"]
        owner_totals[owner]["total_batting_points"] += pred["expected_batting_points"]
        owner_totals[owner]["total_bowling_points"] += pred["expected_bowling_points"]
        owner_totals[owner]["player_count"] += 1
        owner_totals[owner]["players"].append(pred)

    # Round totals
    for owner in owner_totals.values():
        owner["total_points"] = round(owner["total_points"], 1)
        owner["total_batting_points"] = round(owner["total_batting_points"], 1)
        owner["total_bowling_points"] = round(owner["total_bowling_points"], 1)

    # Sort by total points descending
    rankings = sorted(owner_totals.values(), key=lambda x: x["total_points"], reverse=True)

    return {
        "methodology": {
            "scoring": "1 run = 1 point, 1 wicket = 25 points",
            "formula": "Expected Points = Expected_Matches × (Weighted_Runs/Match + Weighted_Wickets/Match × 25)",
            "expected_matches": "14 × Playing_XI_Probability × Availability_Modifier",
            "stat_weighting": "50% IPL 2025, 30% IPL 2024, 20% Career Average",
            "tiers": {tier.value: prob for tier, prob in TIER_PROBABILITIES.items()},
        },
        "rankings": rankings,
        "all_predictions": predictions,
    }


# --- Data Loading ---

def load_draft_from_excel(filepath: str) -> dict[str, list[str]]:
    """
    Parse the fantasy draft Excel file.
    Returns: {fantasy_owner: [list of player nicknames]}
    """
    df = pd.read_excel(filepath)

    # Map IPL team to row ranges
    ipl_teams = ['CSK', 'MI', 'SRH', 'RCB', 'PBKS', 'RR', 'DC', 'KKR', 'LSG', 'GT']
    owners = df.columns[1:].tolist()

    # Build owner -> [(nickname, ipl_team)] mapping
    result = {owner: [] for owner in owners}
    current_team = None

    for idx, row in df.iterrows():
        team_cell = row.iloc[0]
        if pd.notna(team_cell) and str(team_cell).strip() in ipl_teams:
            current_team = str(team_cell).strip()

        for owner in owners:
            player = row[owner]
            if pd.notna(player) and str(player).strip():
                result[owner].append({
                    "nickname": str(player).strip(),
                    "ipl_team": current_team,
                })

    return result


if __name__ == "__main__":
    # Quick test: parse the draft file
    draft = load_draft_from_excel('/sessions/adoring-intelligent-galileo/mnt/uploads/Teamwise Players-2 (1).xlsx')
    for owner, players in draft.items():
        print(f"\n{owner} ({len(players)} players):")
        for p in players:
            print(f"  {p['nickname']:20s} [{p['ipl_team']}]")
