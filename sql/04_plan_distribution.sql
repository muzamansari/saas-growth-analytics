SELECT
    p.plan_name,
    COUNT(*) AS subscriptions
FROM subscriptions s
JOIN subscription_plans p
ON s.plan_id = p.plan_id
GROUP BY p.plan_name
ORDER BY subscriptions DESC;