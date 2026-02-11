#!/bin/bash
# Análisis de grafos (batch, una ejecución)
# Requisitos: pip install graphframes-py setuptools en el venv

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Análisis de grafos ==="
echo "Genera: network_pagerank, network_degrees, network_bottlenecks en HDFS"
echo ""

PYSPARK_PYTHON=./venv/bin/python spark-submit \
  --master "local[*]" \
  --packages io.graphframes:graphframes-spark3_2.12:0.10.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/graphframes/network_analysis.py

echo ""
echo "Verificar: hdfs dfs -ls /user/hive/warehouse/network_bottlenecks/"
