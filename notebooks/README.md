# Notebooks – Colab, Jupyter, Binder

Notebooks para **probar el proyecto** sin instalar el stack completo (Hadoop, NiFi, Kafka, etc.).

## ProyectoBigData_Colab.ipynb

- **Recomendador de rutas** (grafo A–E) sin MongoDB.
- Opcional: con **MongoDB Atlas** (`MONGO_URI`) para retrasos reales.
- Opcional: levantar la **API REST** en el mismo kernel y probar `/docs`.

### Abrir

| Entorno | Enlace |
|--------|--------|
| **Google Colab** | [Abrir en Colab](https://colab.research.google.com/github/gracobjo/proyectobigdata/blob/main/notebooks/ProyectoBigData_Colab.ipynb) |
| **Binder** | [Abrir en Binder](https://mybinder.org/v2/gh/gracobjo/proyectobigdata/HEAD?labpath=notebooks%2FProyectoBigData_Colab.ipynb) |
| **Jupyter local** | Clona el repo, `pip install -r requirements-vercel.txt`, abre el `.ipynb`. |

Sustituye `gracobjo/proyectobigdata` por tu usuario/repo si usas un fork.

### Binder

Binder usa `notebooks/requirements.txt` para instalar dependencias al construir la imagen. Ver [docs/despliegue-colab-jupyter.md](../docs/despliegue-colab-jupyter.md).
