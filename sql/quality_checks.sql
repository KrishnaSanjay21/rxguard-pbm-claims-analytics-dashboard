SELECT 'duplicate_claims' AS check_name, SUM(duplicate_claim) AS issue_count FROM vw_claim_quality
UNION ALL
SELECT 'missing_identifiers', SUM(missing_identifier) FROM vw_claim_quality
UNION ALL
SELECT 'invalid_amounts', SUM(invalid_amount) FROM vw_claim_quality
UNION ALL
SELECT 'inconsistent_dates', SUM(inconsistent_date) FROM vw_claim_quality
UNION ALL
SELECT 'reconciliation_failures', SUM(reconciliation_failure) FROM vw_claim_quality
UNION ALL
SELECT 'reference_failures', SUM(reference_failure) FROM vw_claim_quality
UNION ALL
SELECT 'status_reason_failures', SUM(status_reason_failure) FROM vw_claim_quality;
