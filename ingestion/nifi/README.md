# Configuración de Apache NiFi

Este directorio contiene la documentación de los flujos de ingesta de datos en NiFi para el proyecto. (Si existe un template `transport_monitoring_template.xml`, se puede importar desde NiFi → **Upload Template**.)

## Guía detallada: procesadores, propiedades y conexiones

**Documento principal:** [docs/guides/NIFI_FLUJOS.md](../../docs/guides/NIFI_FLUJOS.md)

En esa guía se indica, paso a paso:

- **Qué procesadores o grupos añadir** en cada momento (Process Group "Transport Monitoring", InvokeHTTP, PublishKafka_2_6, GetFile/TailFile, RouteOnAttribute, PutHDFS).
- **Propiedades y valores** a modificar o añadir (URLs de APIs, Kafka Brokers, Topic Name, directorio HDFS, Run Schedule, etc.).
- **Conexiones** entre procesadores (puertos success/failure → siguiente procesador).

## Resumen de flujos

| Flujo | Procesadores | Destino |
|-------|--------------|---------|
| OpenWeather | InvokeHTTP → PublishKafka_2_6 | Kafka `raw-data` |
| FlightRadar24 | InvokeHTTP → PublishKafka_2_6 | Kafka `raw-data` |
| Logs GPS | GetFile/TailFile → (RouteOnAttribute) → PublishKafka_2_6 + PutHDFS | Kafka `filtered-data` y HDFS `/user/hadoop/raw` |

## Configuración rápida

1. Crear Process Group **"Transport Monitoring"**.
2. Añadir y configurar los procesadores según **NIFI_FLUJOS.md** (Kafka: `localhost:9092`, topics `raw-data` y `filtered-data`; HDFS: `/user/hadoop/raw`).
3. Conectar salida **success** de cada origen al siguiente procesador; opcionalmente **failure** a retry o log.
4. Configurar Controller Service de Hadoop para PutHDFS (core-site.xml, hdfs-site.xml).
5. Iniciar los procesadores y comprobar mensajes en Kafka.

## Referencias

- **Manejo de errores y permisos HDFS:** docs/guides/TROUBLESHOOTING.md (sección NiFi).
- **Puertos y variables:** docs/guides/CONFIGURATION.md.
- **Arquitectura ingesta:** docs/architecture/ARCHITECTURE.md.
