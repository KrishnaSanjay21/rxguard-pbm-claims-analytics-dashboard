# RxGuard KPI dictionary

All measures use valid synthetic claims after the SQL data-quality flags are applied.

| KPI | Formula | Population | Notes |
| --- | --- | --- | --- |
| Total claims | Count of claim rows | Paid, rejected, and reversed | Invalid rows are excluded. |
| Gross drug cost | Sum of `gross_cost` | Paid claims | Reversed and rejected claims are excluded. |
| Member cost | Sum of `member_payment` | Paid claims | Synthetic member responsibility. |
| Plan cost | Sum of `plan_payment` | Paid claims | Synthetic plan responsibility. |
| Generic dispensing rate | Generic paid claims / all paid claims | Paid claims | Claim-count based. |
| Rejection rate | Rejected claims / total claims | All valid claims | Rejection reasons are shown in operations. |
| Cost per paid claim | Gross drug cost / paid claims | Paid claims | Not per member or prescription episode. |
| PDC-style adherence proxy | Min(days supplied / days from first fill through end of last fill supply, 100%) | Maintenance drugs with at least two paid fills | Portfolio demonstration only; not a certified HEDIS measure. |
| Unusual cost increase | A monthly average cost vs its prior three-month average | Paid claims by drug | Each drug's largest increase above 20% is shown. |
