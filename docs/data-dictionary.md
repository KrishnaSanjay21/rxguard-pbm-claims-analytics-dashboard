# Synthetic data dictionary

## Claims

| Field | Type | Description |
| --- | --- | --- |
| `claim_id` | Text | Synthetic claim identifier. |
| `client_id` | Text | Fictional employer-client key. |
| `member_id` | Text | Synthetic member key. |
| `service_date` | Date | Pharmacy service date. |
| `ndc` | Text | Synthetic NDC-like identifier. |
| `days_supply` | Integer | Submitted days supplied. |
| `claim_status` | Text | PAID, REJECTED, or REVERSED. |
| `rejection_reason` | Text | Reason populated for rejected claims. |
| `gross_cost` | Decimal USD | Gross synthetic drug cost. |
| `member_payment` | Decimal USD | Synthetic member contribution. |
| `plan_payment` | Decimal USD | Synthetic employer-plan contribution. |
| `pharmacy_type` | Text | Retail, Mail, or Specialty. |
| `processed_at` | Date | Synthetic processing date. |

Client, member, and drug dimensions provide fictional names, demographics, risk level, therapeutic class, brand/generic status, maintenance-drug flag, and generic-equivalent opportunity flag. No real individuals, employers, pharmacies, or drug pricing records are present.
