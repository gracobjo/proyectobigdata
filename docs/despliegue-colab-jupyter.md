# Probar el proyecto en Google Colab, Jupyter o Binder

Guía para **alojar y probar** el proyecto en entornos tipo notebook (Colab, Jupyter, Binder, Kaggle, etc.) sin instalar el stack completo en tu máquina.

## Qué se puede ejecutar en cada entorno

Estos entornos ejecutan **Python** y permiten instalar paquetes con `pip`; **no** ejecutan servicios como Hadoop, NiFi, Kafka ni Airflow. Por tanto:

| Componente | Colab | Jupyter / Binder | Kaggle / DeepNote |
|------------|--------|-------------------|-------------------|
| **Recomendador de rutas** (grafo + NetworkX) | ✅ | ✅ | ✅ |
| **API REST** (FastAPI) en segundo plano + enlace público | ✅ (con ngrok o proxy) | ✅ (con ngrok) | ✅ |
| **Visualización del grafo** (Streamlit) | ✅ (modo iframe / tunnel) | ✅ | ✅ |
| **Spark** (PySpark local) | ✅ (limitado por memoria) | ✅ | ✅ |
| **MongoDB** | ❌ (usar **MongoDB Atlas** desde el notebook) | ❌ (Atlas) | ❌ (Atlas) |
| **Kafka / HDFS / NiFi / Airflow** | ❌ | ❌ | ❌ |

La idea: **el repo está alojado en GitHub**; en Colab/Jupyter/Binder **clonas el repo** (o abres un notebook que ya lo hace), instalas dependencias ligeras y ejecutas demos (recomendador, API opcional con MongoDB Atlas).

---

## 1. Google Colab

### Opción A: Abrir el notebook del repo (recomendado)

1. Abre el notebook del proyecto en Colab usando el enlace **"Open in Colab"** (si está en el README o en `notebooks/`):
   - URL directa (sustituye `USUARIO` y `REPO` por tu usuario y repo de GitHub):
   - `https://colab.research.google.com/github/USUARIO/REPO/blob/main/notebooks/ProyectoBigData_Colab.ipynb`

2. En la primera celda el notebook suele clonar el repo (o usar el repo ya montado si abriste desde GitHub) e instalar dependencias mínimas (`requirements-vercel.txt` o las del propio notebook).

3. Ejecuta las celdas en orden: verás el grafo de rutas y la recomendación sin MongoDB. Si tienes **MongoDB Atlas**, puedes definir `MONGO_URI` en una celda y probar la API o el recomendador con datos reales.

### Opción B: Crear un notebook desde cero en Colab

1. **Archivo → Nuevo notebook**.
2. Celda 1 (clonar e instalar):
   ```python
   !git clone https://github.com/USUARIO/ProyectoBigData.git
   %cd ProyectoBigData
   !pip install -q -r requirements-vercel.txt
   import sys
   sys.path.insert(0, ".")
   ```
3. Celda 2 (demo recomendador sin MongoDB):
   ```python
   import networkx as nx
   from routing.graph_data import EDGES

   G = nx.DiGraph()
   for (src, dst, rid, dist_km, time_min) in EDGES:
       G.add_edge(src, dst, weight=time_min)
   path = nx.shortest_path(G, "A", "D", weight="weight")
   print("Ruta recomendada A → D:", path)
   ```
4. Opcional: ejecutar la API en segundo plano y exponerla con **ngrok** (ver sección "Exponer la API en Colab" más abajo).

---

## 2. Jupyter (local o JupyterHub)

1. **Clonar el repo** en tu máquina o en el servidor donde corre Jupyter:
   ```bash
   git clone https://github.com/USUARIO/ProyectoBigData.git
   cd ProyectoBigData
   ```
2. **Crear un entorno** e instalar dependencias ligeras (para no instalar Spark/Airflow si solo quieres la API y el recomendador):
   ```bash
   python -m venv venv
   source venv/bin/activate   # o venv\Scripts\activate en Windows
   pip install -r requirements-vercel.txt
   ```
3. **Abrir Jupyter** desde la raíz del proyecto:
   ```bash
   jupyter notebook
   ```
4. Abre `notebooks/ProyectoBigData_Colab.ipynb` (o crea uno nuevo con `sys.path.insert(0, "..")` si estás dentro de `notebooks/`). Ejecuta las celdas; para usar MongoDB, configura `MONGO_URI` (por ejemplo a MongoDB Atlas).

---

## 3. Binder (mybinder.org)

Binder levanta un Jupyter desde un repo de GitHub.

1. En el repo asegúrate de tener:
   - Un notebook en `notebooks/` (por ejemplo `ProyectoBigData_Colab.ipynb`).
   - Un `notebooks/requirements.txt` (o `requirements.txt` en la raíz) con las dependencias que Binder debe instalar. Para no alargar mucho el build, usa solo las necesarias (p. ej. las de `requirements-vercel.txt`).

2. El repo incluye **`binder/requirements.txt`** con dependencias ligeras; Binder lo usará para construir el entorno (no el `requirements.txt` de la raíz, que incluye Spark/Airflow).

3. Abre Binder con la URL (sustituye USUARIO y REPO):
   ```
   https://mybinder.org/v2/gh/USUARIO/REPO/HEAD?labpath=notebooks%2FProyectoBigData_Colab.ipynb
   ```
4. Binder construirá el entorno y abrirá el notebook. La primera vez puede tardar varios minutos. Luego ejecuta las celdas como en Colab.

---

## 4. Kaggle Notebooks / DeepNote / Otros

- **Kaggle**: Crear un nuevo Notebook, en Settings añadir "GitHub" como fuente de datos (tu repo) o pegar el código del notebook; instalar con `!pip install -r requirements-vercel.txt` (si tienes el repo clonado) y usar `sys.path.insert(0, "ProyectoBigData")` para importar `routing`, `api`, etc.
- **DeepNote / Datalore / Google Cloud Vertex AI Workbench**: Mismo esquema: clonar el repo, `pip install -r requirements-vercel.txt`, ejecutar el notebook. Para MongoDB usar siempre Atlas y `MONGO_URI`.

En todos estos entornos, **Hadoop, NiFi, Kafka y Airflow no están disponibles**; solo puedes probar lógica Python, el recomendador de rutas, la API (con MongoDB externo) y, si el entorno lo permite, Spark en modo local.

---

## 5. Exponer la API en Colab (opcional)

Si quieres que la API REST (Swagger) sea accesible desde fuera de Colab:

1. Instala ngrok y la API (en el notebook):
   ```python
   !pip install -q pyngrok fastapi uvicorn pymongo
   ```
2. Arranca la API en segundo plano (después de clonar el repo y tener `api.main`):
   ```python
   import threading
   import uvicorn
   def run_api():
       uvicorn.run("api.main:app", host="0.0.0.0", port=5000)
   t = threading.Thread(target=run_api, daemon=True)
   t.start()
   ```
3. Expón el puerto con ngrok (necesitas cuenta en ngrok y token):
   ```python
   from pyngrok import ngrok
   url = ngrok.connect(5000)
   print("Abrir Swagger:", url.public_url + "/docs")
   ```
   Abre ese enlace en el navegador para usar la API (requiere MongoDB Atlas en `MONGO_URI` para que los endpoints devuelvan datos).

---

## 6. Resumen de enlaces útiles

| Dónde | Enlace / Acción |
|-------|------------------|
| **Colab** | Abrir: `https://colab.research.google.com/github/USUARIO/ProyectoBigData/blob/main/notebooks/ProyectoBigData_Colab.ipynb` |
| **Binder** | `https://mybinder.org/v2/gh/USUARIO/ProyectoBigData/HEAD?labpath=notebooks%2FProyectoBigData_Colab.ipynb` |
| **Repo** | Clonar y abrir `notebooks/ProyectoBigData_Colab.ipynb` en Jupyter local |
| **MongoDB** | Usar [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) y definir `MONGO_URI` en el notebook |

Sustituye **USUARIO** por tu usuario de GitHub (por ejemplo `gracobjo`) y **ProyectoBigData** por el nombre del repo si es distinto.

---

## Referencias

- [docs/README.md](README.md) — Índice de documentación.
- [docker/README.md](../docker/README.md) — Docker, Railway, Vercel, S3.
- [componentes/recomendador-rutas.md](componentes/recomendador-rutas.md) — Lógica del recomendador de rutas.
