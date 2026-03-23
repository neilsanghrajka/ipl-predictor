# Repository Instructions

## Canonical Data Flow

- `player_registry.csv` is the only canonical player data file.
- `player_registry.py` is bootstrap-only input for nickname and role mapping.
- Official IPL data is the only source of truth for player stats and official player IDs.
- Kaggle data is not part of the runtime pipeline.

## Pipeline

Run the pipeline in this order:

```bash
python3 build_registry_csv.py
python3 populate_official_ids.py
python3 fetch_player_data.py
python3 verification/verify.py
python3 run_predictions.py
```

## Data Files

- Keep canonical tabular data in CSV format.
- Keep latest raw official fetches under `data/raw/`.
- Do not introduce JSON as a canonical runtime player-data format.
- Do not reintroduce `needs_review`; accepted overrides are final unless explicitly changed.

## Cleanup Rules

- Do not add new debug export artifacts like crosswalk JSON/CSV files at repo root.
- If temporary inspection files are needed, keep them out of the canonical flow and remove them before finishing.
