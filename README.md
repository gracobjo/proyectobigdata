# Proyecto Big Data - Plataforma de Monitorización de Red de Transporte Global

## Descripción del Proyecto

Este proyecto implementa una plataforma de Big Data capaz de monitorizar una red de transporte global, cruzando datos de sensores en tiempo real con información histórica y grafos de rutas para predecir cuellos de botella y optimizar la logística.

## Arquitectura

El proyecto sigue una **arquitectura Lambda/Kappa** 100% basada en Apache y automatiza el ciclo de vida **KDD (Knowledge Discovery in Databases)**:

1. **Selección**: Ingesta de datos desde múltiples fuentes
2. **Preprocesamiento**: Limpieza y normalización de datos
3. **Transformación**: Enriquecimiento y modelado de grafos
4. **Minería**: Análisis en tiempo real y machine learning
5. **Interpretación**: Visualización y reporting

## Stack Tecnológico (Apache 2026)

- **Ingesta**: Apache NiFi 2.6.0 & Apache Kafka 3.9.1 (KRaft mode)
- **Procesamiento**: Apache Spark 3.5.x (Spark SQL, Structured Streaming, GraphFrames)
- **Orquestación**: Apache Airflow 2.10.x
- **Almacenamiento**: 
  - HDFS 3.4.2 (datos raw y procesados)
  - MongoDB (NoSQL - último estado conocido de cada vehículo y agregados de retrasos)
  - Apache Hive (SQL - reporting histórico)
- **Gestión de Recursos**: YARN

## Entorno del Cluster

El proyecto está configurado para ejecutarse en un cluster distribuido:

- **nodo1** (equipo físico): NameNode, ResourceManager, Kafka, MongoDB, NiFi, Airflow
- **nodo2** (VM VirtualBox): DataNode, NodeManager

Ver [docs/architecture/CLUSTER_SETUP.md](docs/architecture/CLUSTER_SETUP.md) para detalles de configuración del cluster.

## Estructura del Proyecto

```
ProyectoBigData/
├── ingestion/          # Fase I: Ingesta y Selección
│   ├── nifi/          # Configuraciones y flujos de NiFi
│   └── kafka/         # Scripts y configuraciones de Kafka
├── processing/         # Fase II y III: Procesamiento
│   ├── spark/
│   │   ├── sql/       # Scripts Spark SQL
│   │   ├── streaming/ # Structured Streaming
│   │   └── graphframes/ # Análisis de grafos
│   └── scripts/       # Scripts auxiliares
├── storage/            # Persistencia y modelos de datos
│   ├── hive/          # Scripts SQL de reportes (daily_report.sql)
│   ├── mongodb/       # Consumers Kafka→MongoDB, verificación
│   └── cassandra/     # Diseño lógico de colecciones MongoDB (ver README ahí)
├── orchestration/      # Fase IV: Orquestación
│   └── airflow/
│       ├── dags/      # DAGs de Airflow
│       ├── logs/      # Logs de ejecución
│       └── plugins/   # Plugins personalizados
├── config/            # Archivos de configuración
│   └── cluster.properties  # Configuración centralizada del cluster
├── data/              # Definiciones y maestros (datos crudos en HDFS/Kafka)
│   ├── gps_logs/     # README; .jsonl se generan con scripts/utils
│   └── master/       # sample_master_data.sql para Hive/HDFS
├── docs/              # Documentación (architecture, guides, api)
├── api/               # API REST (MongoDB)
├── routing/           # Recomendador de rutas y modelo de retrasos
├── viz/               # Visualización del grafo
└── scripts/           # Setup, run, stack (arranque/parada de la pila)
```

**Hive y carpetas “vacías”:** Los datos viven en HDFS, Kafka y MongoDB. Algunas carpetas solo tienen configs o documentación. Ver **docs/guides/HIVE_Y_ESTRUCTURA_PROYECTO.md**.

## Fases del Proyecto

### Fase I: Ingesta y Selección (NiFi + Kafka)
- Configuración de NiFi para consumir APIs públicas (OpenWeather, FlightRadar24)
- Procesamiento de logs simulados de GPS
- Publicación en temas de Kafka (Datos Crudos y Datos Filtrados)
- Almacenamiento raw en HDFS para auditoría

### Fase II: Preprocesamiento y Transformación (Spark)
- Limpieza de datos con Spark SQL
- Enriquecimiento cruzando streaming con datos maestros de Hive
- Modelado de red de transporte con GraphFrames
- Cálculo de caminos más cortos y detección de comunidades críticas

### Fase III: Minería y Acción (Streaming + ML)
- Cálculo de medias de retrasos en ventanas de 15 minutos
- Carga multicapa:
  - Hive: Datos agregados para reporting histórico
  - MongoDB: Último estado conocido de cada vehículo y agregados recientes para consultas de baja latencia

### Fase IV: Orquestación (Airflow)
- DAG para re-entrenamiento mensual del modelo de grafos
- Limpieza de tablas temporales en HDFS
- Coordinación de workflows complejos

## Requisitos Previos

- Java 11 o superior
- Python 3.8+
- Hadoop 3.4.2 configurado en cluster (nodo1 + nodo2)
- Apache NiFi 2.6.0
- Apache Kafka 3.9.1
- Apache Spark 3.5.x
- Apache Airflow 2.10.x
- MongoDB (comunidad o Atlas)
- Apache Hive

## 🚀 Inicio Rápido

**¿Primera vez con el proyecto?** Empieza aquí:

👉 **[Guía de Inicio Rápido](docs/GETTING_STARTED.md)** - Paso a paso desde cero

**Probar sin instalar (Colab, Jupyter, Binder)**  
Notebook listo para ejecutar en [Google Colab](https://colab.research.google.com/github/gracobjo/proyectobigdata/blob/main/notebooks/ProyectoBigData_Colab.ipynb) o [Binder](https://mybinder.org/v2/gh/gracobjo/proyectobigdata/HEAD?labpath=notebooks%2FProyectoBigData_Colab.ipynb): recomendador de rutas y opcional API con MongoDB Atlas. Ver [docs/despliegue-colab-jupyter.md](docs/despliegue-colab-jupyter.md).

## Configuración Inicial del Cluster

1. **Configurar /etc/hosts** en ambos nodos:
```bash
# En ambos nodos
sudo nano /etc/hosts
# Añadir:
<IP_nodo1>    nodo1
<IP_nodo2>    nodo2
```

2. **Ejecutar script de configuración**:
```bash
./scripts/setup/configure_cluster.sh
```

3. Ver [docs/architecture/CLUSTER_SETUP.md](docs/architecture/CLUSTER_SETUP.md) para más detalles.

## Instalación

Ver [docs/guides/INSTALLATION.md](docs/guides/INSTALLATION.md) para instrucciones detalladas.

## Uso

Ver [docs/guides/USAGE.md](docs/guides/USAGE.md) para guías de uso.

## Documentación

**Índice completo:** [docs/README.md](docs/README.md) — Ingesta, datos, storage, componentes, scripts, orquestación, guías y API.

- [Arquitectura del Sistema](docs/architecture/ARCHITECTURE.md) · [Configuración del Cluster](docs/architecture/CLUSTER_SETUP.md)
- [Guía de Configuración](docs/guides/CONFIGURATION.md) · [Instalación](docs/guides/INSTALLATION.md) · [Uso](docs/guides/USAGE.md)
- [Airflow](docs/guides/AIRFLOW.md) · [NiFi (flujos y propiedades)](docs/guides/NIFI_FLUJOS.md) · [Fuentes de datos](docs/guides/FUENTES_DATOS.md)
- [IoT / sensores](docs/guides/IOT_SENSORES.md) · [Visualización del grafo](docs/guides/VISUALIZACION_GRAFO.md)
- [API Reference](docs/api/API.md) · [Swagger/OpenAPI](docs/api/SWAGGER_API.md) · [IA y rutas](docs/guides/IA_RUTAS.md)

## Contribución

Este es un proyecto académico siguiendo el ciclo KDD.

## Licencia

Proyecto académico - Uso educativo
