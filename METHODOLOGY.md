# IPL 2026 Fantasy Draft — Prediction Methodology

## Scoring System

- 1 run scored = 1 point
- 1 wicket taken = 25 points
- No other scoring (no catches, stumpings, strike rate bonuses, etc.)

## The Core Formula

For each player:

```
Expected Points = Expected Matches × (Weighted Runs Per Match + Weighted Wickets Per Match × 25)
```

Where:

```
Expected Matches = 14 × Playing XI Probability × Availability Modifier
```

That's the entire model. The complexity lives in how we estimate each input.

---

## Input 1: Weighted Runs Per Match

We calculate runs per match (total runs ÷ total matches played) for three time windows, then blend them:

| Window | Weight | What it captures |
|--------|--------|-----------------|
| IPL 2025 season | 50% | Most recent form |
| IPL 2024 season | 30% | Previous year trend |
| Career average | 20% | Long-term baseline |

**Why this weighting:** T20 form is volatile. A player who scored 500 runs last season is more likely to repeat that than a player whose career average is high but recent form is poor. The 50/30/20 split favors recency while still anchoring to career performance.

**Fallback logic:** If a player didn't play in a particular season, that season's weight is redistributed proportionally across available seasons. For example, if a player only has career stats (no 2024 or 2025 data), 100% of the weight goes to career average.

**Calculation:**
```
Runs Per Match = Total Runs in Period ÷ Total Matches in Period
```

Note: We use matches (not innings) as the denominator. This naturally penalizes players who bat lower in the order and sometimes don't get to bat — which is correct for fantasy scoring since they contribute fewer runs on average per game.

---

## Input 2: Weighted Wickets Per Match

Same approach as runs:

| Window | Weight |
|--------|--------|
| IPL 2025 season | 50% |
| IPL 2024 season | 30% |
| Career average | 20% |

**Calculation:**
```
Wickets Per Match = Total Wickets in Period ÷ Total Matches in Period
```

For pure batters this is 0. For part-time bowlers it will be a small positive number. For frontline bowlers it's typically 1.0–1.5 wickets per match.

---

## Input 3: Expected Matches

This is the most impactful factor in the model. A guaranteed starter on a full-season campaign accumulates far more points than a bench player.

```
Expected Matches = 14 × Playing XI Probability × Availability Modifier
```

### 14 League Matches

Every IPL team plays exactly 14 league stage matches. We do NOT model playoffs (per the agreed methodology).

### Playing XI Probability

Each player is classified into one of four tiers:

| Tier | Probability | Who belongs here |
|------|------------|-----------------|
| Guaranteed Starter | 92% | Captains, franchise players, undisputed first-choice players. Examples: Virat Kohli, Jasprit Bumrah, Rishabh Pant, Yashasvi Jaiswal, Shubman Gill |
| Likely Starter | 75% | Strong squad members, first-choice in their role but could be rested/rotated occasionally. Examples: Harshal Patel, Axar Patel, Arshdeep Singh, Heinrich Klaasen |
| Rotation / Fringe | 40% | Players competing for a spot, overseas players in teams with too many overseas options, utility players. Examples: Dasun Shanaka, Tim Seifert, Anukul Roy |
| Unlikely to Play | 10% | Uncapped players, net bowlers, deep bench, players who realistically won't feature. Examples: Sachin Fuletra, Shivang Bhatt, Aniket Verma |

**Why not just starter/non-starter?** Because there's a huge difference between a rotation player who might play 5-6 matches and a net bowler who plays 0-1. The four tiers capture this gradient.

**The 92% for "Guaranteed" (not 100%):** Even stars miss matches — rest days, minor niggles, tactical decisions. No player plays every single match.

### Availability Modifier

A float from 0.0 to 1.0 that captures known absences:

| Value | Meaning | Example |
|-------|---------|---------|
| 1.0 | Fully available all season | Most players |
| 0.8–0.9 | Minor concern, may miss 1-2 matches | Player returning from minor strain |
| 0.5–0.7 | Significant absence, will miss 4-7 matches | Recovering from surgery, late joining |
| 0.2–0.4 | Major absence, may only play last few matches | Serious injury, international commitment overlap |
| 0.0 | Ruled out / retired | MS Dhoni if retired, player with season-ending injury |

---

## Overseas Slot Constraint

Each IPL team can play a maximum of 4 overseas players per match. Teams with 5+ quality overseas options face a selection squeeze — some good overseas players will sit on the bench.

This is captured in the **Playing XI Tier** assignment. An overseas player who would be a "Likely Starter" on talent alone gets downgraded to "Rotation" if their team has 5+ strong overseas options competing for 4 slots.

This is NOT a separate multiplier — it's already baked into the tier assignment to avoid double-counting.

---

## What We Do NOT Model (and Why)

| Factor | Why excluded |
|--------|-------------|
| Venue effects | Over 14 matches across 7+ venues, venue advantages wash out |
| Opponent matchups | Schedule is varied enough that matchup effects average out |
| Toss / pitch conditions | Unpredictable, random noise |
| Batting position changes | Too speculative to predict mid-season lineup changes |
| Playoff matches | Excluded per agreed methodology (league stage only) |
| Catches / stumpings | Not part of the scoring system |
| Strike rate bonuses | Not part of the scoring system |

---

## Points Breakdown Example

**Example: Virat Kohli (RCB, owned by Dharmik)**

| Input | Value | Source |
|-------|-------|--------|
| IPL 2025 runs per match | 43.8 (657 runs in 15 matches) | ESPNcricinfo |
| IPL 2024 runs per match | 52.9 (741 runs in 14 matches) | ESPNcricinfo |
| Career runs per match | 32.4 (8661 runs in 267 matches) | ESPNcricinfo |
| Weighted runs per match | 43.8×0.5 + 52.9×0.3 + 32.4×0.2 = **44.25** | Calculated |
| Wickets per match | **0** (pure batter) | — |
| Playing XI tier | Guaranteed (92%) | Franchise icon |
| Availability modifier | 1.0 | Fully fit |
| Expected matches | 14 × 0.92 × 1.0 = **12.88** | Calculated |
| **Expected batting points** | 44.25 × 12.88 = **570** | Calculated |
| **Expected bowling points** | 0 | — |
| **Expected total points** | **570** | — |

**Example: Jasprit Bumrah (MI, owned by Saurabh)**

| Input | Value | Source |
|-------|-------|--------|
| Weighted runs per match | ~2 | Minimal batting |
| Weighted wickets per match | ~1.3 | Elite bowler |
| Playing XI tier | Guaranteed (92%) | India's #1 bowler |
| Availability modifier | 0.85 | Workload management likely |
| Expected matches | 14 × 0.92 × 0.85 = **10.95** | Calculated |
| **Expected batting points** | 2 × 10.95 = **22** | Calculated |
| **Expected bowling points** | 1.3 × 25 × 10.95 = **356** | Calculated |
| **Expected total points** | **378** | — |

---

## Aggregation

For each fantasy owner:

```
Owner Total Points = Sum of Expected Points across all their players
```

The owner with the highest total is the predicted winner.

---

## Confidence Rating

Each player gets a confidence rating based on data quality:

| Rating | Criteria |
|--------|----------|
| High | Stats found from official source, recent seasons available, injury status confirmed |
| Medium | Stats found but some seasons missing, or injury status unclear |
| Low | Stats not found or estimated, or player is very new with minimal IPL history |

---

## Data Sources

Stats are collected from (in order of preference):
1. https://www.iplt20.com/players/ — official IPL website
2. https://www.espncricinfo.com — comprehensive cricket statistics
3. Web search as fallback

Injury/availability information from:
1. Recent news articles (within 30 days)
2. Team announcements
3. Cricket news aggregators

---

## Implementation Files

| File | Purpose |
|------|---------|
| `model.py` | The prediction engine — all formulas above implemented in Python |
| `player_registry.py` | Maps 186 draft nicknames to full player names, roles, overseas status |
| `player_templates.json` | Blank data templates for all 186 players |
| `fetch_player_data.py` | Data collection script (fills templates with real stats) |
| `collect_data.py` | Bridge between data collection and model |
| `run_predictions.py` | Runs model end-to-end, outputs rankings |
| `verification/verify.py` | 4-suite verification (schema, spot-check, sanity, end-to-end) |
