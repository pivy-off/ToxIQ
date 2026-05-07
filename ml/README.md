# PharmaSim — ML / data module

This folder holds **machine learning, feature extraction, and demo data** for PharmaSim. It is designed to plug into a FastAPI backend (or similar) with clean imports from the repository root.

## Product positioning (read this first)

PharmaSim outputs are **predictive, simulated, and estimated** — useful for **early-stage in silico screening demos** and team storytelling. They are **not** clinically proven, medically validated, or a substitute for regulated preclinical or clinical testing.

## End-to-end prediction flow (whole product)

1. **User** picks or enters a compound in the **Next.js** UI (name, SMILES, dose, route, or a preset like acetaminophen).
2. **Frontend** sends **`POST /predict`** (or **`/compare`** for two compounds) to the **FastAPI** backend.
3. **Backend** calls **`ml.src.pipeline.run_predict`**: validate SMILES → RDKit **features** → optional **ADMET-AI** (when the package is installed; disable with env) → **PK** (F, CL/Vd, t½ from formula, simulated **curve**) → **toxicity** + **derived metrics** + **safety score** → **organ map**, **pathway steps**, **risk list**, **trial copy**, **display flags**, **`pk_display`** (card-friendly numbers).
4. **Response** is one **JSON** (see `/predict`). **GET `/compounds`** lists preset ids and aliases for UI chips (`tylenol` → acetaminophen, etc.).
5. **Frontend** uses that JSON for charts, copy, and the body-journey visuals — no second round trip through the ML layer unless the user runs another predict/compare.

## Layout

```
ml/
├── README.md                 # This file
├── data/
│   ├── raw/                  # Drop-in raw tables (CSV, etc.) — optional for MVP
│   ├── processed/            # Train-ready splits — optional for MVP
│   └── demo_compounds.json   # Preset compounds for stable demos (filled in Step 3)
├── models/
│   └── trained/              # Serialized models (joblib/pkl) when you train them
├── src/                      # Core Python package-style modules (predictors, pipeline)
├── scripts/                  # prepare_data, train_*, evaluate_* entry points
├── utils/                    # SMILES helpers, constants, shared helpers
└── notebooks/                # Exploratory work (optional)
```

## What is “real” vs heuristic (high level)

| Layer | MVP approach |
|-------|----------------|
| SMILES parsing, RDKit descriptors, fingerprints | **Real** chemistry informatics |
| PK parameters, toxicity classes | **Hybrid** — heuristics now; swap in trained models where noted |
| Safety score, organ %, recommendations, pathway copy | **Heuristic** — transparent rules for demo stability |

## Importing from the backend

Add the repo root to `PYTHONPATH`, or install the project as a package, so the API can do:

```python
from ml.src.pipeline import run_predict  # after pipeline exists
```

(Exact import path will match whatever the team standardizes on in later steps.)

## Next implementation steps (hackathon order)

1. **Step 2** — SMILES validation + RDKit feature extraction (`ml/utils/`, `ml/src/feature_extraction.py`)
2. **Step 3** — Demo compound registry (`ml/data/demo_compounds.json`)
3. **Steps 4–8** — PK, toxicity, safety, organ distribution, reaction pathway modules
4. **Step 9** — Orchestrator (`ml/src/pipeline.py`)
5. **Steps 10–11** — FastAPI `/predict` and `/compare`
6. **Step 12** — Training script templates under `ml/scripts/`

## PK / toxicity outputs (MVP)

- **Bioavailability (F)** — heuristic from logP / TPSA / MW / rotatables (`pk_summary.bioavailability_f`).
- **CL & Vd** — classified low/medium/high with numeric surrogates; **t½ = 0.693 × Vd / CL** only (not fit independently).
- **PK curve** — one-compartment oral model → **Cmax, Tmax, AUC, Cmin** (trough after peak).
- **Derived** — `cmax_cmin_ratio`, spike flag, **therapeutic index proxy** with class (`safe` / `moderate` / `high_risk`).
- **Toxicity** — hepatotoxicity (0–100), hERG proxy score + class, Ames probability + boolean.
- **Safety score** — interpretable weighted formula in `ml/src/safety_score.py`.

Run the API from the repo root: `uvicorn backend.app.main:app --reload` (after `pip install -r backend/requirements.txt`). Use **Python 3.10–3.12** so RDKit wheels install cleanly.

### ADMET-AI (optional)

PharmaSim uses the published **[admet-ai](https://pypi.org/project/admet-ai/)** package (`ADMETModel.predict`), not HTTP calls to the public website. **ADMET-AI v2** (current PyPI) is retrained vs **v1** (paper and [admet.ai.greenstonebio.com](https://admet.ai.greenstonebio.com) demo); numbers will not match v1 exactly — see the [PyPI project description](https://pypi.org/project/admet-ai/).

1. **Python ≥3.11** for `admet-ai` (team venv: 3.12 + `backend/requirements.txt` for RDKit is a good combo).
2. Install: `pip install -r backend/requirements.txt -r backend/requirements-admet.txt` (equivalent to adding **`admet-ai`** from PyPI; pulls **PyTorch** / Chemprop — large download).
3. **Default:** if `admet-ai` imports, ADMET runs automatically — no env var needed.
4. **Disable** on small hosts: `export PHARMASIM_USE_ADMET_AI=0` (or `false` / `off` / `no`).
5. Restart the API. Startup **warmups** model load when ADMET is on.
6. **Optional:** same stack’s browser UI locally: `pip install 'admet-ai[web]'` then `admet_web` → [http://127.0.0.1:5000](http://127.0.0.1:5000) (per PyPI docs).

**Flow:** `/predict` → validate SMILES → RDKit features → if ADMET is enabled and healthy, **`ADMETModel.predict(smiles=...)`** (PyPI API) → oral bioavailability (if matched) is **blended** into **F** and the PK curve is recomputed → toxicity fields from matched ADMET endpoints when possible (demo JSON tox overrides skipped) → response includes `admet_ai` `{ enabled, used, error, sample_properties, … }`. If ADMET is off, missing, or errors, heuristics only.

## Dependencies

See `backend/requirements.txt`. Optional later: pandas, scikit-learn, SciPy, XGBoost/LightGBM for training scripts.

## Disclaimer string (for API responses)

Use a consistent disclaimer in JSON responses, for example:

*“Predictions are for early-stage research exploration only and are not clinically validated.”*
