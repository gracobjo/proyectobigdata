# Salida del Análisis de Grafos – Verificación

## ¿Es correcta esta salida?

Sí. Si tras ejecutar `07_network_analysis.sh` ves algo como lo siguiente, el job ha terminado bien.

---

## Ejemplo de salida correcta

### 1. network_bottlenecks

```text
Found 2 items
-rw-r--r--   1 hadoop supergroup          0 2026-02-11 23:05 .../network_bottlenecks/_SUCCESS
-rw-r--r--   1 hadoop supergroup        735 2026-02-11 23:05 .../network_bottlenecks/part-00000-....snappy.parquet
```

| Elemento | Significado |
|----------|-------------|
| `_SUCCESS` | Spark escribe este fichero vacío cuando el job termina bien. |
| `part-00000-....snappy.parquet` | Nodos detectados como cuellos de botella (alto grado o alta centralidad). Tamaño pequeño (p. ej. 735 B) es normal para un grafo pequeño (5 nodos, 7 aristas). |

---

### 2. network_pagerank

```text
Found 5 items
-rw-r--r--   1 hadoop supergroup          0 .../network_pagerank/_SUCCESS
-rw-r--r--   1 hadoop supergroup       1776 .../network_pagerank/part-00000-....snappy.parquet
-rw-r--r--   1 hadoop supergroup       1748 .../network_pagerank/part-00001-....snappy.parquet
-rw-r--r--   1 hadoop supergroup       1762 .../network_pagerank/part-00002-....snappy.parquet
-rw-r--r--   1 hadoop supergroup       1780 .../network_pagerank/part-00003-....snappy.parquet
```

| Elemento | Significado |
|----------|-------------|
| `_SUCCESS` | Job de PageRank completado correctamente. |
| `part-00000` … `part-00003` | Cuatro particiones con los nodos y su puntuación PageRank (importancia en la red). Varias particiones son normales por la configuración de shuffle (p. ej. 4 particiones). |

---

### 3. network_degrees

```text
Found 2 items
-rw-r--r--   1 hadoop supergroup          0 .../network_degrees/_SUCCESS
-rw-r--r--   1 hadoop supergroup        749 .../network_degrees/part-00000-....snappy.parquet
```

| Elemento | Significado |
|----------|-------------|
| `_SUCCESS` | Job de grados completado correctamente. |
| `part-00000-....snappy.parquet` | Nodos con su grado (número de conexiones entrantes/salientes). Un solo part es normal para pocos nodos. |

---

## Resumen

- **network_bottlenecks:** 2 ítems (_SUCCESS + 1 Parquet) → correcto.
- **network_pagerank:** 5 ítems (_SUCCESS + 4 Parquet) → correcto.
- **network_degrees:** 2 ítems (_SUCCESS + 1 Parquet) → correcto.

El análisis de grafos ha escrito los tres conjuntos de resultados en HDFS. Siguiente paso opcional: importar bottlenecks a MongoDB con `bash scripts/run/08_import_bottlenecks.sh`.
