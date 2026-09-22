# AutoValue AI: Used Vehicle Valuation & Deal Intelligence

AutoValue AI is an end-to-end machine learning project that estimates **fair market value** for Indian used-car listings, scores deals against an asking price, and surfaces structured purchase guidance in a Streamlit workspace. Models are trained on listing records in `data/raw/Used_Car_Price_Prediction.csv`.

## Problem Statement

Used-car buyers and sellers rarely agree on a single “fair” price. A practical valuation assistant must:

1. Predict sale price from legitimate vehicle and listing attributes only (no price leakage)
2. Compare the seller’s asking price to the model’s fair value on the **original rupee scale**
3. Translate model output into actionable deal intelligence (verdict, negotiation bands, confidence heuristics) without implying guaranteed transaction outcomes

AutoValue AI addresses these goals with a leakage-aware feature schema, compared regression baselines, a persisted XGBoost pipeline, and an interactive Streamlit dashboard with layered reporting.

## Dataset

- **Source:** `data/raw/Used_Car_Price_Prediction.csv`
- **Rows:** 7,400 used-car listings (after loading the raw file)
- **Target:** `sale_price` (regression, INR)
- **Legitimate model inputs:** manufacturing year, odometer, ownership count, fuel/body/transmission, make/model, city/state, and listing quality flags (`assured_buy`, `warranty_avail`, `fitness_certificate`)

**Excluded from modeling** (leakage, identifiers, or platform judgment):

- **Price / engagement leakage:** `broker_quote`, `original_price`, `emi_starts_from`, `booking_down_pymnt`, `times_viewed`
- **Identifiers / high cardinality:** `car_name`, `ad_created_on`, `rto`, `registered_city`, `variant`
- **Listing operations / platform labels:** `car_rating`, `reserved`, `car_availability`, `is_hot`, `source`

EDA notebook: `notebooks/01_eda.ipynb` (figures saved under `reports/figures/`).

## Exploratory Data Analysis

Notebook: `notebooks/01_eda.ipynb`

Key themes from EDA:

- Regression target with wide price spread (luxury outliers present; handled on original scale at evaluation time)
- Strong categorical structure (make, model, city) drives much of the market variation
- Broker quote and original list price correlate with `sale_price` but are excluded to avoid target leakage
- Visual summaries cover price by make, fuel/transmission/body, city, and numeric feature relationships

## Feature Engineering

Module: `src/features/feature_engineering.py`

Engineered features (reference year pinned at training time, stored in metadata):

| Feature | Description |
|---------|-------------|
| `vehicle_age` | `reference_year − yr_mfr` |
| `kms_run_log1p` | `log1p(kms_run)` |
| `total_owners` | Prior owner count |
| `assured_buy`, `warranty_avail`, `fitness_certificate` | Binary listing quality flags |
| `fuel_type`, `body_type`, `transmission`, `make`, `model`, `city`, `registered_state` | Categorical attributes (one-hot encoded in the sklearn pipeline) |

The production model consumes **13** transformed features (see `models/model_metadata.json`).

## Model Comparison

Script: `src/models/train_models.py`

80/20 holdout (`random_state=42`); models compared on **MAE** (rupee scale). Full table: `reports/model_comparison.csv`.

| Model | Target strategy | MAE (INR) | R² |
|-------|-----------------|-----------|-----|
| XGBRegressor | log1p | **44,528** | 0.912 |
| XGBRegressor | original | 45,559 | 0.915 |
| RandomForestRegressor | original | 47,515 | 0.896 |
| Ridge | log1p | 49,757 | 0.905 |

**XGBRegressor** with **`log1p`** target transformation was selected as the production model (best MAE among candidates).

## Final Test Results

Held-out 20% test set metrics for the selected configuration (also in `models/model_metadata.json`):

| Metric | Value |
|--------|-------|
| MAE | ₹44,528 |
| RMSE | ₹86,942 |
| R² | 0.912 |

After selection, the pipeline is **refit on the full cleaned dataset** and saved as `models/final_model.joblib`.

## Deal Intelligence Layer

Module: `app/deal_analyzer.py`

Downstream of fair-value prediction, the app computes (without retraining):

- Deal score (0–100) and verdict vs asking price
- Indicative market range and negotiation guidance
- Confidence heuristics based on how well the vehicle configuration is represented in training data
- Vehicle signals and rule-based **AI purchase guidance** for the results report

These layers are decision-support heuristics, not separate ML models.

## How to Run the Streamlit Application

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Ensure model artifacts exist

The dashboard loads persisted artifacts only — it does **not** retrain on startup:

- `models/final_model.joblib`
- `models/model_metadata.json`

If missing, run:

```bash
python -m src.models.train_models
```

### 4. Launch the dashboard

```bash
streamlit run app.py
```

The app provides:

1. **Dashboard** — training-data stats, model summary, recent saved analyses
2. **New Valuation** — stepped wizard for vehicle details and asking price (₹)
3. **Results** — executive summary, AI verdict, purchase guidance, and expandable detail sections
4. **History** — session-scoped saved analyses
5. **About** — project and model metadata

## 🚀 Live Demo

Deploy this repository on [Streamlit Community Cloud](https://streamlit.io/cloud) (main branch, entrypoint `app.py`, Python version from `runtime.txt`). After publishing, add your public app URL here—for example, the same naming pattern as [MaintAI](https://github.com/tangocharlei/predictive-maintenance-ai):

`https://<your-app-name>.streamlit.app/`

## Project Structure

```text
used-car-price-intelligence/
├── app.py                         # Streamlit dashboard entry point
├── app/
│   ├── deal_analyzer.py           # Inference, deal logic, recommendations
│   ├── ui_theme.py
│   ├── ui_display.py
│   └── ui_formatting.py
├── data/raw/Used_Car_Price_Prediction.csv
├── models/
│   ├── final_model.joblib
│   └── model_metadata.json
├── notebooks/
│   └── 01_eda.ipynb
├── reports/
│   ├── model_comparison.csv
│   └── figures/
├── src/
│   ├── data/preprocess.py
│   ├── features/feature_engineering.py
│   └── models/train_models.py, evaluate_models.py
├── requirements.txt
├── runtime.txt                    # Streamlit Cloud Python version
└── README.md
```

## Limitations

- Listing data may not capture physical condition, service history, accident damage, or local negotiation dynamics
- Fair value is a statistical estimate; deal scores and purchase badges are heuristic overlays
- Rare make/model/city combinations reduce confidence even when inputs validate
- Saved analysis history lives in the Streamlit session only (not a persistent database)
- The dashboard does not retrain or tune models on user submissions

## License

This project is intended for educational and portfolio purposes.
