# IA en el proyecto: cuándo introducirla y cómo mejorar rutas

Guía sobre **en qué momento** del pipeline tiene sentido introducir **Inteligencia Artificial** (modelos de ML) y **cómo mejorar las rutas** usando tanto lo que ya tenemos (grafo, retrasos, bottlenecks) como modelos predictivos.

---

## En qué momento podemos introducir IA

La IA (modelos de aprendizaje automático) tiene sentido **después** de tener datos limpios, enriquecidos y agregados. Es decir, **después** de las fases actuales del pipeline:

| Fase actual | Salida que necesitamos para IA |
|-------------|--------------------------------|
| Limpieza | Datos consistentes en Kafka/HDFS |
| Enriquecimiento | `route_id`, `is_delayed`, datos maestros (HDFS enriched) |
| Análisis de retrasos | `delay_aggregates`: delay_percentage, avg_speed por ruta y ventana |
| Análisis de grafos | Grafo (nodos, aristas), PageRank, grados, bottlenecks |
| MongoDB | Consultas rápidas: agregados, bottlenecks, vehicle_status |

**Momento idóneo para introducir IA:**

1. **Cuando exista historial de agregados de retrasos** (días o semanas de `route_delay_aggregates` en HDFS o MongoDB). Con eso se puede entrenar un modelo que prediga retraso o tiempo de viaje por ruta y ventana horaria.
2. **Cuando el grafo y los bottlenecks estén estabilizados** (nodos A–E, rutas con `time_minutes`, `distance_km`). Con eso se pueden mejorar rutas evitando segmentos críticos o ponderando aristas con retraso.

En la práctica: **tras ejecutar de forma recurrente** los pasos 01–08 (generar datos, limpieza, enriquecimiento, delay_analysis, análisis de grafos, import bottlenecks), se dispone de la base para:
- **Entrenar** un modelo (p. ej. semanal o mensual, orquestado con Airflow).
- **Inferir** en tiempo casi real o por lotes (recomendación de ruta, predicción de retraso).

No hace falta cambiar el orden actual del pipeline; la IA se añade como **nuevos pasos** que consumen las salidas ya existentes.

---

## ¿Podemos mejorar las rutas? Sí, de dos formas

### 1. Mejorar rutas **sin IA** (con lo que ya hay)

El proyecto ya tiene:

- **Grafo de la red** (`network_analysis.py`): nodos A–E, aristas con `time_minutes` y `distance_km`.
- **Bottlenecks** en MongoDB (nodos con alto grado).
- **Agregados de retrasos** por ruta y ventana (`delay_percentage`, `avg_speed`).

**Qué se puede hacer ya:**

- **Camino más corto / más rápido:** Usar GraphFrames para calcular el camino que minimiza tiempo (o distancia) entre dos nodos. El script actual ya calcula caminos (p. ej. A→D); se puede generalizar a cualquier par origen–destino.
- **Evitar nodos críticos:** Si un nodo es bottleneck (MongoDB), se puede calcular un camino alternativo que pase por otros nodos (por ejemplo, aumentando el “coste” de las aristas que tocan ese nodo y volviendo a calcular el camino).
- **Penalizar rutas con mucho retraso:** Consultar en MongoDB el `delay_percentage` reciente por ruta (o por arista, si mapeamos route_id a arista). Usar ese valor como peso extra en el grafo (p. ej. `time_effective = time_minutes * (1 + delay_percentage/100)`) y calcular el “camino más rápido en condiciones actuales”.

**Cómo hacerlo:**

- **Opción A – Script batch (Spark/GraphFrames):** Nuevo job que lea el grafo desde HDFS, lea retardos actuales desde MongoDB (o desde HDFS delay_aggregates), construya un grafo con aristas ponderadas por tiempo + penalización por retraso, y ejecute shortest path (o similar) para los pares origen–destino que interesen. Salida: tabla o fichero “mejor ruta A→D según últimos datos”.
- **Opción B – Servicio (API):** Endpoint en la API REST (o microservicio) que reciba origen y destino, consulte MongoDB (retrasos, bottlenecks), use el grafo en memoria (NetworkX o el mismo modelo que en `viz/graph_data.py`) y devuelva la ruta recomendada y, si se quiere, alternativas.

En ambos casos se **mejoran las rutas** en el sentido de “elegir la ruta que, con la información actual (retrasos, bottlenecks), es más rápida o más fiable”, sin ningún modelo de ML.

### 2. Mejorar rutas **con IA** (modelos predictivos)

Aquí la mejora viene de **predecir** retrasos o tiempos y elegir la ruta con **menor retraso (o tiempo) predicho**.

**Idea:**

- **Objetivo:** Dado un origen, un destino y una hora (y opcionalmente más contexto), recomendar la ruta que minimice el retraso esperado o el tiempo de viaje esperado.
- **Datos de entrenamiento:** Histórico de `route_delay_aggregates` (y, si se tiene, enriched): por cada ventana y ruta, tenemos `delay_percentage`, `avg_speed`, `route_id`, hora, día de la semana, etc.
- **Modelo:** Por ejemplo:
  - **Regresión:** Predecir `delay_percentage` o `avg_speed` para una ruta y una ventana horaria.
  - **Clasificación:** Predecir “¿esta ruta en esta hora estará retrasada? (sí/no)”.
- **Uso para rutas:** Para cada ruta candidata entre origen y destino (obtenida del grafo), se predice el retraso o el tiempo; se elige la ruta con mejor predicción (menor retraso o menor tiempo).

**Cuándo encaja en el pipeline:**

- **Entrenamiento:** Job batch (p. ej. semanal), después de tener suficientes `route_delay_aggregates`. Lee desde HDFS o MongoDB, entrena (Spark MLlib, scikit-learn o XGBoost), guarda el modelo (HDFS, fichero local o registro de modelos).
- **Inferencia:** En un servicio (API) o en un job batch: dado origen, destino y hora, (1) genera candidatos de ruta con el grafo, (2) para cada ruta candidata obtiene la predicción del modelo, (3) devuelve la ruta “mejor” según la predicción.

Así se **mejora la ruta** usando IA para anticipar qué tramos van a ir peor en lugar de limitarse al retraso actual.

---

## Cómo lo hacemos (pasos concretos)

### Paso 1: Mejora de rutas sin IA (rápida)

1. **Reutilizar el grafo** en un script (Python + NetworkX o Spark + GraphFrames) que tenga los mismos nodos y aristas que `network_analysis.py` / `viz/graph_data.py`.
2. **Leer retrasos actuales** desde MongoDB (`route_delay_aggregates` por `route_id`) o desde HDFS. Mapear cada `route_id` a la arista correspondiente (p. ej. Ruta_AB → arista A–B).
3. **Asignar pesos a las aristas:** por ejemplo `peso = time_minutes * (1 + delay_percentage/100)` usando el último `delay_percentage` conocido por ruta (o un valor por defecto si no hay datos).
4. **Calcular el camino mínimo** entre el nodo origen y el nodo destino con esos pesos. La secuencia de nodos (y las aristas) es la **ruta mejorada** según condiciones actuales.
5. **Opcional:** Exponer esto como endpoint en la API REST (ej. `GET /routes/recommend?from=A&to=D`) que devuelva la ruta recomendada y, si se quiere, tiempo estimado.

No requiere entrenamiento ni IA; solo grafo + datos de retraso en tiempo (casi) real.

### Paso 2: Entrenar un modelo de predicción de retrasos (IA)

1. **Preparar dataset:** Desde HDFS o MongoDB, construir una tabla con filas por (ventana, route_id) y columnas como: `hour`, `day_of_week`, `route_id` (codificado), `delay_percentage` o `avg_speed` como variable objetivo. Incluir si se puede información del grafo (grado del nodo, PageRank) por ruta.
2. **Entrenar:** Con Spark MLlib (Random Forest, GBT) o con Python (scikit-learn, XGBoost) en el venv. Guardar el modelo (MLlib: guardar en HDFS; sklearn: joblib/pickle en disco o en un registro).
3. **Orquestar:** Programar el re-entrenamiento (p. ej. semanal) con Airflow, igual que el DAG de re-entrenamiento mensual del modelo de grafos.

### Paso 3: Recomendación de ruta con IA

1. **Cargar el modelo** en un servicio (API) o en un job batch.
2. Dado **origen, destino y hora:**
   - Generar rutas candidatas (p. ej. los 1–3 caminos más cortos por tiempo en el grafo).
   - Para cada ruta candidata (o cada arista), predecir retraso o tiempo con el modelo.
   - Devolver la ruta con menor retraso predicho (o menor tiempo predicho).
3. Exponer como **GET /routes/recommend?from=A&to=D&at=2025-02-12T14:00** (o similar) en la API REST.

---

## Resumen

| Pregunta | Respuesta |
|----------|-----------|
| **¿En qué momento introducir IA?** | Después de tener historial de agregados de retrasos y grafo estable (pasos 01–08 en marcha). La IA se añade como nuevos jobs de entrenamiento e inferencia. |
| **¿Podemos mejorar rutas?** | Sí: (1) sin IA, usando grafo + retrasos actuales + camino mínimo ponderado; (2) con IA, prediciendo retraso/tiempo y eligiendo la ruta con mejor predicción. |
| **¿Cómo lo hacemos?** | Sin IA: script o API que pondera aristas con delay_percentage y calcula shortest path. Con IA: dataset desde delay_aggregates → entrenar modelo → en inferencia, puntuar rutas candidatas y devolver la mejor. |

**Implementación en el proyecto:** El módulo **routing/** y el endpoint **GET /routes/recommend** en la API ya implementan los tres pasos. Ver **routing/README.md** para cómo ejecutar el entrenamiento (Paso 2) y usar la recomendación con/sin IA (Paso 1 y 3) desde la API.
