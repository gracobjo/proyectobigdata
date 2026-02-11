# Enriquecimiento de Datos – Documentación

Documentación del paso de **enriquecimiento** del pipeline: para qué sirve el script, qué hace, cómo ejecutarlo y cómo interpretar las salidas.

---

## 1. Para qué sirve este script

El script de enriquecimiento (**`data_enrichment.py`**, ejecutado vía **`06_data_enrichment.sh`**) sirve para:

1. **Unir datos en tiempo real** (eventos de vehículos ya limpios) con **datos maestros** (rutas y vehículos) almacenados en HDFS.
2. **Añadir contexto** a cada evento: nombre de ruta, origen/destino, tipo de vehículo, empresa, etc.
3. **Calcular campos derivados** como un indicador de retraso (`is_delayed`) y el momento de enriquecimiento (`enriched_at`).
4. **Escribir el resultado en HDFS** en formato Parquet, particionado por ruta y fecha, para análisis posterior (reporting, ML, consultas SQL).

Sin este paso tendrías solo `vehicle_id`, `route_id`, coordenadas y velocidad; con él tienes también nombres de rutas, ciudades, tipo de vehículo y empresa, lo que permite análisis por ruta, por empresa o por tipo de flota.

---

## 2. Qué script se usa

| Elemento | Valor |
|----------|--------|
| **Script Python** | `processing/spark/sql/data_enrichment.py` |
| **Script de ejecución** | `scripts/run/06_data_enrichment.sh` |
| **Nombre de la aplicación Spark** | `DataEnrichment` |

---

## 3. Qué hace el script (lógica interna)

### Entradas

- **Kafka, topic `filtered-data`:** stream de eventos ya limpios (salida de `data_cleaning.py`). Cada mensaje tiene: `vehicle_id`, `timestamp`, `latitude`, `longitude`, `speed`, `route_id`, `status`, `cleaned_at`.
- **HDFS, tablas maestras:**
  - `master_routes`: `route_id`, `route_name`, `origin_city`, `destination_city`, `distance_km`, `estimated_time_minutes`, etc.
  - `master_vehicles`: `vehicle_id`, `vehicle_type`, `capacity`, `company`, `registration_date`, etc.

### Proceso

1. **Leer el stream** de Kafka `filtered-data` y parsear el JSON con un esquema fijo.
2. **Cargar las tablas maestras** desde HDFS (Parquet) con esquemas explícitos.
3. **Hacer JOIN** del stream con `master_routes` por `route_id` y con `master_vehicles` por `vehicle_id` (LEFT JOIN para no perder eventos si falta dato maestro).
4. **Añadir columnas derivadas:**
   - `is_delayed`: indicador booleano (usa velocidad y tiempo estimado).
   - `enriched_at`: timestamp de cuándo se enriqueció el registro.
   - `partition_date`: fecha del evento (`to_date(timestamp)`) para particionado.
5. **Escribir en HDFS** con Spark Structured Streaming:
   - Formato: Parquet.
   - Ruta base: `hdfs://localhost:9000/user/hadoop/processed/enriched`.
   - Particiones: `route_id` y `partition_date`.
   - Checkpoint: `hdfs://localhost:9000/user/hadoop/checkpoints/enrichment`.
   - Trigger: cada 10 segundos; modo append.

### Salidas

- **HDFS:** directorio `processed/enriched` con carpetas por `route_id` y `partition_date` y ficheros Parquet dentro.
- **Checkpoint:** en `checkpoints/enrichment` para poder reanudar el streaming sin duplicar o perder datos.

---

## 4. Cómo ejecutarlo

### Requisitos previos

- HDFS y Kafka en marcha.
- Tablas maestras creadas en HDFS (`create_tables_spark.py` o `fix_master_vehicles.py`).
- Job de limpieza (`data_cleaning.py`) escribiendo en `filtered-data` (para que haya datos que enriquecer).

### Comando

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
bash scripts/run/06_data_enrichment.sh
```

O directamente con `spark-submit`:

```bash
spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_enrichment.py
```

El job se deja corriendo; cuando no hay datos nuevos verás mensajes como *"Streaming query has been idle and waiting for new data"* (comportamiento normal).

---

## 5. Ejemplo de salida en HDFS y explicación

### 5.1 Listar la raíz del directorio de enriquecimiento

Comando:

```bash
hdfs dfs -ls /user/hadoop/processed/enriched/
```

Ejemplo de salida:

```
Found 8 items
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 22:43 /user/hadoop/processed/enriched/_spark_metadata
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R001
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R002
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R003
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R004
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R005
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R006
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R007
```

Explicación de cada parte:

| Salida | Explicación |
|--------|-------------|
| `Found 8 items` | Hay 8 entradas en ese directorio (1 de metadatos + 7 particiones de ruta). |
| `_spark_metadata` | Carpeta que usa Spark Structured Streaming para guardar metadatos (por ejemplo, qué lotes se han escrito). No contiene datos de negocio. |
| `route_id=R001` … `route_id=R007` | Particiones por **ruta**. Cada carpeta agrupa todos los eventos enriquecidos de esa ruta. Coinciden con las rutas que existen en `master_routes` y para las que ha pasado al menos un evento por el job. |
| `hadoop supergroup` | Propietario y grupo en HDFS (habitual en entorno Hadoop). |
| Fechas (22:43, 01:08) | Momento de creación o última modificación de esos directorios en HDFS. |

En conjunto, esta salida indica que el script está escribiendo correctamente y que hay datos enriquecidos para las rutas R001–R007.

### 5.2 Ver particiones por fecha dentro de una ruta

Comando (ejemplo para R001):

```bash
hdfs dfs -ls /user/hadoop/processed/enriched/route_id=R001/
```

Ejemplo de salida:

```
Found 2 items
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-10
drwxr-xr-x   - hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-11
```

Explicación:

| Salida | Explicación |
|--------|-------------|
| `partition_date=2026-02-10`, `partition_date=2026-02-11` | Segunda partición: por **fecha** del evento. Dentro de cada una están los Parquet de ese día y esa ruta. Así se pueden hacer consultas por ruta y por día sin leer todo el dataset. |

### 5.3 Ver ficheros Parquet escritos

Comando (ejemplo para R001 y 2026-02-11):

```bash
hdfs dfs -ls /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-11/
```

Ejemplo de salida:

```
Found 3 items
-rw-r--r--   1 hadoop supergroup          0 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-11/_SUCCESS
-rw-r--r--   1 hadoop supergroup       1234 2026-02-11 01:07 /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-11/part-00000-xxx.snappy.parquet
-rw-r--r--   1 hadoop supergroup       2567 2026-02-11 01:08 /user/hadoop/processed/enriched/route_id=R001/partition_date=2026-02-11/part-00001-yyy.snappy.parquet
```

Explicación:

| Salida | Explicación |
|--------|-------------|
| `_SUCCESS` | Fichero vacío que Spark escribe cuando un lote se escribe correctamente. Sirve para comprobar que el job no falló en esa partición. |
| `part-00000-xxx.snappy.parquet` | Fragmento de datos en formato Parquet comprimido con Snappy. Cada `part-*` es una parte del resultado del job para esa ruta y fecha. Los nombres incluyen identificadores de escritura. |

---

## 6. Resumen: para qué sirve y qué estás viendo

- **Para qué sirve el script:** enriquecer en tiempo real los eventos limpios de Kafka con datos maestros de rutas y vehículos, y dejar el resultado en HDFS listo para análisis.
- **Qué estás viendo en `hdfs dfs -ls /user/hadoop/processed/enriched/`:**
  - `_spark_metadata`: control del streaming.
  - `route_id=R001` … `route_id=R007`: datos enriquecidos particionados por ruta.
  - Dentro de cada ruta, `partition_date=YYYY-MM-DD` y dentro de eso, ficheros `.parquet` (y `_SUCCESS`) que son la salida real del script.

Con esto queda documentada la utilidad del enriquecimiento hasta aquí, con ejemplos de salida y explicación del script que se usa.
