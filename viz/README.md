# Visualización del grafo de red de transporte

App **Streamlit** que muestra el grafo de almacenes y rutas (mismo modelo que `processing/spark/graphframes/network_analysis.py`) y resalta los **bottlenecks** cargados desde MongoDB.

## Requisitos

- Python 3 con dependencias del proyecto (`pip install -r requirements.txt` incluye streamlit, pyvis, networkx).
- MongoDB opcional: si está en marcha y la colección `transport_db.bottlenecks` tiene datos, los nodos con grado ≥ 3 se muestran en rojo.

## Cómo ejecutar

Desde la **raíz del proyecto**:

```bash
source venv/bin/activate   # o tu entorno virtual
pip install -r requirements.txt   # si aún no tienes streamlit, pyvis, networkx
streamlit run viz/app_grafo.py
```

Se abrirá el navegador en `http://localhost:8501` con:

- **Grafo interactivo (Pyvis):** arrastrar nodos, zoom, tooltips en nodos (nombre, región) y aristas (ruta, km, minutos).
- **Bottlenecks:** si MongoDB está disponible, nodos en rojo = cuello de botella; tamaño proporcional al grado.
- **Resumen:** número de nodos/aristas y lista de rutas.

## Estructura

- `viz/app_grafo.py` – App Streamlit (Pyvis + NetworkX).
- `viz/graph_data.py` – Datos del grafo (vértices y aristas) alineados con `network_analysis.py`.
