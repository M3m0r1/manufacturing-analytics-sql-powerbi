USE [Ajax_Mfg_Analytics]
GO
-- 1.1 Rejection rate per line
SELECT
    line_name,
    CAST(SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) * 100.0
         / COUNT(*) AS DECIMAL(5,2)) AS rejection_rate
FROM dbo.vw_units_enriched
GROUP BY line_name

-- 1.2 Part of rejections of each line
SELECT
    line_name,
    SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
    CAST(
        SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) * 100.0
            / SUM(SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END)) OVER ()
    AS DECIMAL(4,2)) AS share_of_all_rejected
FROM vw_units_enriched
GROUP BY line_name
ORDER BY line_name ASC

-- 1.3 Брак по зрізах і перевірка історій G1 і G2
-- По змінах: у який час брак вищий
SELECT
    shift_name,
    COUNT(*) AS produced,
    SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
    CAST(ROUND(SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS DECIMAL(5,2)) AS scrap_rate_pct
FROM vw_units_enriched
GROUP BY shift_name;

-- По продуктах
SELECT
    product_code,
    COUNT(*) AS produced,
    SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
    CAST(ROUND(SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS DECIMAL(5,2)) AS scrap_rate_pct
FROM vw_units_enriched
GROUP BY product_code
ORDER BY scrap_rate_pct DESC;

-- G2: частка виробів, списаних саме на етапі 4 (фінальне складання), по змінах
SELECT
    shift_name,
    CAST(ROUND(SUM(CASE WHEN scrapped_at_stage_id = 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS DECIMAL(5,2)) AS stage4_scrap_pct
FROM vw_units_enriched
GROUP BY shift_name;

-- G1: частка виробів лінії C, списаних на етапі 2 (пайка), по місяцях
SELECT
    [month],
    ROUND(SUM(CASE WHEN scrapped_at_stage_id = 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS stage2_scrap_pct
FROM vw_units_enriched
WHERE line_name = 'Line C'                                               -- лише лінія C
GROUP BY [month]
ORDER BY [month]
;
SELECT
    [month],
    line_name,
    CAST(ROUND(SUM(CASE WHEN scrapped_at_stage_id = 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS DECIMAL(4,2)) AS stage2_scrap_pct
FROM vw_units_enriched
GROUP BY [month], line_name
ORDER BY line_name, [month];

-- 2.1 План і факт по місяцях
WITH plan_m AS (                                          -- крок 1: план, зведений до місяця
    SELECT
        d.[month],
        SUM(p.planned_good_units) AS planned              -- скільки придатних виробів планували
    FROM production_plan p
    JOIN dim_date d ON d.date_id = p.date_id              -- додаємо номер місяця
    GROUP BY d.[month]
),
fact_m AS (                                               -- крок 2: факт, зведений до місяця
    SELECT
        [month],
        SUM(CASE WHEN final_status = 'Good' THEN 1 ELSE 0 END) AS good   -- скільки придатних випустили
    FROM vw_units_enriched
    GROUP BY [month]
)
SELECT                                                    -- крок 3: з'єднуємо два готові результати
    pm.[month],
    pm.planned,
    fm.good,
    fm.good - pm.planned AS variance_to_plan,             -- відхилення: мінус означає недовиконання
    CAST(fm.good * 100.0 / NULLIF(pm.planned, 0) AS DECIMAL(5,2)) AS plan_achievement_pct  -- NULLIF: захист від ділення на 0
FROM plan_m pm
JOIN fact_m fm ON fm.[month] = pm.[month]
ORDER BY pm.[month];

-- 2.2 План і факт по лініях
WITH plan_l AS (
    SELECT
        l.line_name,
        SUM(p.planned_good_units) AS planned
    FROM production_plan p
    JOIN production_lines l ON l.line_id = p.line_id
    GROUP BY l.line_name
),
fact_l AS (
    SELECT
        line_name,
        SUM(CASE WHEN final_status = 'Good' THEN 1 ELSE 0 END) AS good
    FROM vw_units_enriched
    GROUP BY line_name
)
SELECT
    pl.line_name,
    pl.planned,
    fl.good,
    fl.good - pl.planned AS variance_to_plan,
    CAST(fl.good * 100.0 / NULLIF(pl.planned, 0) AS DECIMAL(5,2)) AS plan_achievement_pct
FROM plan_l pl
JOIN fact_l fl ON fl.line_name = pl.line_name
ORDER BY plan_achievement_pct;                            -- найгірша лінія першою


-- 3.1 FPY і Retest Rate загалом
WITH per_unit AS (                                        -- крок 1: один рядок = один протестований виріб
    SELECT
        unit_id,
        MAX(CASE WHEN attempt_no = 1 AND result = 'Pass'
                 THEN 1 ELSE 0 END) AS first_pass,        -- 1, якщо перша спроба успішна; MAX зводить рядки виробу до одного значення
        MAX(attempt_no) AS attempts                       -- скільки було спроб (1, 2 або 3)
    FROM test_results
    GROUP BY unit_id                                      -- групуємо по виробу, щоб не було дублів
)
SELECT                                                    -- крок 2: рахуємо KPI по виробах
    COUNT(*) AS tested_units,                             -- кількість ВИРОБІВ (не спроб)
    SUM(first_pass) AS passed_first_time,                 -- скільки пройшли з першої спроби
    SUM(CASE WHEN attempts >= 2 THEN 1 ELSE 0 END) AS retested_units,  -- скільки мали повторний тест
    CAST(SUM(first_pass) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS fpy_pct,            -- FPY = пройшли з першої / усі протестовані
    CAST(SUM(CASE WHEN attempts >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS retest_rate_pct  -- Retest = мали 2+ спроби / усі протестовані
FROM per_unit;

-- 3.2 FPY і Retest Rate по продуктах
WITH per_unit AS (
    SELECT
        unit_id,
        MAX(CASE WHEN attempt_no = 1 AND result = 'Pass' THEN 1 ELSE 0 END) AS first_pass,
        MAX(attempt_no) AS attempts
    FROM test_results
    GROUP BY unit_id
)
SELECT
    v.product_code,                                       -- продукт беремо з view
    COUNT(*) AS tested_units,
    CAST(SUM(pu.first_pass) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS fpy_pct,
    CAST(SUM(CASE WHEN pu.attempts >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS retest_rate_pct
FROM per_unit pu
JOIN vw_units_enriched v ON v.unit_id = pu.unit_id        -- один рядок на виріб з обох боків, тому рядки не множаться
GROUP BY v.product_code
ORDER BY fpy_pct;                                         -- найгірший FPY першим

-- 3.3 Retest Rate лінії C по місяцях
WITH per_unit AS (
    SELECT unit_id, MAX(attempt_no) AS attempts
    FROM test_results
    GROUP BY unit_id
)
SELECT
    v.[month],
    COUNT(*) AS tested_units,
    CAST(SUM(CASE WHEN pu.attempts >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS retest_rate_pct
FROM per_unit pu
JOIN vw_units_enriched v ON v.unit_id = pu.unit_id
WHERE v.line_name = 'Line C'                              -- лише лінія C
GROUP BY v.[month]
ORDER BY v.[month];

-- 3.4 Перевірка: спроби і вироби не змішуються
SELECT
    COUNT(*)                 AS test_rows,                -- спроби
    COUNT(DISTINCT unit_id)  AS tested_units              -- вироби 
FROM test_results;

-- 4.1 Простої за причинами
SELECT
    r.reason_name,                                                    -- причина
    r.category,                                                       -- група причин
    r.is_planned,                                                     -- 1 = плановий простій
    COUNT(*) AS events,                                               -- скільки було подій
    CAST(SUM(dr.duration_min) / 60.0 AS DECIMAL(8,1)) AS downtime_hours,  -- скільки годин (60.0, щоб ділення не було цілим)
    CAST(SUM(dr.duration_min) * 100.0
         / SUM(SUM(dr.duration_min)) OVER () AS DECIMAL(5,1)) AS share_pct  -- частка від усіх простоїв
FROM downtime_records dr
JOIN downtime_reasons r ON r.reason_id = dr.reason_id                 -- підтягуємо назву причини
GROUP BY r.reason_name, r.category, r.is_planned
ORDER BY downtime_hours DESC;                                         -- найбільша причина першою

-- 4.2 Downtime % по змінах
WITH line_days AS (                                                   -- скільки пар "день + лінія" було у виробництві
    SELECT COUNT(*) AS n
    FROM (SELECT DISTINCT date_id, line_id FROM production_plan) x
),
dt AS (                                                               -- простої, зведені до зміни
    SELECT shift_id, SUM(duration_min) AS downtime_min
    FROM downtime_records
    GROUP BY shift_id
)
SELECT
    s.shift_name,
    dt.downtime_min,
    s.planned_run_min * ld.n AS planned_minutes,                      -- 660 хв на кожну пару "день + лінія"
    CAST(dt.downtime_min * 100.0 / (s.planned_run_min * ld.n) AS DECIMAL(5,2)) AS downtime_pct
FROM shifts s
JOIN dt ON dt.shift_id = s.shift_id
CROSS JOIN line_days ld;                                              -- додаємо однакове число ld.n до кожної зміни

-- 4.3 Нестача деталей по лініях
SELECT
    l.line_name,
    SUM(dr.duration_min) AS shortage_minutes                          -- хвилини простою через нестачу деталей
FROM downtime_records dr
JOIN production_lines l ON l.line_id = dr.line_id
WHERE dr.reason_id = 1                                                -- 1 = Component Shortage
GROUP BY l.line_name;

-- 5.1 Cost per Good Unit по продуктах
WITH cost AS (                                            -- крок 1: загальні витрати по продуктах
    SELECT
        product_id,
        SUM(total_cost) AS total_cost                     -- матеріали + праця + накладні
    FROM production_costs
    GROUP BY product_id
),
good AS (                                                 -- крок 2: кількість придатних виробів по продуктах
    SELECT
        product_id,
        COUNT(*) AS good_units
    FROM vw_units_enriched
    WHERE final_status = 'Good'                           -- ділимо тільки на придатні (їх можна продати)
    GROUP BY product_id
)
SELECT                                                    -- крок 3: з'єднуємо два готові результати
    p.product_code,
    c.total_cost,
    g.good_units,
    CAST(c.total_cost / g.good_units AS DECIMAL(10,2)) AS cost_per_good_unit   -- K12
FROM products p
JOIN cost c ON c.product_id = p.product_id
JOIN good g ON g.product_id = p.product_id
ORDER BY p.product_id;

-- 5.2 Брак за етапами та збитки (K13 і K14)
SELECT
    st.stage_name,                                                    -- назва етапу
    COUNT(*) AS rejected_units,                                       -- скільки виробів списано на цьому етапі
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS DECIMAL(5,1)) AS pct_of_all_rejected,  -- K13: частка етапу в усьому браку
    CAST(SUM(p.material_cost_uah * st.cost_accumulated_pct) AS DECIMAL(12,0)) AS scrap_cost_uah  -- K14: матеріали, уже вкладені у виріб
FROM vw_units_enriched v
JOIN production_stages st ON st.stage_id = v.scrapped_at_stage_id    -- у Good етапу списання немає, тому вони сюди не потраплять
JOIN products p ON p.product_id = v.product_id                       -- потрібна вартість матеріалів продукту
WHERE v.final_status = 'Rejected'
GROUP BY st.stage_order, st.stage_name
ORDER BY st.stage_order;

-- 6.1 Динаміка по місяцях: придатні, зміна до попереднього місяця, брак
WITH monthly AS (                                         -- крок 1: підсумки по кожному місяцю
    SELECT
        [month],
        month_name,
        COUNT(*) AS produced,                             -- скільки виробів запущено
        SUM(CASE WHEN final_status = 'Good' THEN 1 ELSE 0 END) AS good,         -- скільки придатних
        SUM(CASE WHEN final_status = 'Rejected' THEN 1 ELSE 0 END) AS rejected  -- скільки забракованих
    FROM vw_units_enriched
    GROUP BY [month], month_name
)
SELECT                                                    -- крок 2: додаємо порівняння з попереднім місяцем
    month_name,
    good,
    LAG(good) OVER (ORDER BY [month]) AS prev_month_good, -- LAG: значення good з попереднього рядка (для першого місяця буде NULL)
    CAST((good - LAG(good) OVER (ORDER BY [month])) * 100.0
         / NULLIF(LAG(good) OVER (ORDER BY [month]), 0) AS DECIMAL(6,2)) AS mom_change_pct,  -- зміна до попереднього місяця, %
    CAST(rejected * 100.0 / produced AS DECIMAL(5,2)) AS scrap_rate_pct       -- брак у місяці
FROM monthly
ORDER BY [month];