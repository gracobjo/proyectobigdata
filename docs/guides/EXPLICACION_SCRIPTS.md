# Explicación de los Scripts del Pipeline

Documentación detallada de qué hace cada script ejecutado en los terminales del pipeline.

---

## 📋 Índice

1. [Scripts de Preparación](#scripts-de-preparación)
2. [Scripts del Pipeline Principal](#scripts-del-pipeline-principal)
3. [Terminal 6: Enriquecimiento](#terminal-6-enriquecimiento-de-datos-06_data_enrichmentsh)
4. [Scripts de Persistencia](#scripts-de-persistencia)
5. [Scripts de Verificación](#scripts-de-verificación)

---

## 🔧 Scripts de Preparación

### `00_start_hdfs.sh`

**Ubicación:** `scripts/run/00_start_hdfs.sh`

**Qué hace:**
- Arranca los servicios de HDFS necesarios para el pipeline
- Inicia el NameNode (gestor del sistema de archivos distribuido)
- Inicia el DataNode (almacenamiento de datos)
- Sale del modo seguro de HDFS para permitir operaciones

**Por qué es necesario:**
- HDFS es el sistema de almacenamiento donde Spark guarda:
  - Checkpoints (para recuperación ante fallos)
  - Resultados procesados (tablas Parquet)
  - Datos maestros (rutas, vehículos)
- Sin HDFS corriendo, los scripts de Spark fallan con "Connection refused"

**Cuándo ejecutarlo:**
- **Siempre primero**, antes de ejecutar cualquier script de Spark
- Solo una vez al inicio de la sesión

**Comando:**
```bash
bash scripts/run/00_start_hdfs.sh
```

---

### `01_generate_data.sh`

**Ubicación:** `scripts/run/01_generate_data.sh`

**Qué hace:**
- Genera datos de prueba simulando eventos de transporte
- Crea mensajes JSON con información de vehículos:
  - ID del vehículo
  - Timestamp (fecha y hora)
  - Coordenadas GPS (latitud, longitud)
  - Velocidad
  - ID de ruta
  - Estado (IN_TRANSIT, LOADING, MAINTENANCE, etc.)
- Envía estos mensajes al topic `raw-data` de Kafka

**Por qué es necesario:**
- El pipeline necesita datos de entrada para procesar
- Simula datos reales de sensores GPS en vehículos
- Permite probar el pipeline completo sin datos reales

**Cuándo ejecutarlo:**
- Al inicio, antes de ejecutar el pipeline
- Puede ejecutarse múltiples veces para generar más datos
- Opcional: puede omitirse si ya hay datos en `raw-data`

**Comando:**
```bash
bash scripts/run/01_generate_data.sh
```

**Ejemplo de datos generados:**
```json
{
  "vehicle_id": "V001",
  "timestamp": "2026-02-11 16:30:00",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "speed": 45.5,
  "route_id": "R001",
  "status": "IN_TRANSIT"
}
```

---

## 🔄 Scripts del Pipeline Principal

### `02_data_cleaning.sh` (Terminal 2)

**Ubicación:** `scripts/run/02_data_cleaning.sh`  
**Script Python:** `processing/spark/sql/data_cleaning.py`

**Qué hace:**
1. **Lee datos desde Kafka** (`raw-data` topic)
   - Consume mensajes JSON en tiempo real usando Spark Structured Streaming
   - Procesa datos en micro-batches cada 10 segundos

2. **Limpia y valida los datos:**
   - Normaliza formatos (trim, uppercase)
   - Valida coordenadas GPS (latitud entre -90 y 90, longitud entre -180 y 180)
   - Valida velocidad (no negativa, no excesiva)
   - Maneja valores nulos
   - Convierte timestamps a formato estándar

3. **Elimina duplicados:**
   - Usa `dropDuplicates` basado en `vehicle_id` + `timestamp`
   - Evita procesar el mismo evento múltiples veces

4. **Añade metadatos:**
   - Campo `cleaned_at`: timestamp de cuándo se limpió el dato
   - Mantiene todos los campos originales válidos

5. **Escribe resultados:**
   - En Kafka topic `filtered-data` (datos limpios para siguiente etapa)
   - Guarda checkpoint en HDFS para recuperación

**Por qué es necesario:**
- Los datos en `raw-data` pueden tener errores, duplicados o formatos inconsistentes
- Esta etapa asegura calidad de datos antes del análisis
- Es el primer paso del procesamiento en el pipeline

**Cuándo ejecutarlo:**
- Después de generar datos (`01_generate_data.sh`)
- Debe estar corriendo continuamente mientras hay datos para procesar
- Se ejecuta en **Terminal 2**

**Comando:**
```bash
bash scripts/run/02_data_cleaning.sh
```

**Salidas:**
- **Kafka:** Topic `filtered-data` con datos limpios
- **HDFS:** Checkpoint en `/user/hadoop/checkpoints/cleaning/`

**Ejemplo de datos de salida:**
```json
{
  "vehicle_id": "V001",
  "timestamp": "2026-02-11T16:30:00.000+01:00",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "speed": 45.5,
  "route_id": "R001",
  "status": "IN_TRANSIT",
  "cleaned_at": "2026-02-11T17:04:30.038+01:00"
}
```

---

### `03_delay_analysis.sh` (Terminal 3)

**Ubicación:** `scripts/run/03_delay_analysis.sh`  
**Script Python:** `processing/spark/streaming/delay_analysis.py`

**Qué hace:**
1. **Lee datos limpios desde Kafka** (`filtered-data` topic)
   - Consume datos ya validados y normalizados
   - Procesa en micro-batches cada 10 segundos

2. **Calcula retrasos:**
   - Determina si un vehículo está en retraso usando heurística:
     - `is_delayed = True` si velocidad < 10 km/h
     - `is_delayed = False` si velocidad >= 10 km/h
   - Esta es una aproximación simple (en producción usaría tiempos estimados vs reales)

3. **Agrupa por ventanas de tiempo:**
   - Crea ventanas de **15 minutos** usando `window` function
   - Agrupa por `route_id` y ventana de tiempo
   - Calcula agregados para cada ventana:
     - `total_vehicles`: número de vehículos en esa ventana/ruta
     - `avg_speed`: velocidad media
     - `delayed_count`: número de vehículos en retraso
     - `delay_percentage`: porcentaje de vehículos en retraso
     - `max_speed`, `min_speed`: velocidades máxima y mínima

4. **Escribe resultados en múltiples destinos:**
   - **Kafka topic `alerts`:** Agregados en formato JSON para servicios externos
   - **HDFS Parquet:** Tabla `delay_aggregates` particionada por `route_id`
   - **Consola:** Para debugging y monitoreo

**Por qué es necesario:**
- Proporciona métricas agregadas de retrasos por ruta y tiempo
- Permite identificar rutas problemáticas
- Genera alertas en tiempo real para sistemas externos
- Almacena resultados históricos en HDFS para análisis posterior

**Cuándo ejecutarlo:**
- Después de que `data_cleaning.py` haya procesado algunos datos
- Debe estar corriendo continuamente
- Se ejecuta en **Terminal 3**

**Comando:**
```bash
bash scripts/run/03_delay_analysis.sh
```

**Salidas:**
- **Kafka:** Topic `alerts` con agregados JSON
- **HDFS:** Tabla `delay_aggregates` en `/user/hive/warehouse/delay_aggregates/`
- **Consola:** Logs de cada batch procesado

**Ejemplo de mensaje en `alerts`:**
```json
{
  "window_start": "2026-02-11T16:45:00.000+01:00",
  "window_end": "2026-02-11T17:00:00.000+01:00",
  "route_id": "R003",
  "total_vehicles": 3,
  "avg_speed": 8.5,
  "delayed_count": 2,
  "delay_percentage": 66.7,
  "max_speed": 15.2,
  "min_speed": 0.0,
  "analysis_timestamp": "2026-02-11T17:05:30.089+01:00"
}
```

**Interpretación:**
- En la ventana 16:45-17:00, ruta R003
- 3 vehículos registrados
- Velocidad media: 8.5 km/h (muy baja)
- 2 de 3 vehículos en retraso (66.7%)
- Indica posible problema en esa ruta

---

## 💾 Scripts de Persistencia

### `04_mongodb_consumer.sh` (Terminal 4)

**Ubicación:** `scripts/run/04_mongodb_consumer.sh`  
**Script Python:** `storage/mongodb/kafka_to_mongodb_alerts.py`

**Qué hace:**
1. **Conecta a Kafka y MongoDB:**
   - Se conecta al topic `alerts` de Kafka
   - Se conecta a MongoDB en `127.0.0.1:27017`
   - Usa base de datos `transport_db`

2. **Consume mensajes del topic `alerts`:**
   - Lee agregados de retrasos generados por `delay_analysis.py`
   - Procesa mensajes JSON en tiempo real

3. **Parsea y transforma datos:**
   - Convierte timestamps ISO a objetos `datetime` de MongoDB
   - Valida estructura de los mensajes

4. **Inserta/actualiza en MongoDB:**
   - Colección: `route_delay_aggregates`
   - Usa `upsert` (inserta si no existe, actualiza si existe)
   - Clave única: `route_id` + `window_start`
   - Crea índices automáticamente para consultas rápidas

5. **Muestra progreso:**
   - Imprime cada documento insertado/actualizado
   - Muestra estadísticas: ruta, ventana, vehículos, porcentaje de retraso

**Por qué es necesario:**
- MongoDB permite consultas rápidas de agregados de retrasos
- Ideal para dashboards y aplicaciones web
- Complementa el almacenamiento en HDFS (más lento pero más escalable)
- Permite alertas en tiempo real

**Cuándo ejecutarlo:**
- Después de que `delay_analysis.py` haya generado algunos alerts
- Debe estar corriendo continuamente para procesar nuevos alerts
- Se ejecuta en **Terminal 4**

**Comando:**
```bash
bash scripts/run/04_mongodb_consumer.sh
```

**Salidas:**
- **MongoDB:** Colección `route_delay_aggregates` con documentos JSON
- **Consola:** Mensajes de inserción/actualización

**Ejemplo de salida en consola:**
```
✓ Insertado: R003 @ 2026-02-11 17:00:00+01:00 (2 vehículos, 100.0% retraso)
✓ Insertado: R002 @ 2026-02-11 16:45:00+01:00 (4 vehículos, 100.0% retraso)
↻ Actualizado: R003 @ 2026-02-11 16:45:00+01:00
```

**Estructura del documento en MongoDB:**
```json
{
  "_id": ObjectId("..."),
  "route_id": "R003",
  "window_start": ISODate("2026-02-11T17:00:00.000Z"),
  "window_end": ISODate("2026-02-11T17:15:00.000Z"),
  "total_vehicles": 2,
  "avg_speed": 5.2,
  "delayed_count": 2,
  "delay_percentage": 100.0,
  "max_speed": 8.1,
  "min_speed": 0.0,
  "analysis_timestamp": ISODate("2026-02-11T17:05:30.089Z")
}
```

---

## ✅ Scripts de Verificación

### `05_verify_mongodb.sh`

**Ubicación:** `scripts/run/05_verify_mongodb.sh`  
**Script Python:** `storage/mongodb/verify_data.py`

**Qué hace:**
1. **Conecta a MongoDB:**
   - Se conecta a `transport_db` en MongoDB
   - Verifica las tres colecciones principales

2. **Cuenta documentos:**
   - `route_delay_aggregates`: Agregados de retrasos
   - `vehicle_status`: Estado de vehículos (si existe)
   - `bottlenecks`: Cuellos de botella (si existe)

3. **Muestra estadísticas:**
   - Últimos documentos insertados
   - Promedio de retraso por ruta
   - Número de ventanas procesadas por ruta

4. **Ordena resultados:**
   - Por porcentaje de retraso (descendente)
   - Por fecha (más recientes primero)

**Por qué es necesario:**
- Permite verificar que el pipeline está funcionando
- Muestra estadísticas útiles para análisis
- Útil para debugging y monitoreo

**Cuándo ejecutarlo:**
- En cualquier momento para verificar el estado
- Puede ejecutarse múltiples veces
- No necesita estar corriendo continuamente

**Comando:**
```bash
bash scripts/run/05_verify_mongodb.sh
```

**Características de la salida (qué significa cada número, últimos 5, promedios, vehículos en retraso, bottlenecks):** Ver **docs/guides/VERIFICACION_MONGODB_CARACTERISTICAS.md**.

**Ejemplo de salida:**
```
=== Verificación de datos en MongoDB ===

📊 route_delay_aggregates: 26 documentos

Últimos 5 documentos:
  - Ruta: R006, Ventana: 2026-02-11 16:00:00, Retraso: 100.0%, Vehículos: 1
  - Ruta: R005, Ventana: 2026-02-11 16:00:00, Retraso: 100.0%, Vehículos: 1
  ...

Promedio de retraso por ruta:
  - R002: 100.0% (ventanas: 1)
  - R004: 100.0% (ventanas: 4)
  - R003: 91.7% (ventanas: 4)
  ...
```

---

## 🔄 Flujo Completo del Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    PREPARACIÓN                               │
└─────────────────────────────────────────────────────────────┘
         │
         ├─ 00_start_hdfs.sh → Arranca HDFS
         │
         └─ 01_generate_data.sh → Genera datos de prueba
                                  ↓
                            raw-data (Kafka)
         │
┌─────────────────────────────────────────────────────────────┐
│              PROCESAMIENTO (Streaming)                      │
└─────────────────────────────────────────────────────────────┘
         │
         ├─ Terminal 2: 02_data_cleaning.sh
         │   ↓ Lee raw-data
         │   ↓ Limpia y valida
         │   ↓ Escribe filtered-data (Kafka)
         │
         ├─ Terminal 3: 03_delay_analysis.sh
         │   ↓ Lee filtered-data
         │   ↓ Calcula agregados (ventanas 15 min)
         │   ↓ Escribe alerts (Kafka) + HDFS
         │
┌─────────────────────────────────────────────────────────────┐
│                    PERSISTENCIA                             │
└─────────────────────────────────────────────────────────────┘
         │
         └─ Terminal 4: 04_mongodb_consumer.sh
             ↓ Lee alerts (Kafka)
             ↓ Inserta en MongoDB
             ↓ route_delay_aggregates
         │
┌─────────────────────────────────────────────────────────────┐
│                  VERIFICACIÓN                               │
└─────────────────────────────────────────────────────────────┘
         │
         └─ 05_verify_mongodb.sh → Muestra estadísticas
```

---

### Terminal 6: Enriquecimiento de datos (`06_data_enrichment.sh`)

**Script Python:** `processing/spark/sql/data_enrichment.py`

**Qué hace:** Lee el stream de `filtered-data` (Kafka), lo cruza con las tablas maestras `master_routes` y `master_vehicles` (HDFS), añade campos derivados (`is_delayed`, `enriched_at`) y escribe el resultado en HDFS en formato Parquet, particionado por `route_id` y `partition_date`.

**Para qué sirve:** Tener eventos de transporte enriquecidos con nombre de ruta, origen/destino, tipo de vehículo y empresa, listos para análisis o reporting en HDFS.

**Salida en HDFS:** `hdfs://localhost:9000/user/hadoop/processed/enriched/` con carpetas `route_id=R001`, `route_id=R002`, etc., y dentro `partition_date=YYYY-MM-DD` con ficheros `.parquet`.

**Documentación detallada** (ejemplos de salida, explicación de cada elemento, comandos de verificación): **docs/guides/ENRIQUECIMIENTO_DATOS.md**.

---

## 📊 Resumen por Terminal

| Terminal | Script | Qué Hace | Entrada | Salida |
|----------|--------|----------|---------|--------|
| **0** | `00_start_hdfs.sh` | Arranca HDFS | - | HDFS activo |
| **1** | `01_generate_data.sh` | Genera datos | - | `raw-data` (Kafka) |
| **2** | `02_data_cleaning.sh` | Limpia datos | `raw-data` | `filtered-data` (Kafka) |
| **3** | `03_delay_analysis.sh` | Analiza retrasos | `filtered-data` | `alerts` (Kafka) + HDFS |
| **4** | `04_mongodb_consumer.sh` | Persiste en MongoDB | `alerts` | MongoDB |
| **5** | `05_verify_mongodb.sh` | Verifica datos | MongoDB | Estadísticas (consola) |
| **6** | `06_data_enrichment.sh` | Enriquecimiento (stream + maestros) | `filtered-data` + HDFS master_* | HDFS `processed/enriched` |

---

## 🎯 Conceptos Clave

### Spark Structured Streaming
- Procesa datos en tiempo real usando micro-batches
- Permite recuperación ante fallos mediante checkpoints
- Procesa datos cada 10 segundos (configurable)

### Ventanas de Tiempo (Windows)
- Agrupa eventos por intervalos de tiempo (15 minutos)
- Permite análisis temporal de tendencias
- Útil para detectar patrones en el tiempo

### Checkpoints
- Guardan el estado del procesamiento en HDFS
- Permiten recuperar desde el último punto procesado
- Evitan perder datos ante fallos

### Upsert en MongoDB
- Inserta si no existe, actualiza si existe
- Evita duplicados usando clave única
- Mantiene datos actualizados automáticamente

---

## 📝 Notas Importantes

1. **Orden de ejecución:** Los scripts deben ejecutarse en orden (0 → 1 → 2 → 3 → 4)
2. **Tiempo de espera:** Entre cada terminal, esperar ~30 segundos para que procese datos
3. **Ejecución continua:** Terminales 2, 3 y 4 deben seguir corriendo
4. **HDFS primero:** Siempre arrancar HDFS antes de ejecutar scripts de Spark
5. **Datos persistentes:** Los datos en Kafka y HDFS persisten aunque los scripts se detengan

---

## 🔍 Troubleshooting

**Si un script falla:**
1. Verificar que HDFS está corriendo (`jps | grep NameNode`)
2. Verificar que Kafka está corriendo (`jps | grep Kafka`)
3. Verificar que MongoDB está corriendo (`pgrep mongod`)
4. Revisar logs del script para ver el error específico

**Si no hay datos:**
1. Verificar que hay datos en el topic anterior (`raw-data` → `filtered-data` → `alerts`)
2. Esperar unos segundos (los batches se procesan cada 10 segundos)
3. Generar más datos si es necesario (`01_generate_data.sh`)
