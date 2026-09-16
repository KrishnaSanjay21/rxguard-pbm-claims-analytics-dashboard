# Methodology and limitations

RxGuard is a portfolio demonstration for PBM claims analytics. The source CSVs are generated with a fixed random seed and contain no protected health information or real client records.

The refresh pipeline loads four source files into SQLite, applies referential and claim-level SQL checks, and exposes enriched analytical views. Rows with any quality flag remain visible on the Data Quality page but are excluded from KPI calculations.

Cost metrics intentionally use paid claims only. Rejected claims carry zero cost. Reversed claims remain visible in operations but do not reduce the paid-cost totals. This keeps the demo definitions easy to audit; production logic would follow the PBM's financial settlement rules.

The adherence page uses a simple days-supplied proxy from first fill through the end of the last fill's days supplied. It does not handle overlapping fills, inpatient stays, continuous enrollment, clinical exclusions, or formal measure specifications. It must not be described as a certified PDC or HEDIS result.
