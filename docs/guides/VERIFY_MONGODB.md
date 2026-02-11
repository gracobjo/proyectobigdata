# Verificación de Persistencia MongoDB

## ¿Qué está haciendo el consumidor?

El script `kafka_to_mongodb_alerts.py` está:
1. **Esperando mensajes** del topic `alerts` de Kafka
2. **Parseando** cada mensaje JSON (agregados de retrasos por ventana de 15 min)
3. **Insertando/actualizando** documentos en MongoDB (`route_delay_aggregates`)

## Flujo de datos

```
delay_analysis.py (Spark Streaming)
    ↓ (escribe agregados)
Kafka topic: alerts
    ↓ (consume)
kafka_to_mongodb_alerts.py
    ↓ (persiste)
MongoDB: route_delay_aggregates
```

## Cómo comprobar que funciona

### 1. Verificar que hay mensajes en Kafka `alerts`

```bash
# Consumir mensajes del topic alerts directamente
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic alerts \
  --from-beginning \
  --max-messages 5
```

**Qué esperar:** Mensajes JSON como:
```json
{"window_start":"2026-02-11T00:00:00.000+01:00","window_end":"2026-02-11T00:15:00.000+01:00","route_id":"R004","total_vehicles":22,"avg_speed":18.39,"delayed_count":17,"delay_percentage":77.27,"max_speed":90.49,"min_speed":0.0,"analysis_timestamp":"2026-02-11T01:43:36.089+01:00"}
```

### 2. Verificar que el consumidor está procesando

En la terminal donde corre `kafka_to_mongodb_alerts.py`, deberías ver mensajes como:
```
✓ Insertado: R004 @ 2026-02-11 00:00:00 (22 vehículos, 77.3% retraso)
✓ Insertado: R001 @ 2026-02-11 00:00:00 (15 vehículos, 60.0% retraso)
```

Si no ves mensajes, significa que:
- No hay datos en el topic `alerts` (necesitas ejecutar `delay_analysis.py` primero)
- O el consumidor está esperando nuevos mensajes (ya procesó los existentes)

### 3. Verificar datos en MongoDB

```bash
# Conectar a MongoDB
mongosh "mongodb://127.0.0.1:27017/transport_db"
```

**Consultas de verificación:**

```javascript
// Contar documentos insertados
db.route_delay_aggregates.countDocuments()

// Ver los últimos 5 documentos insertados
db.route_delay_aggregates.find().sort({ window_start: -1 }).limit(5).pretty()

// Ver agregados de una ruta específica
db.route_delay_aggregates.find({ route_id: "R004" }).sort({ window_start: -1 }).limit(5).pretty()

// Rutas con mayor porcentaje de retraso
db.route_delay_aggregates.find().sort({ delay_percentage: -1 }).limit(10).pretty()

// Promedio de retraso por ruta
db.route_delay_aggregates.aggregate([
  { $group: { _id: "$route_id", avg_delay: { $avg: "$delay_percentage" }, count: { $sum: 1 } } },
  { $sort: { avg_delay: -1 } }
])
```

### 4. Verificar índices creados

```javascript
// Ver índices de la colección
db.route_delay_aggregates.getIndexes()
```

Deberías ver un índice en `route_id` y `window_start`.

## Próximos pasos

### A. Si no hay datos en `alerts`

Necesitas ejecutar `delay_analysis.py` primero:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Asegúrate de que hay datos en filtered-data (ejecuta data_cleaning.py primero)
# Luego ejecuta delay_analysis.py
spark-submit \
  --master "local[*]" \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/streaming/delay_analysis.py
```

### B. Otros consumidores MongoDB disponibles

1. **`kafka_to_mongodb_vehicle_status.py`**
   - Consume de `filtered-data`
   - Mantiene estado de vehículos en `vehicle_status`
   - Ejecutar en otra terminal:
   ```bash
   python storage/mongodb/kafka_to_mongodb_vehicle_status.py
   ```

2. **`import_bottlenecks.py`**
   - Importa bottlenecks desde HDFS a MongoDB
   - Ejecutar después de `network_analysis.py`:
   ```bash
   spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 storage/mongodb/import_bottlenecks.py
   ```

## Troubleshooting

**Problema:** El consumidor no muestra mensajes de inserción
- **Causa:** No hay datos en el topic `alerts`
- **Solución:** Ejecuta `delay_analysis.py` para generar agregados

**Problema:** Error "NoBrokersAvailable"
- **Causa:** Kafka no está ejecutándose
- **Solución:** `jps | grep Kafka` y arranca Kafka si falta

**Problema:** Error "ConnectionFailure" en MongoDB
- **Causa:** MongoDB no está ejecutándose
- **Solución:** Verifica con `sudo systemctl status mongodb` o `docker ps | grep mongo`

**Problema:** Datos duplicados en MongoDB
- **Causa:** El script usa `upsert` con `route_id + window_start` como clave única, pero puede haber timestamps ligeramente diferentes
- **Solución:** Normalmente no debería pasar, pero si ocurre, puedes limpiar duplicados con:
  ```javascript
  db.route_delay_aggregates.aggregate([
    { $group: { _id: { route_id: "$route_id", window_start: "$window_start" }, dups: { $push: "$_id" }, count: { $sum: 1 } } },
    { $match: { count: { $gt: 1 } } }
  ])
  ```
