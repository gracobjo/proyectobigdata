# Configuración de Apache NiFi

Definiciones de flujo para importar en NiFi y cómo usarlas.

**Enfoque del proyecto:** flujo principal = **ingesta de logs GPS**: **GetFile GPS Logs** → **PublishKafka** (topic `filtered-data`).

## Importar el flujo GPS (recomendado)

**Archivo listo para importar:** en la carpeta del proyecto `ingestion/nifi/` usa **`gps_transport_flow_importable.json`**.

- **GetFile GPS Logs** (directorio `/home/hadoop/data/gps_logs`, filtro `.*\.jsonl?`)
- **PublishKafka filtered-data** (brokers `localhost:9092`, topic `filtered-data`)
- **Conexión:** GetFile (success) → PublishKafka

**Pasos en NiFi 2.7.x:** Crear un **Process Group** → doble clic → **Upload flow definition** → seleccionar `gps_transport_flow_importable.json` → **Add**.

Si la importación falla, monta el flujo a mano: [nifi-montar-flujo-manual.md](nifi-montar-flujo-manual.md).

### Qué contienen los JSON importables

Cada `*_importable.json` es una definición completa de Process Group en formato NiFi 2.7 (propertyDescriptors, instanceIdentifier, etc.). Sin ellos la importación suele fallar.

### Otros flows

- **`transport_monitoring_flow_nifi27_importable.json`** — Incluye OpenWeather y FlightRadar24.
- Definiciones fuente en `ingestion/nifi/source/`. Regenerar: `python3 fix_flow_property_descriptors.py source/<fuente>.json <salida>_importable.json`.

## Guía detallada

Procesadores, propiedades y conexiones: [NIFI_FLUJOS.md](../guides/NIFI_FLUJOS.md).

## Configuración rápida (flujo GPS)

1. Importar `gps_transport_flow_importable.json` en un Process Group.
2. Directorio y datos de prueba: `mkdir -p /home/hadoop/data/gps_logs` y `python3 scripts/utils/generate_gps_log_file.py -n 100`.
3. En NiFi: revisar GetFile (Input Directory, File Filter) y PublishKafka (Kafka Brokers, Topic Name); arrancar ambos procesadores.
4. Comprobar: `kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic filtered-data --from-beginning --max-messages 3`.

## Referencias

- [TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) (sección NiFi)
- [CONFIGURATION.md](../guides/CONFIGURATION.md)
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
