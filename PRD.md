# IPL 2026 Fantasy Draft Predictor — Data Collection PRD

## Overview

We have a fantasy IPL draft with 7 owners and 186 players across 10 IPL teams. We need to predict which fantasy owner will win based on: **1 run = 1 point, 1 wicket = 25 points**.

The prediction model (`model.py`) is already built. What's missing is **real player data**. This PRD specifies the data collection script that fetches stats for every player and outputs a single JSON file that the model consumes.

---

## Goal

Build a script (`fetch_player_data.py`) that:
1. Reads `player_templates.json` (186 players with search queries pre-built)
2. For each player, fetches IPL career stats, recent season stats, and injury/availability info
3. Outputs `player_data.json` — the same schema as templates but with stats filled in
4. Also assigns each player a `playing_xi_tier` and `availability_modifier`

---

## Data Source Strategy

**Primary source:** https://www.iplt20.com/players/{slug}/{id}

URL pattern: `https://www.iplt20.com/players/{firstname-lastname}/{player_id}`

Examples:
- https://www.iplt20.com/players/virat-kohli/164
- https://www.iplt20.com/players/mayank-markande/4951
- https://www.iplt20.com/players/jasprit-bumrah/2972

**Fallback sources:**
- ESPNcricinfo: `https://www.espncricinfo.com/cricketers/{name}-{id}`
- Google search: `"{full_name}" IPL career stats runs wickets matches`

**For injury/availability:**
- Google search: `"{full_name}" IPL 2026 injury update availability`

---

## Input File: `player_templates.json`

Already generated. Array of 186 objects, each with this shape:

```json
{
  "nickname": "Samson",
  "full_name": "Sanju Samson",
  "ipl_team": "CSK",
  "fantasy_owner": "Manan",
  "role": "WK",
  "is_overseas": false,
  "season_2025": { "season": 2025, "matches": 0, "innings_batted": 0, "runs": 0, "innings_bowled": 0, "wickets": 0 },
  "season_2024": { "season": 2024, "matches": 0, "innings_batted": 0, "runs": 0, "innings_bowled": 0, "wickets": 0 },
  "career_stats": { "season": 0, "matches": 0, "innings_batted": 0, "runs": 0, "innings_bowled": 0, "wickets": 0 },
  "playing_xi_tier": "LIKELY",
  "availability_modifier": 1.0,
  "availability_note": "",
  "overseas_competition_note": "",
  "stats_source": "",
  "availability_source": "",
  "confidence": "Medium",
  "search_queries": {
    "stats": "Sanju Samson IPL career statistics runs wickets matches espncricinfo",
    "form_2025": "Sanju Samson IPL 2025 stats runs wickets",
    "injury": "Sanju Samson injury fitness update IPL 2026"
  }
}
```

---

## Output File: `player_data.json`

**Same schema as input**, but with these fields populated:

### Required Fields (must be filled for every player)

| Field | Type | Description |
|-------|------|-------------|
| `career_stats.matches` | int | Total IPL career matches |
| `career_stats.innings_batted` | int | Total IPL innings batted |
| `career_stats.runs` | int | Total IPL career runs |
| `career_stats.innings_bowled` | int | Total IPL innings bowled (0 for pure batters) |
| `career_stats.wickets` | int | Total IPL career wickets (0 for pure batters) |
| `season_2025.matches` | int | Matches played in IPL 2025 (0 if didn't play) |
| `season_2025.runs` | int | Runs in IPL 2025 |
| `season_2025.wickets` | int | Wickets in IPL 2025 |
| `season_2024.matches` | int | Matches played in IPL 2024 (0 if didn't play) |
| `season_2024.runs` | int | Runs in IPL 2024 |
| `season_2024.wickets` | int | Wickets in IPL 2024 |
| `playing_xi_tier` | string | One of: `GUARANTEED`, `LIKELY`, `ROTATION`, `UNLIKELY` |
| `availability_modifier` | float | 0.0 to 1.0 (1.0 = fully available all season) |
| `stats_source` | string | URL where stats were sourced from |
| `confidence` | string | `High`, `Medium`, or `Low` |

### Playing XI Tier Assignment Rules

| Tier | Criteria | Examples |
|------|----------|---------|
| `GUARANTEED` | Captain, star player, undisputed starter | Kohli, Bumrah, Pant, Gill, Jaiswal |
| `LIKELY` | Strong squad member, first-choice in role | Harshal, Axar, Arshdeep, Klaasen |
| `ROTATION` | Competes for spot, overseas player in crowded team, utility | Shanaka, Seifert, Anukul Roy |
| `UNLIKELY` | Uncapped, net bowler, deep bench, unlikely to get games | Fuletra, Shivang, Aniket Verma |

### Availability Modifier Rules

| Value | Meaning |
|-------|---------|
| 1.0 | Fully fit, available for entire season |
| 0.8-0.9 | Minor concern — may miss 1-2 matches |
| 0.5-0.7 | Significant — known injury, expected to miss 4-7 matches |
| 0.2-0.4 | Major — serious injury, may only play last few matches |
| 0.0 | Ruled out for the season / retired (e.g., MSD if he retires) |

---

## Script Architecture

```
fetch_player_data.py
├── load player_templates.json
├── For each player (parallelizable):
│   ├── fetch_career_stats(full_name) → career totals + 2024 + 2025 season
│   ├── fetch_injury_status(full_name) → availability info
│   ├── assign_playing_xi_tier(player) → tier classification
│   └── merge into player dict
├── Save player_data.json
└── Print summary report
```

### Parallelization

Players are independent — fetch all 186 in parallel (with rate limiting). Suggested: 10-20 concurrent requests.

### Error Handling

If a player's stats can't be found:
- Set `confidence: "Low"`
- Set stats to 0
- Set `availability_note: "Stats not found — using zero baseline"`
- **Do not skip the player** — they must appear in the output

---

## Stub Files

The repo contains these files:

| File | Status | Description |
|------|--------|-------------|
| `model.py` | ✅ Complete | Prediction engine |
| `player_registry.py` | ✅ Complete | Nickname → full name mapping |
| `collect_data.py` | ✅ Complete | Template generator + model runner |
| `player_templates.json` | ✅ Complete | 186 blank player templates |
| `fetch_player_data.py` | 🔲 STUB | **You implement this** — fetches real data |
| `player_data.json` | 🔲 OUTPUT | Generated by fetch_player_data.py |
| `run_predictions.py` | ✅ Complete | Takes player_data.json → predictions.json |
| `verification/verify.py` | ✅ Complete | Verification script (see below) |
| `verification/expected_samples.json` | ✅ Complete | Known-good data for 5 test players |

---

## Verification Plan

### Test 1: Schema Validation
Run `verify.py` which checks that `player_data.json`:
- Has exactly 186 entries
- Every entry has all required fields
- All `playing_xi_tier` values are valid enum values
- All `availability_modifier` values are between 0.0 and 1.0
- All stat values are non-negative integers
- Every `stats_source` is non-empty

### Test 2: Spot-Check 5 Known Players
We hardcode expected stats for 5 well-known players. The verification script checks that your fetched data is within ±10% of these values (to allow for minor discrepancies across sources):

| Player | Career Matches | Career Runs | Career Wickets | Source |
|--------|---------------|-------------|----------------|--------|
| Virat Kohli | ~267 | ~8661 | 0 | WebSearch confirmed |
| Jasprit Bumrah | ~133 | ~56 | ~165 | Well-known |
| Ravindra Jadeja | ~232 | ~2500 | ~155 | Well-known |
| Sunil Narine | ~177 | ~1500 | ~180 | Well-known |
| Rishabh Pant | ~115 | ~3300 | 0 | Well-known |

### Test 3: Sanity Checks
- No batter should have >1000 runs per season (max ever is ~973 by Kohli)
- No bowler should have >35 wickets per season (max ever is ~32)
- Every IPL team should have at least 15 players in the dataset
- Total player count per fantasy owner should match the draft sheet

### Test 4: Run Model End-to-End
After `player_data.json` is created, run:
```bash
python run_predictions.py
```
This should produce `predictions.json` with rankings for all 7 owners. Verify:
- All 7 owners appear
- Total points are in a reasonable range (2000-8000 per owner)
- The predicted winner has a plausible margin

---

## How to Run

```bash
# Step 1: You implement and run this
python fetch_player_data.py

# Step 2: Verify the data
python verification/verify.py

# Step 3: Run predictions
python run_predictions.py
```
