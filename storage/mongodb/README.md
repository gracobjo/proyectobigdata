# Persistencia MongoDB

Scripts para escribir datos del pipeline en MongoDB (NoSQL) para consultas de baja latencia.

## Colecciones

- **route_delay_aggregates**: Agregados de retrasos por ventana y ruta (desde topic `alerts`)
- **vehicle_status**: Último estado conocido de cada vehículo (desde topic `filtered-data`)
- **bottlenecks**: Cuellos de botella detectados por análisis de grafos (desde HDFS)

## Requisitos

1. **MongoDB ejecutándose** en `127.0.0.1:27017`:
   ```bash
   # Verificar
   sudo systemctl status mongodb
   # o
   docker ps | grep mongo
   ```

2. **Dependencias Python** (en el venv):
   ```bash
   source venv/bin/activate
   pip install pymongo
   ```

3. **Kafka con datos** (para los consumidores):
   - Topic `alerts` con agregados (generado por `delay_analysis.py`)
   - Topic `filtered-data` con datos limpios (generado por `data_cleaning.py`)

## Scripts

### 1. kafka_to_mongodb_alerts.py

Consume agregados de retrasos desde `alerts` y los escribe en `route_delay_aggregates`.

**Uso:**
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python storage/mongodb/kafka_to_mongodb_alerts.py
```

**Qué hace:**
- Lee mensajes JSON del topic `alerts`
- Convierte timestamps ISO a datetime de MongoDB
- Inserta/actualiza documentos en `route_delay_aggregates` (clave única: route_id + window_start)
- Crea índices automáticamente

**Ejemplo de documento insertado:**
```json
{
  "route_id": "R004",
  "window_start": ISODate("2026-02-11T00:00:00Z"),
  "window_end": ISODate("2026-02-11T00:15:00Z"),
  "total_vehicles": 22,
  "avg_speed": 18.39,
  "delayed_count": 17,
  "delay_percentage": 77.27,
  "max_speed": 90.49,
  "min_speed": 0.0,
  "analysis_timestamp": ISODate("2026-02-11T01:43:36Z")
}
```

---

### 2. kafka_to_mongodb_vehicle_status.py

Mantiene el último estado conocido de cada vehículo desde `filtered-data`.

**Uso:**
```bash
source venv/bin/activate
python storage/mongodb/kafka_to_mongodb_vehicle_status.py
```

**Qué hace:**
- Lee mensajes del topic `filtered-data`
- Calcula `is_delayed` heurísticamente (speed < 10) si no está
- Inserta documentos en `vehicle_status` (mantiene histórico completo)
- Opcionalmente enriquece con datos maestros si existen en MongoDB

**Nota:** Por defecto inserta todos los mensajes (histórico completo). Para mantener solo el último estado, descomenta las líneas de `update_one` en el script.

---

### 3. import_bottlenecks.py

Importa resultados de análisis de grafos desde HDFS a MongoDB.

**Uso:**
```bash
spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 storage/mongodb/import_bottlenecks.py
```

**Qué hace:**
- Lee Parquet de `network_bottlenecks` desde HDFS
- Convierte a documentos MongoDB
- Limpia la colección y reinserta los datos

**Ejecutar después de:** `network_analysis.py` (análisis de grafos)

---

## Consultas de ejemplo

Conectar a MongoDB:
```bash
mongosh "mongodb://127.0.0.1:27017/transport_db"
```

### Consultar agregados de retrasos

```javascript
// Últimos agregados de la ruta R004
db.route_delay_aggregates.find({ route_id: "R004" }).sort({ window_start: -1 }).limit(5)

// Rutas con mayor porcentaje de retraso en la última hora
db.route_delay_aggregates.find({
  window_start: { $gte: new Date(Date.now() - 3600000) }
}).sort({ delay_percentage: -1 }).limit(10)

// Promedio de retraso por ruta
db.route_delay_aggregates.aggregate([
  { $group: { _id: "$route_id", avg_delay: { $avg: "$delay_percentage" } } },
  { $sort: { avg_delay: -1 } }
])
```

### Consultar estado de vehículos

```javascript
// Último estado conocido del vehículo V001
db.vehicle_status.find({ vehicle_id: "V001" }).sort({ timestamp: -1 }).limit(1)

// Vehículos en retraso actualmente
db.vehicle_status.find({ is_delayed: true }).sort({ timestamp: -1 })

// Vehículos en una ruta específica
db.vehicle_status.find({ route_id: "R004" }).sort({ timestamp: -1 })
```

### Consultar bottlenecks

```javascript
// Todos los bottlenecks
db.bottlenecks.find().sort({ degree: -1 })

// Nodos con grado >= 3
db.bottlenecks.find({ degree: { $gte: 3 } })
```

---

## Orden de ejecución recomendado

1. **MongoDB en marcha** (`sudo systemctl start mongodb` o `docker start mongodb`)
2. **Pipeline Spark corriendo:**
   - `data_cleaning.py` → escribe en `filtered-data`
   - `delay_analysis.py` → escribe en `alerts`
   - `network_analysis.py` → escribe bottlenecks en HDFS
3. **Consumidores MongoDB:**
   - `kafka_to_mongodb_alerts.py` (en una terminal)
   - `kafka_to_mongodb_vehicle_status.py` (en otra terminal, opcional)
4. **Importar bottlenecks:**
   - `import_bottlenecks.py` (una vez, después de análisis de grafos)

---

## Troubleshooting

**Error: "NoBrokersAvailable"**
- Kafka no está ejecutándose: `jps | grep Kafka`

**Error: "ConnectionFailure"**
- MongoDB no está ejecutándose: `sudo systemctl status mongodb` o `docker ps | grep mongo`

**No hay mensajes en alerts**
- Ejecuta `delay_analysis.py` primero para generar agregados

**Duplicados en route_delay_aggregates**
- El script usa `upsert` con route_id + window_start como clave única; debería evitar duplicados. Si aparecen, puede ser por timestamps ligeramente diferentes (redondeo).
