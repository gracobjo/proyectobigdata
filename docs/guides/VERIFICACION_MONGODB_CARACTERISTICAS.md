# Características de la verificación MongoDB

Documentación del script `verify_data.py` y del significado de cada resultado que muestra.

---

## Cómo ejecutar la verificación

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python storage/mongodb/verify_data.py
```

---

## Ejemplo de salida y significado

A continuación se describe cada bloque de la salida y qué representa.

---

### 1. route_delay_aggregates

**Ejemplo:**
```
📊 route_delay_aggregates: 26 documentos

Últimos 5 documentos:
  - Ruta: R006, Ventana: 2026-02-11 16:00:00, Retraso: 100.0%, Vehículos: 1
  - Ruta: R005, Ventana: 2026-02-11 16:00:00, Retraso: 100.0%, Vehículos: 1
  - Ruta: R003, Ventana: 2026-02-11 16:00:00, Retraso: 100.0%, Vehículos: 2
  - Ruta: R007, Ventana: 2026-02-11 16:00:00, Retraso: 50.0%, Vehículos: 2
  - Ruta: R004, Ventana: 2026-02-11 15:45:00, Retraso: 100.0%, Vehículos: 1

Promedio de retraso por ruta:
  - R002: 100.0% (ventanas: 1)
  - R004: 100.0% (ventanas: 4)
  - R003: 91.7% (ventanas: 4)
  - R001: 87.5% (ventanas: 4)
  - R006: 80.0% (ventanas: 5)
  - R007: 80.0% (ventanas: 5)
  - R005: 66.7% (ventanas: 3)
```

| Elemento | Significado |
|----------|-------------|
| **Número de documentos** | Cantidad de agregados almacenados. Cada documento = una ventana de 15 minutos para una ruta. Proviene del topic Kafka `alerts` (consumidor `kafka_to_mongodb_alerts.py`). |
| **Últimos 5 documentos** | Los 5 registros más recientes por `window_start`. Muestra ruta, inicio de ventana, porcentaje de retraso en esa ventana y número de vehículos. |
| **Ruta** | Identificador de ruta (ej. R001–R007). |
| **Ventana** | Inicio de la ventana de 15 minutos a la que corresponde el agregado. |
| **Retraso** | Porcentaje de vehículos considerados en retraso en esa ventana (heurística: velocidad &lt; 10 km/h). 100% = todos en retraso; 0% = ninguno. |
| **Vehículos** | Número de registros (vehículos) que entraron en esa ventana y ruta. |
| **Promedio de retraso por ruta** | Para cada ruta: promedio de `delay_percentage` en todas sus ventanas y número de ventanas (`count`). Ordenado de mayor a menor retraso medio. Sirve para ver qué rutas son más problemáticas. |

**Origen de los datos:** Topic Kafka `alerts`, generado por `delay_analysis.py`, persistido por `kafka_to_mongodb_alerts.py`.

---

### 2. vehicle_status

**Ejemplo:**
```
🚗 vehicle_status: 99 documentos
  - Vehículos en retraso: 85
```

| Elemento | Significado |
|----------|-------------|
| **Número de documentos** | Cantidad de eventos de estado de vehículos guardados. Cada documento es un evento de un vehículo (posición, velocidad, ruta, etc.) leído de `filtered-data`. Si el script inserta todo el histórico, el número crece con cada mensaje consumido. |
| **Vehículos en retraso** | Cuántos de esos documentos tienen `is_delayed: true` (velocidad &lt; 10 km/h en el momento del evento). Indica cuántos registros corresponden a vehículos considerados en retraso. |

**Origen de los datos:** Topic Kafka `filtered-data`, persistido por `kafka_to_mongodb_vehicle_status.py`. El script puede insertar todos los mensajes (histórico) o solo el último estado por vehículo, según configuración.

**Nota:** Si `vehicle_status` tiene 0 documentos, el consumidor de vehicle_status no se ha ejecutado o no ha recibido mensajes (revisar `auto_offset_reset` y que haya datos en `filtered-data`).

---

### 3. bottlenecks

**Ejemplo (sin datos):**
```
🔗 bottlenecks: 0 documentos
```

**Ejemplo (con datos, tras importar):**
```
🔗 bottlenecks: 5 documentos
  Top 5 bottlenecks (por grado):
  - A: grado 4
  - C: grado 3
  - E: grado 3
  ...
```

| Elemento | Significado |
|----------|-------------|
| **Número de documentos** | Cantidad de nodos detectados como cuellos de botella en la red (alto grado o centralidad). Proviene de HDFS `network_bottlenecks`, importado con `import_bottlenecks.py`. |
| **Top 5 bottlenecks** | Los 5 nodos con mayor `degree` (más conexiones). Ayuda a ver qué almacenes/nodos son más críticos en la red. |

**Origen de los datos:** HDFS `network_bottlenecks` generado por `network_analysis.py`, importado a MongoDB con `bash scripts/run/08_import_bottlenecks.sh` (o `spark-submit ... import_bottlenecks.py`).

**Nota:** Si bottlenecks tiene 0 documentos, no se ha ejecutado aún el script de importación desde HDFS, o el análisis de grafos no ha generado datos en `network_bottlenecks`.

---

## Resumen de las tres colecciones

| Colección | Origen en el pipeline | Qué representa |
|-----------|------------------------|----------------|
| **route_delay_aggregates** | Kafka `alerts` → consumidor alerts | Agregados de retraso por ruta y ventana de 15 min (porcentaje de retraso, vehículos, velocidades). |
| **vehicle_status** | Kafka `filtered-data` → consumidor vehicle_status | Eventos de estado de vehículos (posición, velocidad, ruta, is_delayed); puede ser histórico o último estado. |
| **bottlenecks** | HDFS `network_bottlenecks` → import_bottlenecks | Nodos de la red (almacenes/rutas) detectados como cuellos de botella (grado, centralidad). |

---

## Interpretación rápida de un resultado típico

- **route_delay_aggregates: 26 documentos** → El pipeline de retrasos y el consumidor de alerts están funcionando; hay 26 ventanas/ruta almacenadas.
- **vehicle_status: 99 documentos, 85 en retraso** → Se han persistido 99 eventos de vehículos; en 85 de ellos el vehículo estaba en retraso (speed &lt; 10).
- **bottlenecks: 0 documentos** → Aún no se ha importado la salida del análisis de grafos; ejecutar `08_import_bottlenecks.sh` para rellenar esta colección.

---

## Referencias

- Script de verificación: `storage/mongodb/verify_data.py`
- Descripción de scripts MongoDB: `storage/mongodb/README.md`
- Orden de ejecución del pipeline: `docs/guides/RUN_PIPELINE.md`
