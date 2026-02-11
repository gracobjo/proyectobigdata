#!/bin/bash
# Script para verificar el estado del pipeline
# Uso: bash scripts/utils/check_pipeline_status.sh

echo "=== Estado del Pipeline ==="
echo ""

# Verificar servicios
echo "📦 Servicios:"
if jps | grep -qi kafka; then
    echo "  ✓ Kafka: corriendo"
else
    echo "  ❌ Kafka: NO está corriendo"
fi

if pgrep -f mongod > /dev/null || docker ps | grep -qi mongo; then
    echo "  ✓ MongoDB: corriendo"
else
    echo "  ❌ MongoDB: NO está corriendo"
fi

if jps | grep -qi SparkSubmit; then
    echo "  ✓ Spark jobs: corriendo"
    jps | grep SparkSubmit
else
    echo "  ⚠ Spark jobs: NO están corriendo"
fi

echo ""

# Verificar datos en Kafka
echo "📊 Datos en Kafka:"
for topic in raw-data filtered-data alerts; do
    COUNT=$(timeout 3 /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic "$topic" 2>/dev/null | awk -F: '{sum += $3} END {print sum+0}')
    if [ "$COUNT" -gt 0 ] 2>/dev/null; then
        echo "  ✓ $topic: ~$COUNT mensajes"
    else
        echo "  ⚠ $topic: vacío o no accesible"
    fi
done

echo ""

# Verificar datos en HDFS
echo "💾 Datos en HDFS:"
if hdfs dfs -test -d /user/hadoop/processed/enriched 2>/dev/null; then
    COUNT=$(hdfs dfs -ls /user/hadoop/processed/enriched 2>/dev/null | grep -c "\.parquet$" || echo "0")
    echo "  ✓ enriched: $COUNT archivos Parquet"
else
    echo "  ⚠ enriched: directorio no existe"
fi

if hdfs dfs -test -d /user/hive/warehouse/delay_aggregates 2>/dev/null; then
    COUNT=$(hdfs dfs -ls /user/hive/warehouse/delay_aggregates 2>/dev/null | grep -c "\.parquet$" || echo "0")
    echo "  ✓ delay_aggregates: $COUNT archivos Parquet"
else
    echo "  ⚠ delay_aggregates: directorio no existe"
fi

echo ""

# Verificar MongoDB
echo "🗄️  MongoDB:"
if command -v python3 >/dev/null 2>&1; then
    cd /home/hadoop/Documentos/ProyectoBigData 2>/dev/null
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate 2>/dev/null
        python3 storage/mongodb/verify_data.py 2>/dev/null | grep -E "📊|🚗|🔗" || echo "  ⚠ No se pudo verificar MongoDB"
    fi
fi

echo ""
echo "=== Fin ==="
