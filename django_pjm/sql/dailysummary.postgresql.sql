/*
2014.4.8 CKS
Aggregates hourly values into daily values.
*/
DROP VIEW IF EXISTS django_pjm_dailysummary CASCADE;
CREATE OR REPLACE VIEW django_pjm_dailysummary
AS
SELECT  CONCAT(CAST(p.node_id AS VARCHAR), '-', CAST(p.segment AS VARCHAR), '-', CAST(p.start_datetime::date AS VARCHAR)) AS id,
        p.node_id,
        p.segment,
        p.start_datetime::date AS start_date,
        SUM(CASE WHEN p.day_ahead = false THEN p.load ELSE null END)::float AS sum_load,
        AVG(CASE WHEN p.day_ahead = false THEN p.total ELSE null END)::float AS avg_total,
        AVG(CASE WHEN p.day_ahead = true THEN p.total ELSE null END)::float AS avg_total_da,
        AVG(CASE WHEN p.day_ahead = false THEN p.total_price ELSE null END)::float AS avg_total2,
        AVG(CASE WHEN p.day_ahead = true THEN p.total_price ELSE null END)::float AS avg_total2_da
FROM    django_pjm_hourlysummary AS p
WHERE   p.segment IS NOT NULL
GROUP BY
        p.node_id, p.segment, start_date;