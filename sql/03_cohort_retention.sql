SELECT
    DATE_TRUNC('month', subscription_start)::date AS cohort_month,
    COUNT(*) AS customers
FROM subscriptions
GROUP BY 1
ORDER BY 1;