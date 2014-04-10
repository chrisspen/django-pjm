/*
2014.4.8 CKS
Organizes price and load records by hour.
*/
DROP VIEW IF EXISTS django_pjm_hourlysummary CASCADE;
CREATE OR REPLACE VIEW django_pjm_hourlysummary
AS
SELECT  p.node_id,
        p.start_datetime,
        p.end_datetime,
        p.day_ahead,
        p.total,
        p.total + p.congestion + p.marginal_loss as total_price,
        l.segment,
        l.load
FROM    django_pjm_lmpda AS p
LEFT OUTER
        join django_pjm_load AS l ON
        l.node_id = p.node_id
    AND l.start_datetime = p.start_datetime
    AND l.end_datetime = p.end_datetime;