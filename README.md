# AutoValue AI

**AI-powered used vehicle intelligence**

AutoValue AI is an end-to-end machine learning product that estimates fair market value for Indian used-car listings, scores the asking price as a deal, and returns structured purchase guidance in an interactive Streamlit workspace.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://used-car-price-intelligence-namansinghai.streamlit.app/)

## 🚀 Live Demo

[**Try the Live Application →**](https://used-car-price-intelligence-namansinghai.streamlit.app/)

The application is deployed on Streamlit Community Cloud and provides an interactive AI-powered used-vehicle valuation experience.

---

## What it does

From vehicle attributes and an asking price (₹), AutoValue AI produces a **Vehicle Intelligence Report** that covers:

**Vehicle Data → AI Valuation → Deal Assessment → Market Range → Valuation Signals → Confidence → Negotiation Guidance → Purchase Guidance**

| Capability | What the user sees |
|------------|-------------------|
| **AI Fair Value** | Predicted market value (INR) from the trained regression pipeline |
| **Deal assessment** | Asking vs fair value, deal score (0–100), and verdict (`Good Deal` / `Fairly Priced` / `Overpriced`) |
| **Market range** | Indicative low / mid / high band around the AI estimate (±5%) |
| **Valuation factors & signals** | Heuristic drivers plus positive signals and risks |
| **Prediction confidence** | Coverage-based confidence level and score (not model predictive uncertainty) |
| **Negotiation guidance** | Opening offer, target price, and max recommended anchors |
| **AI purchase guidance** | Rule-based recommendation badge, summary, action line, and next steps |

Outputs are **decision-support insights**, not appraisals or guarantees of sale price.

---

## User workflow

1. **Dashboard** — Model snapshot (listings, feature count, R²) and recent session analyses  
2. **New Valuation** — Enter vehicle basics, configuration, listing flags, and asking price  
3. **Results** — Layered Vehicle Intelligence Report (executive summary always visible; detail in expanders)  
4. **History** — Session-scoped saved analyses  
5. **About** — Product and model metadata  

**New Valuation** form sections:

1. Vehicle basics — year, kilometers, previous owners  
2. Configuration — make, model, fuel, transmission, body type, city, registered state  
3. Listing & pricing — assured buy, warranty, fitness certificate, asking price (₹)  

Then **Generate Valuation** → review the report → optionally **Save Analysis**.

---

## Vehicle Intelligence Report

### Always visible

- Executive summary: vehicle identity, AI fair value, asking price, difference, deal score  
- **AI Verdict** with purchase badge (`STRONG BUY` / `BUY` / `CONSIDER` / `NEGOTIATE` / `AVOID`)  
- **Key Decision Signals** — positives and risks  
- **AI Purchase Guidance** — summary, action line, and next steps  

### Expandable detail

- **Detailed Valuation Analysis** — market range and ask-vs-estimate narrative  
- **What's Driving This Valuation?** — heuristic factor signals and vehicle chips  
- **Negotiation Guidance** — opening / target / max recommended  
- **Confidence & Methodology** — confidence level, score, and methodology notes  

---

## AI valuation methodology (high level)

1. User inputs are validated against ranges and categories present in the training CSV.  
2. Features are engineered consistently with training (`vehicle_age`, `kms_run_log1p`, categoricals, listing flags).  
3. A persisted **scikit-learn Pipeline** (`XGBRegressor`, `log1p` target) predicts fair value; predictions are inverted to the original rupee scale.  
4. Deal score, verdict, market range, confidence, negotiation anchors, vehicle signals, and purchase guidance are derived in `app/deal_analyzer.py` from prediction vs asking price and dataset coverage — **not** a second trained model.

**Leakage excluded from modeling:** broker quote, original price, EMI / booking amounts, times viewed, platform ratings, identifiers (`car_name`, `rto`, `variant`, etc.), and listing-operation flags.

---

## Dataset & model

| Item | Value (from repository artifacts) |
|------|-----------------------------------|
| Dataset | `data/raw/Used_Car_Price_Prediction.csv` |
| Listings | **7,400** |
| Target | `sale_price` (INR regression) |
| Production model | **XGBRegressor** (`models/final_model.joblib`) |
| Target strategy | `log1p` |
| Model features | **13** (see `models/model_metadata.json`) |
| Holdout split | 80/20, `random_state=42` |
| Held-out MAE | ₹44,528 |
| Held-out RMSE | ₹86,942 |
| Held-out R² | **0.912** |

### Model comparison (MAE on rupee scale)

From `reports/model_comparison.csv`:

| Model | Target strategy | MAE (INR) | R² |
|-------|-----------------|-----------|-----|
| **XGBRegressor** | **log1p** | **44,528** | **0.912** |
| XGBRegressor | original | 45,559 | 0.915 |
| RandomForestRegressor | original | 47,515 | 0.896 |
| Ridge | log1p | 49,757 | 0.905 |

The production checkpoint was selected by **best MAE**, then refit on the full cleaned dataset.

### Model feature list

`vehicle_age`, `kms_run_log1p`, `total_owners`, `assured_buy`, `warranty_avail`, `fitness_certificate`, `fuel_type`, `body_type`, `transmission`, `make`, `model`, `city`, `registered_state`

---

## Technology stack

| Layer | Stack |
|-------|--------|
| UI | Streamlit 1.39 |
| ML | scikit-learn, XGBoost, joblib |
| Data | pandas, NumPy, SciPy |
| Runtime (Cloud) | Python 3.11 (`runtime.txt`) |

---

## Project structure

```text
used-car-price-intelligence/
├── app.py                      # Streamlit entrypoint
├── app/
│   ├── deal_analyzer.py        # Inference, deal logic, purchase guidance
│   ├── ui_theme.py             # Branding and CSS
│   ├── ui_display.py           # INR / verdict formatting
│   └── ui_formatting.py        # Category / owner label maps
├── assets/images/              # Hero imagery
├── data/raw/                   # Training / form-option CSV
├── models/
│   ├── final_model.joblib
│   └── model_metadata.json
├── notebooks/01_eda.ipynb
├── reports/
│   ├── model_comparison.csv
│   └── figures/
├── src/
│   ├── data/preprocess.py
│   ├── features/feature_engineering.py
│   └── models/train_models.py, evaluate_models.py
├── requirements.txt
├── runtime.txt
└── README.md
```

---

## Local setup

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Required artifacts (already in the repo for deployment):

- `models/final_model.joblib`
- `models/model_metadata.json`
- `data/raw/Used_Car_Price_Prediction.csv`

To retrain from scratch:

```bash
python -m src.models.train_models
```

---

## Streamlit Community Cloud

| Setting | Value |
|---------|--------|
| Repository | [tangocharlei/used-car-price-intelligence](https://github.com/tangocharlei/used-car-price-intelligence) |
| Branch | `main` |
| Entrypoint | `app.py` |
| Python | `3.11` (`runtime.txt`) |
| Live app | [used-car-price-intelligence-namansinghai.streamlit.app](https://used-car-price-intelligence-namansinghai.streamlit.app/) |

No Streamlit secrets are required for the default app.

---

## Limitations & responsible use

- Fair value is a statistical estimate from historical listing patterns; physical condition, accidents, service history, and local demand are not fully observed.  
- Deal score, confidence, negotiation anchors, and purchase badges are **heuristic overlays**, not calibrated uncertainty or transaction guarantees.  
- Rare make / model / city combinations may lower confidence even when inputs validate.  
- Saved analyses persist only for the current Streamlit session (no database).  
- The app loads a persisted model; it does not retrain on user submissions.

---

## License

This project is intended for educational and portfolio purposes.
