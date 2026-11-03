-- Кожен рядок: назва перевірки і кількість проблем (очікуємо 0)

-- 1. Придатний виріб, у якого остання спроба тесту не Pass
SELECT 
    N'Good, але остання спроба не Pass' AS check_name, 
    COUNT(*) AS problems
FROM units u
JOIN (
    -- нумеруємо спроби кожного виробу з кінця: rn = 1 це остання спроба
    SELECT unit_id, result,
           ROW_NUMBER() OVER (PARTITION BY unit_id ORDER BY attempt_no DESC) AS rn
    FROM test_results
) t ON t.unit_id = u.unit_id AND t.rn = 1
WHERE u.final_status = 'Good' AND t.result <> 'Pass'

UNION ALL

-- 2. Вироби, списані на етапах 1-4, не мали б мати тестів
SELECT 
    N'Списані на етапах 1-4, але мають тести', 
    COUNT(DISTINCT u.unit_id)
FROM units u
JOIN test_results t ON t.unit_id = u.unit_id
WHERE u.scrapped_at_stage_id BETWEEN 1 AND 4

UNION ALL

-- 3. Вироби, які дійшли до етапу 5, але тестів не мають
SELECT 
    N'Мали бути протестовані, але тестів немає', 
    COUNT(*)
FROM units u
WHERE (u.scrapped_at_stage_id IS NULL OR u.scrapped_at_stage_id >= 5)
  AND NOT EXISTS (  SELECT 1 
                    FROM test_results t 
                    WHERE t.unit_id = u.unit_id)

UNION ALL

-- 4. Партія: qty_started має дорівнювати кількості її виробів
SELECT 
    N'Партії: qty_started не збігається з виробами', 
    COUNT(*)
FROM batches b
LEFT JOIN ( SELECT 
                batch_id, 
                COUNT(*) AS n 
            FROM units 
            GROUP BY batch_id) x
       ON x.batch_id = b.batch_id
WHERE b.qty_started <> ISNULL(x.n, 0)

UNION ALL

-- 5. Fail-інспекція має належати лише забракованому виробу
SELECT 
    N'Fail-інспекція у виробу не Rejected', 
    COUNT(*)
FROM quality_inspections q
JOIN units u ON u.unit_id = q.unit_id
WHERE 
    q.result = 'Fail' 
    AND u.final_status <> 'Rejected'

UNION ALL

-- 6. Reworked-інспекція має належати лише придатному виробу
SELECT 
    N'Reworked-інспекція у виробу не Good', 
    COUNT(*)
FROM quality_inspections q
JOIN units u ON u.unit_id = q.unit_id
WHERE 
    q.result = 'Reworked' 
    AND u.final_status <> 'Good'

UNION ALL

-- 7. Номери спроб мають йти підряд: кількість спроб = найбільший номер
SELECT 
    N'Прогалини в номерах спроб', 
    COUNT(*)
FROM (
    SELECT unit_id
    FROM test_results
    GROUP BY unit_id
    HAVING COUNT(*) <> MAX(attempt_no)
) g

UNION ALL

-- 8. Інспекція має вказувати той самий етап, на якому списано виріб
SELECT
    N'Інспекція вказує не той самий етап на якому списано виріб',
    COUNT(*)
FROM quality_inspections q 
JOIN units u ON u.unit_id = q.unit_id
WHERE 
    u.scrapped_at_stage_id <> q.stage_id
    AND u.scrapped_at_stage_id IS NOT NULL
    AND q.stage_id IS NOT NULL