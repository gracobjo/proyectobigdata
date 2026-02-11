#!/bin/bash
# Crea la estructura de directorios en HDFS para el proyecto (modo standalone).
# Ejecutar después de que HDFS tenga al menos 1 DataNode activo.
# Uso: bash scripts/setup/setup_hdfs_dirs.sh

set -e
HDFS_CMD="${HADOOP_HOME:-/usr/local/hadoop}/bin/hdfs dfs"

echo "=== Creando directorios en HDFS ==="

for dir in \
  /user/hadoop \
  /user/hadoop/raw \
  /user/hadoop/processed \
  /user/hadoop/processed/enriched \
  /user/hadoop/checkpoints \
  /user/hadoop/checkpoints/cleaning \
  /user/hadoop/checkpoints/enrichment \
  /user/hadoop/checkpoints/delay_analysis \
  /user/hadoop/checkpoints/delay_hive \
  /user/hadoop/checkpoints/delay_kafka \
  /user/hive \
  /user/hive/warehouse \
  /spark-logs; do
  if $HDFS_CMD -test -d "$dir" 2>/dev/null; then
    echo "  OK (ya existe): $dir"
  else
    $HDFS_CMD -mkdir -p "$dir"
    echo "  Creado: $dir"
  fi
done

echo ""
echo "Estructura actual:"
$HDFS_CMD -ls -R /user 2>/dev/null | head -40
echo ""
echo "=== Fin ==="
