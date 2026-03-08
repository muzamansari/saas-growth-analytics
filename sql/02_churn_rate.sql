SELECT
    DATE_TRUNC('month', churn_date)::date AS month,
    COUNT(*) AS churned_customers
FROM churn_events
GROUP BY 1
ORDER BY 1;