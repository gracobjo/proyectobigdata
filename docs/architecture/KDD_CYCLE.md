# Ciclo KDD en el Proyecto

## Knowledge Discovery in Databases (KDD)

Este proyecto implementa el ciclo completo KDD para descubrir conocimiento a partir de datos de transporte.

## Fases del Ciclo KDD

### 1. Selección (Selection)

**Objetivo**: Identificar y obtener los datos relevantes para el análisis.

**Implementación**:
- **NiFi**: Consume datos de APIs públicas (OpenWeather, FlightRadar24)
- **NiFi**: Procesa logs GPS simulados
- **Kafka**: Distribuye datos en topics `raw-data` y `filtered-data`
- **HDFS**: Almacena copia raw para auditoría

**Archivos relacionados**:
- `ingestion/nifi/` - Configuraciones de NiFi
- `ingestion/kafka/create_topics.sh` - Creación de topics

### 2. Preprocesamiento (Preprocessing)

**Objetivo**: Limpiar y preparar los datos para el análisis.

**Implementación**:
- **Spark SQL**: Normalización de formatos
- **Spark SQL**: Gestión de nulos y valores inválidos
- **Spark SQL**: Eliminación de duplicados
- **Spark SQL**: Validación de rangos (coordenadas, velocidades)

**Archivos relacionados**:
- `processing/spark/sql/data_cleaning.py` - Script de limpieza

**Operaciones realizadas**:
- Trim y uppercase de campos de texto
- Validación de coordenadas geográficas (-90 a 90 latitud, -180 a 180 longitud)
- Validación de velocidades (0 a 200 km/h)
- Conversión de timestamps
- Eliminación de registros duplicados

### 3. Transformación (Transformation)

**Objetivo**: Transformar y enriquecer los datos con información adicional.

**Implementación**:
- **Spark SQL**: Enriquecimiento cruzando streaming con datos maestros de Hive
- **GraphFrames**: Modelado de red de transporte como grafo
- **GraphFrames**: Cálculo de métricas de red (PageRank, grados, caminos más cortos)

**Archivos relacionados**:
- `processing/spark/sql/data_enrichment.py` - Enriquecimiento de datos
- `processing/spark/graphframes/network_analysis.py` - Análisis de grafos

**Transformaciones realizadas**:
- Join con tablas maestras de rutas y vehículos
- Cálculo de campos derivados (is_delayed)
- Modelado de red: Nodos = Almacenes, Aristas = Rutas
- Cálculo de PageRank para identificar nodos críticos
- Detección de comunidades y triángulos en la red

### 4. Minería de Datos (Data Mining)

**Objetivo**: Aplicar algoritmos de minería de datos para descubrir patrones.

**Implementación**:
- **Structured Streaming**: Ventanas de tiempo de 15 minutos
- **Structured Streaming**: Cálculo de agregaciones (medias, conteos)
- **Structured Streaming**: Detección de retrasos y cuellos de botella
- **GraphFrames**: Análisis de patrones en la red

**Archivos relacionados**:
- `processing/spark/streaming/delay_analysis.py` - Análisis de retrasos

**Patrones descubiertos**:
- Porcentaje de retrasos por ruta
- Velocidades promedio en ventanas de tiempo
- Nodos críticos en la red (alto PageRank)
- Rutas con mayor número de retrasos

### 5. Interpretación/Evaluación (Interpretation/Evaluation)

**Objetivo**: Interpretar los resultados y evaluar el conocimiento descubierto.

**Implementación**:
- **Hive**: Almacenamiento de agregados para reporting histórico
- **Cassandra**: Último estado conocido para consultas de baja latencia
- **Airflow**: Generación de reportes diarios
- **SQL**: Consultas analíticas sobre datos agregados

**Archivos relacionados**:
- `storage/hive/daily_report.sql` - Reportes SQL
- `orchestration/airflow/dags/transport_monitoring_dag.py` - Orquestación

**Resultados interpretados**:
- Identificación de rutas problemáticas
- Detección de cuellos de botella en la red
- Alertas en tiempo real sobre retrasos
- Optimización de rutas basada en análisis de grafos

## Flujo Completo KDD

```
┌─────────────────────────────────────────────────────────────┐
│  1. SELECCIÓN                                               │
│  APIs → NiFi → Kafka → HDFS (raw)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  2. PREPROCESAMIENTO                                        │
│  Kafka → Spark SQL → Limpieza → Kafka (filtered)            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TRANSFORMACIÓN                                          │
│  Kafka → Spark SQL → Enriquecimiento                        │
│  GraphFrames → Modelado de Red → Análisis                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  4. MINERÍA                                                 │
│  Structured Streaming → Ventanas → Agregaciones             │
│  Detección de Patrones → Alertas                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  5. INTERPRETACIÓN                                          │
│  Hive (Reporting) + Cassandra (Estado Actual)              │
│  Airflow → Reportes → Optimización                          │
└─────────────────────────────────────────────────────────────┘
```

## Métricas y KPIs

### Métricas de Calidad de Datos
- Porcentaje de datos válidos después de limpieza
- Tasa de duplicados eliminados
- Tasa de valores nulos gestionados

### Métricas de Negocio
- Porcentaje de retrasos por ruta
- Velocidad promedio por ventana de tiempo
- Número de vehículos en tránsito
- Identificación de nodos críticos

### Métricas de Rendimiento
- Latencia de procesamiento (tiempo desde ingesta hasta análisis)
- Throughput (mensajes por segundo)
- Tiempo de respuesta de consultas

## Automatización del Ciclo KDD

El ciclo KDD está completamente automatizado mediante:

1. **NiFi**: Automatiza la selección de datos
2. **Spark Streaming**: Automatiza preprocesamiento y transformación en tiempo real
3. **Airflow**: Orquesta el ciclo completo y tareas periódicas
4. **Hive/Cassandra**: Almacenamiento automático de resultados

## Mejoras Continuas

- **Re-entrenamiento mensual**: El modelo de grafos se re-entrena mensualmente con nuevos datos
- **Limpieza automática**: Las tablas temporales se limpian automáticamente
- **Monitoreo**: Airflow monitorea el éxito/fallo de cada fase
