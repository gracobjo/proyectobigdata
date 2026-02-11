# API Reference

## Endpoints de Consulta

### Hive Queries

#### Consultar retrasos por ruta
```sql
SELECT * FROM delay_aggregates 
WHERE route_id = 'R001' 
AND DATE(window_start) = CURRENT_DATE();
```

#### Consultar estado de red
```sql
SELECT * FROM network_pagerank 
ORDER BY pagerank DESC;
```

### MongoDB Queries

#### Obtener último estado de un vehículo
```javascript
// En mongosh
use transport_db;
db.vehicle_status.find(
  { vehicle_id: "V001" },
  {}
).sort({ timestamp: -1 }).limit(1);
```

#### Obtener vehículos por ruta
```javascript
use transport_db;
db.vehicle_status.find(
  { route_id: "R001" },
  { vehicle_id: 1, timestamp: 1, status: 1, speed: 1, _id: 0 }
).limit(10);
```

### Kafka Topics

#### Consumir datos crudos
```bash
kafka-console-consumer.sh \
  --bootstrap-server nodo1:9092 \
  --topic raw-data \
  --from-beginning
```

#### Consumir datos filtrados
```bash
kafka-console-consumer.sh \
  --bootstrap-server nodo1:9092 \
  --topic filtered-data \
  --from-beginning
```

## Schemas de Datos

### Raw Data Schema
```json
{
  "vehicle_id": "string",
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "latitude": "double",
  "longitude": "double",
  "speed": "double",
  "route_id": "string",
  "status": "string"
}
```

### Enriched Data Schema
```json
{
  "vehicle_id": "string",
  "timestamp": "timestamp",
  "latitude": "double",
  "longitude": "double",
  "speed": "double",
  "route_id": "string",
  "status": "string",
  "route_name": "string",
  "origin_city": "string",
  "destination_city": "string",
  "distance_km": "double",
  "vehicle_type": "string",
  "company": "string",
  "is_delayed": "boolean"
}
```

### Delay Aggregates Schema
```json
{
  "window_start": "timestamp",
  "window_end": "timestamp",
  "route_id": "string",
  "route_name": "string",
  "total_vehicles": "bigint",
  "avg_speed": "double",
  "delayed_count": "bigint",
  "delay_percentage": "double",
  "max_speed": "double",
  "min_speed": "double"
}
```
