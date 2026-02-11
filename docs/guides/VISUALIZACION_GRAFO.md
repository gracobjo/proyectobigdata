# Visualización del grafo de red de transporte

Esta funcionalidad permite **visualizar de forma interactiva** el grafo de la red de transporte (almacenes y rutas) usado en el análisis de grafos (GraphFrames), y opcionalmente **resaltar los cuellos de botella** cargados desde MongoDB.

## Descripción

- **Grafo:** Mismo modelo que `processing/spark/graphframes/network_analysis.py`: 5 nodos (almacenes A–E), 7 aristas (rutas) con distancia y tiempo.
- **Interactividad:** Grafo dibujado con **Pyvis** (red interactiva en el navegador: arrastrar nodos, zoom, tooltips en nodos y aristas).
- **Bottlenecks:** Si MongoDB está en marcha y la colección `transport_db.bottlenecks` tiene datos, los nodos con grado ≥ 3 se muestran en **rojo** y con tamaño proporcional al grado.

## Requisitos

- **Python 3** con el entorno virtual del proyecto.
- **Dependencias:** Incluidas en `requirements.txt`: `streamlit`, `pyvis`, `networkx`. Instalación:
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- **MongoDB (opcional):** Para resaltar bottlenecks, MongoDB en `127.0.0.1:27017` y colección `transport_db.bottlenecks` con documentos que tengan `node_id` y `degree`. Si no está disponible, el grafo se muestra igual sin colorear nodos.

## Cómo ejecutar

Desde la **raíz del proyecto**:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
streamlit run viz/app_grafo.py
```

Se abrirá el navegador en `http://localhost:8501`. La interfaz incluye:

| Elemento | Descripción |
|----------|-------------|
| **Grafo interactivo (Pyvis)** | Nodos = almacenes (A–E), aristas = rutas. Tooltips: nombre, región en nodos; ruta, km y minutos en aristas. |
| **Bottlenecks** | Si hay datos en MongoDB: mensaje de éxito y expandible con lista de nodos y grado. Nodos en rojo = cuello de botella. |
| **Resumen** | Número de nodos y aristas, leyenda (rojo = bottleneck, tamaño = grado) y lista de rutas de ejemplo. |

## Estructura de archivos

| Archivo | Uso |
|---------|-----|
| `viz/app_grafo.py` | App Streamlit: construye el grafo con NetworkX, lo renderiza con Pyvis y opcionalmente lee bottlenecks de MongoDB. |
| `viz/graph_data.py` | Datos del grafo (vértices y aristas) alineados con `network_analysis.py`. |
| `viz/README.md` | Resumen rápido de requisitos y comando de ejecución. |

## Relación con el pipeline

- El **grafo** (nodos y aristas) es el mismo que usa el job Spark `network_analysis.py`; aquí se replica en `graph_data.py` para no depender de Spark/HDFS al visualizar.
- Los **bottlenecks** mostrados provienen de MongoDB, que se alimenta con `storage/mongodb/import_bottlenecks.py` desde los Parquet de HDFS (`network_bottlenecks`) tras ejecutar el análisis de grafos.

Orden típico si quieres ver bottlenecks en la visualización:

1. Ejecutar análisis de grafos: `scripts/run/07_network_analysis.sh`
2. Importar bottlenecks a MongoDB: `scripts/run/08_import_bottlenecks.sh`
3. Arrancar la app: `streamlit run viz/app_grafo.py`

## Referencias

- Análisis de grafos (Spark): **docs/guides/ANALISIS_GRAFOS_SALIDA.md**
- Persistencia MongoDB (bottlenecks): **docs/ENTREGABLES.md** (sección R5c), **storage/mongodb/README.md**
- Ejecución del pipeline: **docs/guides/RUN_PIPELINE.md**
