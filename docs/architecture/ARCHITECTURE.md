# Arquitectura del Sistema

## Visión General

La plataforma implementa una **arquitectura Lambda/Kappa** que permite el procesamiento tanto en tiempo real (streaming) como en batch, siguiendo el ciclo de vida KDD.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                         │
├─────────────────────────────────────────────────────────────────┤
│  APIs Públicas (OpenWeather, FlightRadar24)                     │
│  Logs GPS Simulados                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASE I: INGESTA                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  Apache NiFi │────────▶│ Apache Kafka │                     │
│  │    2.6.0     │         │   3.9.1      │                     │
│  └──────────────┘         └──────┬───────┘                     │
│         │                        │                              │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  HDFS Raw    │         │ Topics:      │                     │
│  │  (Auditoría) │         │ - raw-data   │                     │
│  └──────────────┘         │ - filtered   │                     │
│                           └──────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE II: PREPROCESAMIENTO Y TRANSFORMACIÓN         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Apache Spark 3.5.x                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Spark SQL: Limpieza y normalización                   │  │
│  │  • Structured Streaming: Procesamiento en tiempo real    │  │
│  │  • GraphFrames: Modelado de red de transporte           │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                        │                              │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  Hive        │         │  MongoDB     │                     │
│  │  (SQL)       │         │  (NoSQL)     │                     │
│  └──────────────┘         └──────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE III: MINERÍA Y ACCIÓN                         │
├─────────────────────────────────────────────────────────────────┤
│  • Ventanas de tiempo (15 minutos)                              │
│  • Cálculo de medias de retrasos                                │
│  • Detección de cuellos de botella                              │
│  • Optimización de rutas                                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE IV: ORQUESTACIÓN                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Apache Airflow 2.10.x                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Re-entrenamiento mensual de modelos                   │  │
│  │  • Limpieza de tablas temporales                         │  │
│  │  • Coordinación de workflows                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Capa de Ingesta

**Apache NiFi 2.6.0**
- Consume datos de APIs públicas
- Procesa logs GPS simulados
- Implementa back-pressure y manejo de errores
- Almacena copia raw en HDFS

**Apache Kafka 3.9.1 (KRaft mode)**
- Topics: `raw-data` y `filtered-data`
- Distribución de eventos en tiempo real
- Persistencia de mensajes

### 2. Capa de Procesamiento

**Apache Spark 3.5.x**
- **Spark SQL**: Limpieza, normalización, gestión de nulos
- **Structured Streaming**: Procesamiento en tiempo real con ventanas
- **GraphFrames**: Modelado de red de transporte, cálculo de caminos más cortos

### 3. Capa de Almacenamiento

**HDFS 3.4.2**
- Datos raw para auditoría
- Datos procesados para análisis histórico

**Apache Hive**
- Datos agregados para reporting histórico
- Consultas SQL sobre datos estructurados

**MongoDB**
- Último estado conocido de cada vehículo
- Agregados recientes de retrasos por ruta
- Consultas de baja latencia orientadas a API/microservicios

### 4. Capa de Orquestación

**Apache Airflow 2.10.x**
- DAGs complejos con dependencias
- Reintentos y alertas
- Coordinación de workflows

## Flujo de Datos

1. **Ingesta**: NiFi → Kafka → HDFS (raw)
2. **Procesamiento**: Kafka → Spark → Hive/MongoDB
3. **Análisis**: Spark Streaming → Ventanas de tiempo → Alertas
4. **Orquestación**: Airflow coordina workflows periódicos

## Escalabilidad

- **HDFS**: Distribución horizontal de datos
- **YARN**: Gestión de recursos distribuidos
- **Kafka**: Particionado de topics para paralelismo
- **Spark**: Procesamiento distribuido en cluster

## Seguridad

- Autenticación y autorización en HDFS
- Seguridad en Kafka (SASL/SSL)
- Control de acceso en Hive y MongoDB (roles, usuarios, IP allowlist)
