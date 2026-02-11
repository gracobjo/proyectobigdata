# Iniciar el Pipeline Completo

## Estado Actual

El consumidor MongoDB está esperando datos, pero el pipeline no está generando mensajes en el topic `alerts`.

## Orden de Ejecución

Para que el consumidor MongoDB procese datos, necesitas ejecutar el pipeline en este orden:

### 1. Generar Datos de Prueba (si no hay)

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Generar 100 mensajes de prueba
python scripts/utils/generate_sample_data.py 100
```

### 2. Limpieza de Datos (genera `filtered-data`)

```bash
# En una terminal
spark-submit \
  --master "local[*]" \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_cleaning.py
```

**Espera a que procese algunos batches** (verás mensajes en la consola).

### 3. Análisis de Retrasos (genera `alerts`)

```bash
# En otra terminal (mientras data_cleaning.py sigue corriendo)
spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/streaming/delay_analysis.py
```

**Nota:** El parámetro `--packages` es necesario para el conector de Kafka.

**Ahora el consumidor MongoDB debería empezar a procesar mensajes** y verás:
```
✓ Insertado: R004 @ 2026-02-11 00:00:00 (22 vehículos, 77.3% retraso)
```

### 4. Verificar Resultados

```bash
# Verificar MongoDB
python storage/mongodb/verify_data.py

# Verificar Kafka
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic alerts \
  --from-beginning \
  --max-messages 5
```

## Resumen del Flujo

```
generate_sample_data.py
    ↓ (escribe en raw-data)
data_cleaning.py
    ↓ (escribe en filtered-data)
delay_analysis.py
    ↓ (escribe en alerts)
kafka_to_mongodb_alerts.py ← ESTÁ ESPERANDO AQUÍ
    ↓ (escribe en MongoDB)
route_delay_aggregates
```

## Verificar Estado del Pipeline

```bash
bash scripts/utils/check_pipeline_status.sh
```

Este script muestra:
- Qué servicios están corriendo
- Cuántos mensajes hay en cada topic de Kafka
- Cuántos archivos hay en HDFS
- Estado de las colecciones MongoDB
