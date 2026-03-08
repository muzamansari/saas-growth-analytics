SELECT
    DATE_TRUNC('month', billing_period_start)::date AS month,
    SUM(invoice_amount) AS monthly_revenue
FROM invoices
WHERE invoice_status = 'paid'
GROUP BY 1
ORDER BY 1;