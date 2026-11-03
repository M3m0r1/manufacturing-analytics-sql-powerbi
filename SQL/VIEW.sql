USE Ajax_Mfg_Analytics;                                  
GO                                                       

CREATE VIEW vw_units_enriched AS                         
SELECT
    u.unit_id,                 -- серійний номер виробу
    u.final_status,            -- остаточний статус: Good або Rejected
    u.scrapped_at_stage_id,    -- етап списання (для Good порожньо)
    b.batch_id,                   -- номер партії виробу
    b.shift_id,                   -- номер зміни (1 = Day, 2 = Night)
    s.shift_name,                   -- назва зміни: Day або Night
    w.work_order_id,                  -- номер замовлення, до якого належить партія
    w.date_id,                        -- ключ дня виробництва
    w.line_id,                        -- номер лінії
    w.product_id,                     -- номер продукту
    d.[month],                          -- номер місяця (4-9), у дужках, бо month це службове слово
    d.month_name,                       -- назва місяця
    l.line_name,                            -- назва лінії (Line A ... Line D)
    p.product_code,                             -- код продукту (MS-100 ...)
    p.category                                  -- категорія продукту

FROM units u                                                    -- основа: 1 рядок = 1 виріб

JOIN batches          b     ON b.batch_id       = u.batch_id        -- до виробу підтягуємо його партію
JOIN shifts           s     ON s.shift_id       = b.shift_id        -- до партії підтягуємо зміну
JOIN work_orders      w     ON w.work_order_id  = b.work_order_id   -- до партії підтягуємо замовлення
JOIN dim_date         d     ON d.date_id        = w.date_id         -- до замовлення підтягуємо календар (місяць)
JOIN production_lines l     ON l.line_id        = w.line_id         -- до замовлення підтягуємо лінію
JOIN products         p     ON p.product_id     = w.product_id;     -- до замовлення підтягуємо продукт
GO
