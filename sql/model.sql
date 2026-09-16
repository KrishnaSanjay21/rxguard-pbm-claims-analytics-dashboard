DROP VIEW IF EXISTS vw_claims_enriched;
DROP VIEW IF EXISTS vw_claim_quality;

CREATE INDEX IF NOT EXISTS idx_claims_service_date ON claims_raw(service_date);
CREATE INDEX IF NOT EXISTS idx_claims_client ON claims_raw(client_id);
CREATE INDEX IF NOT EXISTS idx_claims_member ON claims_raw(member_id);
CREATE INDEX IF NOT EXISTS idx_claims_ndc ON claims_raw(ndc);

CREATE VIEW vw_claim_quality AS
WITH duplicate_ids AS (
    SELECT claim_id, COUNT(*) AS duplicate_count
    FROM claims_raw
    WHERE claim_id IS NOT NULL AND TRIM(claim_id) <> ''
    GROUP BY claim_id
), quality AS (
    SELECT
        c.*,
        COALESCE(d.duplicate_count, 0) AS duplicate_count,
        CASE WHEN COALESCE(d.duplicate_count, 0) > 1 THEN 1 ELSE 0 END AS duplicate_claim,
        CASE WHEN c.claim_id IS NULL OR TRIM(c.claim_id) = ''
               OR c.client_id IS NULL OR TRIM(c.client_id) = ''
               OR c.member_id IS NULL OR TRIM(c.member_id) = ''
               OR c.ndc IS NULL OR TRIM(c.ndc) = ''
             THEN 1 ELSE 0 END AS missing_identifier,
        CASE WHEN c.gross_cost IS NULL OR c.member_payment IS NULL OR c.plan_payment IS NULL
               OR c.gross_cost < 0 OR c.member_payment < 0 OR c.plan_payment < 0
             THEN 1 ELSE 0 END AS invalid_amount,
        CASE WHEN DATE(c.service_date) IS NULL OR DATE(c.processed_at) IS NULL
               OR DATE(c.processed_at) < DATE(c.service_date)
               OR (m.member_id IS NOT NULL AND DATE(c.service_date) < DATE(m.effective_date))
               OR (m.termination_date IS NOT NULL AND DATE(c.service_date) > DATE(m.termination_date))
             THEN 1 ELSE 0 END AS inconsistent_date,
        CASE WHEN c.claim_status IN ('PAID', 'REVERSED')
                  AND ROUND(ABS(COALESCE(c.gross_cost, 0) - COALESCE(c.member_payment, 0) - COALESCE(c.plan_payment, 0)), 2) > 0.01
             THEN 1
             WHEN c.claim_status = 'REJECTED'
                  AND ROUND(ABS(COALESCE(c.gross_cost, 0) + COALESCE(c.member_payment, 0) + COALESCE(c.plan_payment, 0)), 2) > 0.01
             THEN 1 ELSE 0 END AS reconciliation_failure,
        CASE WHEN cl.client_id IS NULL OR m.member_id IS NULL OR dr.ndc IS NULL THEN 1 ELSE 0 END AS reference_failure,
        CASE WHEN c.claim_status NOT IN ('PAID', 'REJECTED', 'REVERSED')
               OR (c.claim_status = 'REJECTED' AND (c.rejection_reason IS NULL OR TRIM(c.rejection_reason) = ''))
               OR (c.claim_status <> 'REJECTED' AND COALESCE(TRIM(c.rejection_reason), '') <> '')
             THEN 1 ELSE 0 END AS status_reason_failure
    FROM claims_raw c
    LEFT JOIN duplicate_ids d ON c.claim_id = d.claim_id
    LEFT JOIN clients_raw cl ON c.client_id = cl.client_id
    LEFT JOIN members_raw m ON c.member_id = m.member_id AND c.client_id = m.client_id
    LEFT JOIN drugs_raw dr ON c.ndc = dr.ndc
)
SELECT *,
       duplicate_claim + missing_identifier + invalid_amount + inconsistent_date
       + reconciliation_failure + reference_failure + status_reason_failure AS issue_count
FROM quality;

CREATE VIEW vw_claims_enriched AS
SELECT
    q.claim_id,
    q.client_id,
    cl.client_name,
    cl.industry,
    cl.region,
    q.member_id,
    m.age,
    m.sex,
    m.risk_level,
    DATE(q.service_date) AS service_date,
    STRFTIME('%Y-%m', q.service_date) AS service_month,
    q.ndc,
    dr.drug_name,
    dr.therapeutic_class,
    dr.brand_generic,
    dr.maintenance_flag,
    dr.generic_equivalent_available,
    q.days_supply,
    q.claim_status,
    q.rejection_reason,
    q.gross_cost,
    q.member_payment,
    q.plan_payment,
    q.pharmacy_type,
    DATE(q.processed_at) AS processed_at,
    q.duplicate_claim,
    q.missing_identifier,
    q.invalid_amount,
    q.inconsistent_date,
    q.reconciliation_failure,
    q.reference_failure,
    q.status_reason_failure,
    q.issue_count,
    CASE WHEN q.issue_count = 0 THEN 1 ELSE 0 END AS is_valid_claim
FROM vw_claim_quality q
LEFT JOIN clients_raw cl ON q.client_id = cl.client_id
LEFT JOIN members_raw m ON q.member_id = m.member_id AND q.client_id = m.client_id
LEFT JOIN drugs_raw dr ON q.ndc = dr.ndc;
