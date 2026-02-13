# Hive en el proyecto y estructura de carpetas

Este documento aclara **qué papel tiene Hive** en la arquitectura y **por qué algunas carpetas del proyecto están vacías o solo tienen documentación**, aunque el sistema esté integrado.

---

## 1. Qué hacemos con Hive

### Papel de Hive en la arquitectura

En este proyecto **Apache Hive** se usa para:

| Uso | Descripción |
|-----|-------------|
| **Metastore** | Guarda el catálogo de tablas (nombres, esquemas, ubicación en HDFS). Así puedes consultar con SQL los mismos datos que Spark escribe en HDFS. |
| **Consultas SQL** | Una vez el metastore está levantado y las tablas creadas/registradas, puedes usar `hive` o Beeline para hacer `SELECT * FROM delay_aggregates`, etc. |
| **Reporting** | El script **`storage/hive/daily_report.sql`** contiene consultas de reporte (retrasos por ruta, top rutas con retrasos, nodos críticos, cuellos de botella). Se ejecutan en Hive sobre las tablas que Spark ha escrito. |

### Dónde están realmente los datos

Spark escribe en **HDFS** en rutas que siguen el convenio del warehouse de Hive:

- `hdfs://.../user/hive/warehouse/master_routes/`, `master_vehicles/` (datos maestros)
- `hdfs://.../user/hive/warehouse/delay_aggregates/` (agregados de retrasos)
- `hdfs://.../user/hive/warehouse/network_pagerank/`, `network_bottlenecks/`, etc. (análisis de grafos)

**No hace falta tener Hive en marcha** para que el pipeline funcione: Spark escribe en esas rutas igualmente. Hive solo añade:

1. Poder consultar esas mismas rutas con SQL (`hive -e "SHOW TABLES;"`).
2. Poder ejecutar **`storage/hive/daily_report.sql`** para reportes diarios.

### Resumen

- **Pipeline (NiFi → Kafka → Spark → HDFS/MongoDB):** funciona sin Hive; solo hace falta HDFS y YARN.
- **Consultas SQL y reportes sobre los datos de HDFS:** sí requieren Hive (metastore + tablas creadas/registradas). Por eso en **scripts/stack/start_stack.sh** se arranca el metastore de Hive: para tener la pila completa y poder usar Hive cuando quieras.

---

## 2. Carpetas del proyecto: por qué algunas están “vacías”

La integración del pipeline **no implica que todas las carpetas del repo tengan ficheros de datos**. Parte de los datos viven en **HDFS**, **Kafka** o **MongoDB**, no en el árbol de carpetas del proyecto. Esta tabla aclara cada caso:

| Carpeta | Contenido | ¿Por qué está así? |
|---------|-----------|---------------------|
| **data/gps_logs/** | Solo `README.md` (o ficheros `.jsonl` que tú generes) | Los datos se **generan en ejecución** con `scripts/utils/generate_gps_log_file.py`. El repo no incluye datos de prueba; es intencionado. |
| **data/master/** | `sample_master_data.sql` | **Datos maestros en formato SQL** para cargar en Hive/HDFS (rutas, vehículos). No son “carpeta vacía”. |
| **storage/cassandra/** | `schema.cql` | **No es Cassandra.** Ese fichero es el **diseño lógico de las colecciones de MongoDB** (vehicle_status, route_delay_aggregates, etc.). El nombre de la carpeta es histórico; el proyecto usa **MongoDB**. |
| **storage/hive/** | `daily_report.sql` | **Scripts de reportes SQL** para ejecutar en Hive. Los datos están en HDFS (warehouse), no en esta carpeta. |
| **storage/mongodb/** | Scripts Python (consumers, import, verify) | Aquí están los **programas** que escriben/leen MongoDB. Los datos están en el **servidor MongoDB**, no en el repo. |
| **config/cassandra/** | `cassandra.yaml` | Configuración de **Cassandra**, que **no se usa** en el pipeline actual. Opcional; se puede ignorar o eliminar si solo usas MongoDB. |

### Dónde están los datos “en bruto” y procesados

- **En el repositorio:** solo definiciones (SQL, esquemas, configs) y scripts. No se versionan datos grandes.
- **En HDFS:** `/user/hadoop/raw`, `/user/hadoop/processed/enriched`, `/user/hive/warehouse/...` (creados por Spark y scripts de setup).
- **En Kafka:** topics `raw-data`, `filtered-data`, `alerts` (datos en tránsito).
- **En MongoDB:** bases y colecciones (vehicle_status, route_delay_aggregates, bottlenecks, etc.).

Por tanto, **carpetas “sin datos” en el árbol del proyecto** son coherentes con una integración donde los datos viven en HDFS, Kafka y MongoDB.

---

## 3. Qué puedes hacer en la práctica

- **Hive:**  
  - Arrancarlo con el resto de la pila (`scripts/stack/start_stack.sh`).  
  - Crear tablas maestros desde `data/master/sample_master_data.sql` (ver GETTING_STARTED).  
  - Cuando Spark haya escrito en el warehouse, usar Hive para consultas y para ejecutar **`storage/hive/daily_report.sql`**.

- **Carpetas “vacías” o solo con docs:**  
  - **data/gps_logs:** generar datos con `generate_gps_log_file.py` cuando quieras probar NiFi.  
  - **storage/cassandra:** tratarla como documentación del modelo MongoDB; no hace falta Cassandra instalado.  
  - **config/cassandra:** ignorar si no usas Cassandra.

Si quieres, en el README principal se puede añadir una frase que remita a este documento para “Hive y estructura de carpetas”.
