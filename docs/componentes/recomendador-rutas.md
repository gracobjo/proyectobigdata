# Recomendación de rutas

Tres pasos (grafo + retrasos, entrenamiento modelo, recomendación con IA). Detalle: [IA_RUTAS.md](../guides/IA_RUTAS.md).

- **Paso 1:** Sin IA — API `GET /routes/recommend?from_node=A&to_node=D`
- **Paso 2:** Entrenar modelo — `python -m routing.train_delay_model`
- **Paso 3:** Con IA — API `GET /routes/recommend?from_node=A&to_node=D&use_ml=true`

Archivos: `routing/graph_data.py`, `routing/route_recommender.py`, `routing/train_delay_model.py`, `api/main.py`.
