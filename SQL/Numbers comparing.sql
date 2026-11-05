-- Контрольні суми: порівнюємо з числами зі скриптів Python
USE Mfg_Analytics;
GO

SELECT 
	'Planned Units'				AS metric, 
	SUM(planned_good_units)     AS value 
	FROM production_plan

UNION ALL

SELECT 
	'Units',           
	COUNT(*)                                              
FROM units

UNION ALL

SELECT 
	'Good',            
	COUNT(*)                                              
FROM units 
WHERE final_status = 'Good'

UNION ALL

SELECT 
	'Rejected',        
	COUNT(*)                                              
FROM units 
WHERE final_status = 'Rejected'

UNION ALL

SELECT 
	'Good без етапу списання', 
	COUNT(*)                                      
FROM units 
WHERE 
	final_status = 'Good' 
	AND scrapped_at_stage_id IS NULL

UNION ALL

SELECT 
	'Tested units',    
	COUNT(DISTINCT unit_id)                               
FROM test_results

UNION ALL

SELECT 
	'Test attempts',   
	COUNT(*)                                              
FROM test_results

UNION ALL

SELECT 
	'Downtime minutes', 
	SUM(duration_min)                                    
FROM downtime_records

UNION ALL

SELECT 
	'Total cost',      
	CAST(ROUND(SUM(total_cost), 0) AS BIGINT)             
FROM production_costs;