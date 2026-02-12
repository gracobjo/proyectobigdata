# Recomendación de rutas (Paso 1, 2 y 3)

Implementación de los tres pasos descritos en **docs/guides/IA_RUTAS.md**.

## Paso 1: Sin IA (grafo + retrasos MongoDB)

- **Grafo:** Mismo que `viz/graph_data.py` y `network_analysis.py` (nodos A–E, aristas con tiempo).
- **Retrasos:** Se leen los últimos `delay_percentage` por `route_id` desde MongoDB `route_delay_aggregates`.
- **Peso:** `time_minutes * (1 + delay_percentage/100)`.
- **Salida:** Camino mínimo por peso (Dijkstra).

**API:** `GET /routes/recommend?from_node=A&to_node=D` (sin `use_ml` o `use_ml=false`).

**Requisitos:** MongoDB con datos en `route_delay_aggregates` (ejecutar pipeline: delay_analysis + consumer MongoDB).

---

## Paso 2: Entrenar modelo de predicción de retrasos

- **Dataset:** MongoDB `route_delay_aggregates` (features: route_id, hour, day_of_week, month; target: delay_percentage).
- **Modelo:** RandomForestRegressor (scikit-learn). Se guarda en `routing/model_delay.joblib` y el encoder en `routing/encoder_route.joblib`.

**Ejecutar** (desde la raíz del proyecto, con venv activado):

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
pip install scikit-learn joblib pandas  # o pip install -r requirements.txt
python -m routing.train_delay_model
```

Opcional: `--min-samples 50`. Si hay pocos documentos en MongoDB, el script avisa pero entrena igual.

**Orquestar con Airflow:** Añadir una tarea que ejecute `python -m routing.train_delay_model` (p. ej. semanalmente).

---

## Paso 3: Recomendación con IA (API)

- **Candidatos:** Hasta 5 caminos más cortos por tiempo base entre origen y destino.
- **Puntuación:** Para cada camino, se predice `delay_percentage` por arista (y hora, si se pasa `at`) con el modelo; tiempo efectivo = suma de `time_min * (1 + pred_delay/100)`.
- **Salida:** El camino con menor tiempo efectivo predicho.

**API:** `GET /routes/recommend?from_node=A&to_node=D&use_ml=true`  
Opcional: `&at=2025-02-12T14:00` para evaluar a una hora concreta.

Si no existe el modelo (`model_delay.joblib`), el endpoint usa automáticamente el Paso 1 (retrasos actuales en MongoDB).

---

## Resumen de archivos

| Archivo | Uso |
|---------|-----|
| `routing/graph_data.py` | Nodos, aristas, mapeo R001… ↔ (src, dst). |
| `routing/route_recommender.py` | Paso 1 (recommend_route) y Paso 3 (recommend_route_ml, load_model, predict_delay_for_route). |
| `routing/train_delay_model.py` | Paso 2: entrenar y guardar modelo + encoder. |
| `api/main.py` | Endpoint `GET /routes/recommend` (Paso 1 y 3 según `use_ml`). |

Documentación completa: **docs/guides/IA_RUTAS.md**.
