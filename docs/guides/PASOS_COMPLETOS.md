# Pasos Completos para Probar el Pipeline MongoDB

## Orden de Ejecución (Paso a Paso)

### ✅ Paso 0: Arrancar HDFS (IMPORTANTE - Primero)

```bash
# Arrancar HDFS
bash scripts/run/00_start_hdfs.sh

# O manualmente:
hdfs --daemon start namenode
sleep 5
hdfs --daemon start datanode
sleep 5
hdfs dfsadmin -safemode leave
```

**Verificar que HDFS está corriendo:**
```bash
jps | grep -E "NameNode|DataNode"
# Debe mostrar: NameNode y DataNode

hdfs dfsadmin -report | head -5
# Debe mostrar información del cluster
```

**⚠️ IMPORTANTE:** Si HDFS no está corriendo, los scripts de Spark fallarán con "Connection refused" en `localhost:9000`.

---

### ✅ Paso 1: Verificar Servicios Base

```bash
# Verificar que Kafka está corriendo
jps | grep Kafka
# Debe mostrar: [número] Kafka

# Verificar que MongoDB está corriendo
pgrep -f mongod || docker ps | grep mongo
# Debe mostrar un proceso o contenedor
```

**Si Kafka no está corriendo:**
```bash
# Arrancar Kafka
KAFKA_HOME=/opt/kafka
$KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server.properties
sleep 5
jps | grep Kafka  # Verificar
```

---

### ✅ Paso 2: Generar Datos de Prueba

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Generar 100 mensajes de prueba en raw-data
python scripts/utils/generate_sample_data.py 100
```

**Verificar que se generaron:**
```bash
# Debe mostrar mensajes JSON
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic raw-data \
  --from-beginning \
  --max-messages 3 \
  --timeout-ms 5000
```

---

### ✅ Paso 3: Ejecutar Limpieza de Datos (Terminal 1)

**Abre una nueva terminal** y ejecuta:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_cleaning.py
```

**Qué esperar:**
- Verás logs de Spark iniciando
- Verás batches procesándose cada 10 segundos
- Debe mostrar mensajes como "Batch X" con número de filas procesadas
- **NO cierres esta terminal**, déjala corriendo

**Verificar que está funcionando:**
```bash
# En otra terminal, verificar que filtered-data tiene mensajes
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic filtered-data \
  --from-beginning \
  --max-messages 3 \
  --timeout-ms 10000
```

---

### ✅ Paso 4: Ejecutar Análisis de Retrasos (Terminal 2)

**Abre otra nueva terminal** y ejecuta:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/streaming/delay_analysis.py
```

**Qué esperar:**
- Verás logs de Spark iniciando
- Verás batches procesándose cada 10 segundos
- Debe mostrar agregados en la consola con ventanas de 15 minutos
- **NO cierres esta terminal**, déjala corriendo

**Verificar que está generando alerts:**
```bash
# En otra terminal, verificar que alerts tiene mensajes
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic alerts \
  --from-beginning \
  --max-messages 3 \
  --timeout-ms 15000
```

Deberías ver mensajes JSON con `route_id`, `delay_percentage`, `total_vehicles`, etc.

---

### ✅ Paso 5: Ejecutar Consumidor MongoDB (Terminal 3)

**Abre otra nueva terminal** y ejecuta:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

python storage/mongodb/kafka_to_mongodb_alerts.py
```

**Qué esperar:**
- Verás: `✓ Conectado a MongoDB: transport_db.route_delay_aggregates`
- Verás: `✓ Conectado a Kafka, consumiendo desde alerts`
- Después de unos segundos, deberías ver mensajes como:
  ```
  ✓ Insertado: R004 @ 2026-02-11 00:00:00 (22 vehículos, 77.3% retraso)
  ✓ Insertado: R001 @ 2026-02-11 00:00:00 (15 vehículos, 60.0% retraso)
  ```

**Si no ves mensajes de inserción:**
- Espera unos segundos (los batches se procesan cada 10 segundos)
- Verifica que `delay_analysis.py` está corriendo y generando datos

---

### ✅ Paso 6: Verificar Datos en MongoDB

**Abre otra nueva terminal** y ejecuta:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

python storage/mongodb/verify_data.py
```

**Qué esperar:**
```
=== Verificación de datos en MongoDB ===

📊 route_delay_aggregates: X documentos
  - Ruta: R004, Ventana: ..., Retraso: 77.3%, Vehículos: 22
  ...

Promedio de retraso por ruta:
  - R004: 77.3% (ventanas: 5)
  - R001: 60.0% (ventanas: 3)
  ...
```

---

## Resumen Visual del Flujo

```
Terminal 1: data_cleaning.py
    ↓ (lee raw-data, escribe filtered-data)
    
Terminal 2: delay_analysis.py
    ↓ (lee filtered-data, escribe alerts)
    
Terminal 3: kafka_to_mongodb_alerts.py
    ↓ (lee alerts, escribe MongoDB)
    
Terminal 4: verify_data.py (solo para verificar)
    ↓ (lee MongoDB, muestra resultados)
```

---

## Comandos Rápidos de Verificación

### Ver estado completo del pipeline:
```bash
bash scripts/utils/check_pipeline_status.sh
```

### Ver mensajes en Kafka:
```bash
# raw-data
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw-data --from-beginning --max-messages 3

# filtered-data
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic filtered-data --from-beginning --max-messages 3

# alerts
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic alerts --from-beginning --max-messages 3
```

### Ver datos en MongoDB:
```bash
python storage/mongodb/verify_data.py
```

---

## Troubleshooting

**Problema:** `delay_analysis.py` falla con "Failed to find data source: kafka"
- **Solución:** Agrega `--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0` al comando spark-submit

**Problema:** El consumidor MongoDB no muestra mensajes
- **Solución:** Verifica que `delay_analysis.py` está corriendo y generando datos en `alerts`

**Problema:** No hay datos en `filtered-data`
- **Solución:** Verifica que `data_cleaning.py` está corriendo y que hay datos en `raw-data`

**Problema:** Kafka no arranca
- **Solución:** Verifica permisos de `~/kafka-logs` o ejecuta `bash scripts/setup/fix_kafka_permissions.sh` (requiere sudo)

---

## Orden de Terminales

1. **Terminal 1:** `data_cleaning.py` (debe estar corriendo primero)
2. **Terminal 2:** `delay_analysis.py` (ejecutar después de que Terminal 1 procese algunos batches)
3. **Terminal 3:** `kafka_to_mongodb_alerts.py` (ejecutar cuando Terminal 2 esté generando alerts)
4. **Terminal 4:** `verify_data.py` (solo para verificar, no necesita estar corriendo continuamente)
