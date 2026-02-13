# Dataset de Logs GPS

Este directorio contiene ficheros de logs GPS en formato JSONL (JSON Lines) para ser procesados por NiFi.

## Formato

Cada línea del fichero es un objeto JSON independiente con la siguiente estructura:

```json
{"vehicle_id": "V001", "timestamp": "2026-02-12 17:00:00", "latitude": 40.7128, "longitude": -74.0060, "speed": 75.5, "route_id": "R001", "status": "IN_TRANSIT"}
```

## Generar Nuevos Datos

Para generar nuevos ficheros de ejemplo:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Generar 200 registros
python3 scripts/utils/generate_gps_log_file.py -n 200

# Generar en este directorio específico
python3 scripts/utils/generate_gps_log_file.py -n 500 -d /home/hadoop/data/gps_logs
```

## Usar en NiFi

1. Configura el procesador `GetFile` en NiFi:
   - **Input Directory**: `/home/hadoop/data/gps_logs`
   - **File Filter**: `.*\.jsonl?`
   - **Keep Source File**: `false` (mueve) o `true` (copia)

2. O usa `TailFile` para leer un fichero específico en tiempo real.

Ver **docs/guides/FUENTES_DATOS.md** para más información sobre las fuentes de datos.
