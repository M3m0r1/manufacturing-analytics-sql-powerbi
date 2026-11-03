SELECT
    COUNT(*) AS units_total,                                    -- кількість рядків у view
    SUM(CASE WHEN final_status = 'Good' THEN 1 END) AS good,    -- рахуємо тільки Good: для інших CASE дає NULL, і SUM його пропускає
    COUNT(DISTINCT unit_id) AS distinct_units                   -- кількість унікальних виробів
FROM vw_units_enriched;  