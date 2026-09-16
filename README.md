# RxGuard — PBM Claims Analytics Dashboard

RxGuard is a Python and Streamlit portfolio dashboard for a fictional pharmacy benefit manager. It combines deterministic synthetic claims data, SQLite transformations, governed KPI definitions, automated data-quality checks, interactive Plotly analysis, a PDC-style adherence demonstration, and downloadable Excel client packs.

> **Synthetic-data notice:** every claim, member, client, cost, NDC-like code, and drug name in this repository is fictional. The project contains no PHI and is not a production PBM system.

## Dashboard pages

- **Executive Summary:** total claims, paid cost, member and plan cost, generic dispensing rate, rejection rate, and cost per paid claim.
- **Client Reporting:** employer-group comparisons, monthly trends, and formatted Excel exports.
- **Drug Analysis:** high-cost drugs, therapeutic classes, brand/generic opportunity flags, and unusual cost increases.
- **Claims Operations:** paid, rejected, and reversed claims, rejection reasons, and processing volume.
- **Adherence:** a clearly labeled PDC-style portfolio proxy for maintenance therapies. It is not a certified HEDIS measure.
- **Data Quality:** duplicate claims, missing identifiers, invalid amounts, inconsistent dates, broken references, status/reason conflicts, and payment reconciliation failures.

## Architecture

```text
Synthetic CSVs
    |
    v
Python validation and SQLite load
    |
    v
SQL quality flags + enriched analytical view
    |
    +--> Streamlit + Plotly dashboard
    +--> Excel client reporting pack
    +--> pytest regression checks
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m scripts.generate_data
python -m scripts.refresh
streamlit run app.py
```

The first dashboard run also creates the SQLite database automatically if it does not exist.

## Test

```bash
pytest -q
```

## Repository structure

- `rxguard/` — reusable generation, ETL, metrics, charts, exports, and data-access code
- `pages/` — six Streamlit dashboard pages
- `sql/` — analytical model and data-quality checks
- `data/source/` — versioned synthetic CSV inputs
- `data/negative/` — deliberately broken claim rows
- `docs/` — KPI dictionary, data dictionary, and methodology
- `tests/` — pipeline, KPI, Excel-export, and Streamlit smoke tests

## Important limitations

This is an evidence-backed portfolio implementation, not a production PBM platform. Cost signals are synthetic, generic opportunities are illustrative, and the adherence calculation omits measure-specific exclusions and enrollment rules. Review [the methodology](docs/methodology.md) and [KPI dictionary](docs/kpi-dictionary.md) before reusing any logic.
