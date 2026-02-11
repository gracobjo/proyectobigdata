#!/bin/bash
# Script para crear las tablas maestras en Hive

echo "=== Creando Tablas Maestras en Hive ==="
echo ""

cd /home/hadoop/Documentos/ProyectoBigData

# Crear tablas primero (antes de insertar datos)
echo "1. Creando tabla master_routes..."
hive <<EOF
CREATE TABLE IF NOT EXISTS master_routes (
    route_id STRING,
    route_name STRING,
    origin_city STRING,
    destination_city STRING,
    distance_km DOUBLE,
    estimated_time_minutes INT,
    created_at TIMESTAMP
) STORED AS PARQUET
LOCATION 'hdfs://localhost:9000/user/hive/warehouse/master_routes';
EOF

echo ""
echo "2. Creando tabla master_vehicles..."
hive <<EOF
CREATE TABLE IF NOT EXISTS master_vehicles (
    vehicle_id STRING,
    vehicle_type STRING,
    capacity INT,
    company STRING,
    registration_date DATE,
    created_at TIMESTAMP
) STORED AS PARQUET
LOCATION 'hdfs://localhost:9000/user/hive/warehouse/master_vehicles';
EOF

echo ""
echo "3. Insertando datos maestros..."
hive -f data/master/sample_master_data.sql

echo ""
echo "4. Verificando tablas creadas..."
hive -e "SHOW TABLES;"

echo ""
echo "5. Verificando datos..."
hive -e "SELECT COUNT(*) FROM master_routes;"
hive -e "SELECT COUNT(*) FROM master_vehicles;"

echo ""
echo "✓ Tablas maestras creadas exitosamente"
