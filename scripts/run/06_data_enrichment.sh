#!/bin/bash
# Enriquecimiento: filtered-data + tablas maestras -> HDFS processed/enriched
# Requisitos: create_tables_spark.py, data_cleaning escribiendo en filtered-data

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Enriquecimiento de datos ==="
echo "Lee: filtered-data (Kafka) + master_routes, master_vehicles (HDFS)"
echo "Escribe: HDFS processed/enriched"
echo ""

spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_enrichment.py
