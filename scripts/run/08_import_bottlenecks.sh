#!/bin/bash
# Importa bottlenecks desde HDFS a MongoDB (ejecutar después de 07_network_analysis.sh)

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Importar bottlenecks a MongoDB ==="
echo "Lee de: HDFS network_bottlenecks"
echo "Escribe en: MongoDB transport_db.bottlenecks"
echo ""

spark-submit --master "local[*]" \
  --conf spark.driver.host=127.0.0.1 \
  storage/mongodb/import_bottlenecks.py

echo ""
echo "Verificar: python storage/mongodb/verify_data.py"
