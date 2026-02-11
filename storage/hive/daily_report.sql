-- Script SQL para generar reporte diario de transporte
-- Agregaciones y análisis de datos de retrasos

USE default;

-- Reporte de retrasos por ruta
SELECT 
    route_id,
    route_name,
    DATE(window_start) as report_date,
    SUM(total_vehicles) as total_vehicles,
    AVG(avg_speed) as avg_speed,
    SUM(delayed_count) as total_delayed,
    AVG(delay_percentage) as avg_delay_percentage,
    MAX(max_speed) as max_speed,
    MIN(min_speed) as min_speed
FROM delay_aggregates
WHERE DATE(window_start) = CURRENT_DATE() - 1
GROUP BY route_id, route_name, DATE(window_start)
ORDER BY avg_delay_percentage DESC;

-- Top 5 rutas con más retrasos
SELECT 
    route_id,
    route_name,
    SUM(delayed_count) as total_delayed_vehicles,
    AVG(delay_percentage) as avg_delay_percentage
FROM delay_aggregates
WHERE DATE(window_start) >= CURRENT_DATE() - 7
GROUP BY route_id, route_name
ORDER BY total_delayed_vehicles DESC
LIMIT 5;

-- Análisis de nodos críticos en la red
SELECT 
    id as node_id,
    name as node_name,
    pagerank,
    degree
FROM network_pagerank npr
JOIN network_degrees nd ON npr.id = nd.id
ORDER BY pagerank DESC;

-- Resumen de cuellos de botella
SELECT 
    COUNT(*) as total_bottlenecks,
    AVG(degree) as avg_degree
FROM network_bottlenecks;
