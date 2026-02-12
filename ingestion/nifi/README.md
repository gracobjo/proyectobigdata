# Configuración de Apache NiFi

Este directorio contiene la documentación y la **definición de flujo** para importar en NiFi.

## Importar el flujo (NiFi 2.x)

1. En NiFi, arrastra **Process Group** al canvas (o Add → Process Group).
2. Doble clic en el grupo → en la barra de herramientas, **Upload flow definition** (icono de subir / Browse).
3. Selecciona el fichero **`transport_monitoring_flow.json`** de este directorio.
4. Revisa y **habilita** los procesadores que vayas a usar. Ajusta:
   - **OpenWeather InvokeHTTP**: sustituye `REPLACE_WITH_API_KEY` en Remote URL por tu API key.
   - **Kafka Brokers**: `localhost:9092` o `nodo1:9092` según tu entorno.
   - **GetFile**: directorio `Input Directory` (p. ej. `/home/hadoop/data/gps_logs`); créalo si no existe.
   - **PutHDFS**: configurar un **Controller Service** de Hadoop (core-site.xml, hdfs-site.xml) y asignarlo a PutHDFS si no lo toma por defecto.

Ver **docs/guides/NIFI_FLUJOS.md** para propiedades detalladas y conexiones.

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
| Logs GPS (Simulación) | GetFile/TailFile → (RouteOnAttribute) → PublishKafka_2_6 + PutHDFS | Kafka `filtered-data` y HDFS `/user/hadoop/raw` |
| **Sensores IoT (MQTT)** | ConsumeMQTT → JoltTransformJSON → PublishKafka_2_6 | Kafka `raw-data` |

**Nota**: Para integrar sensores IoT reales, ver **docs/guides/IOT_SENSORES.md** y el flujo de ejemplo **`iot_sensors_flow.json`**.

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
