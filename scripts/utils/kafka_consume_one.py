#!/usr/bin/env python3
"""Consume 1 mensaje de un topic y lo imprime. Sirve para comprobar si el broker entrega datos."""
import sys
import time

BOOTSTRAP = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:9092"
TOPIC = sys.argv[1] if len(sys.argv) > 1 else "raw-data"
TIMEOUT_MS = 15000

# Reintentar conexión por si Kafka acaba de arrancar
for intento in range(5):
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP,
            auto_offset_reset="earliest",
            consumer_timeout_ms=TIMEOUT_MS,
        )
        break
    except Exception as e:
        if "NoBrokersAvailable" in str(type(e).__name__) or "NoBrokersAvailable" in str(e):
            print("Broker no disponible (¿Kafka en marcha?). Reintento %d/5 en 3s..." % (intento + 1), file=sys.stderr)
            time.sleep(3)
            continue
        raise
else:
    print("No se pudo conectar al broker en 127.0.0.1:9092. Comprueba: jps | grep -i kafka", file=sys.stderr)
    sys.exit(2)

for msg in consumer:
    print(msg.value.decode("utf-8"))
    break
else:
    print("(ningún mensaje en %d s)" % (TIMEOUT_MS // 1000), file=sys.stderr)
    sys.exit(1)
consumer.close()
