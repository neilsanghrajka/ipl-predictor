# IPL 2026 Fantasy Draft Predictor

Predicts the winner of a 7-person fantasy IPL draft.

**Scoring:** 1 run = 1 point, 1 wicket = 25 points

## Quick Start

```bash
# 1. Fetch player data (YOU implement this)
python fetch_player_data.py

# 2. Verify the data
python verification/verify.py

# 3. Run predictions
python run_predictions.py
```

## Files

| File | Status | Description |
|------|--------|-------------|
| `PRD.md` | ✅ | Full specification for data collection |
| `model.py` | ✅ | Prediction engine |
| `player_registry.py` | ✅ | Nickname → full name mapping (186 players) |
| `collect_data.py` | ✅ | Template generator + model runner |
| `player_templates.json` | ✅ | Blank templates for all 186 players |
| `fetch_player_data.py` | 🔲 STUB | Fetches real stats — **implement this** |
| `run_predictions.py` | ✅ | Generates final rankings |
| `verification/verify.py` | ✅ | 4-suite verification (schema, spot-check, sanity, e2e) |
| `verification/expected_samples.json` | ✅ | Known stats for 5 test players |
