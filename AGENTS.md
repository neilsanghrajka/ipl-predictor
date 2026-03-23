# IPL 2026 Fantasy Draft Predictor

Predicts the winner of a 7-person fantasy IPL draft.

## Scoring

- `1 run = 1 point`
- `1 wicket = 25 points`

## Canonical Data Flow

- `player_registry.csv` is the only canonical player data file.
- `player_registry.py` is bootstrap-only input for nickname and role mapping.
- Official IPL data is the only source of truth for player stats and official player IDs.
- Kaggle data is not part of the runtime pipeline.

## Quick Start

Run the pipeline in this order:

```bash
python3 build_registry_csv.py
python3 populate_official_ids.py
python3 fetch_player_data.py
python3 enrich_non_stats.py
python3 repair_availability.py
python3 verification/verify.py
python3 run_predictions.py
```

## Files

| File | Description |
|------|-------------|
| `player_registry.csv` | Canonical source of truth for draft slots, official IDs, and stats |
| `build_registry_csv.py` | Bootstrap builder for `player_registry.csv` |
| `populate_official_ids.py` | Refreshes official IPL player IDs and URLs from squad pages |
| `fetch_player_data.py` | Fetches official IPL batting and bowling stats into the CSV |
| `enrich_non_stats.py` | Adds GPT-5.4 lineup/availability enrichment and audit metadata |
| `repair_availability.py` | Repairs schedule-contaminated availability fields without touching lineup or stats |
| `collect_data.py` | CSV-to-model adapter layer |
| `registry_csv.py` | Canonical CSV schema and row helpers |
| `official_ipl.py` | Official IPL draft, squad, and stats fetch helpers |
| `grounded_research.py` | Shared OpenAI Responses client, schemas, validation, and raw exchange persistence |
| `model.py` | Prediction engine |
| `run_predictions.py` | Generates final rankings |
| `verification/verify.py` | Verification against schema, audit fields, contamination checks, raw inputs, and end-to-end model execution |
| `verification/expected_samples.json` | Known stats for spot-check players |
| `data/raw/` | Latest raw official fixtures, team/player research bundles, availability repairs, squad pages, and player stats payloads |

## Data Rules

- Keep canonical tabular data in CSV format.
- Keep latest raw official fetches under `data/raw/`.
- Do not introduce JSON as a canonical runtime player-data format.
- Do not reintroduce `needs_review`; accepted overrides are final unless explicitly changed.

## Cleanup Rules

- Do not add new debug export artifacts like crosswalk JSON or CSV files at repo root.
- If temporary inspection files are needed, keep them out of the canonical flow and remove them before finishing.
