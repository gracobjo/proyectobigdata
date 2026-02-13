# Fuentes de Datos para Ingesta

Este documento explica de dónde obtener los datos para la ingesta en NiFi y cómo prepararlos.

**Para sensores IoT reales**: Ver **docs/guides/IOT_SENSORES.md** para integrar sensores reales mediante MQTT/HTTP.

## Resumen de Fuentes de Datos

| Fuente | Tipo | Método de Obtención | Procesador NiFi |
|--------|------|---------------------|-----------------|
| **OpenWeather** | API HTTP | Llamada HTTP directa | `InvokeHTTP` |
| **FlightRadar24** | API HTTP | Llamada HTTP directa | `InvokeHTTP` |
| **Logs GPS** | Fichero local | Generar con script o leer fichero | `GetFile` / `TailFile` |

---

## 1. Datos de OpenWeather (API HTTP)

### Cómo obtenerlos

**No necesitas un fichero**: NiFi consume directamente desde la API usando `InvokeHTTP`.

### Requisitos

1. **API Key de OpenWeather**:
   - Regístrate en https://openweathermap.org/api
   - Obtén tu API key gratuita
   - Configura la URL en NiFi: `https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid=<TU_API_KEY>&units=metric`

### Configuración en NiFi

- **Procesador**: `InvokeHTTP`
- **Remote URL**: `https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid=<TU_API_KEY>&units=metric`
- **Run Schedule**: 5 min (para no exceder límites gratuitos)

### Formato de datos

La API devuelve JSON con información meteorológica:
```json
{
  "coord": {"lon": -3.7, "lat": 40.4},
  "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
  "main": {"temp": 15.5, "feels_like": 14.2, "temp_min": 13.0, "temp_max": 18.0},
  "wind": {"speed": 2.5, "deg": 180},
  "dt": 1707746400,
  "name": "Madrid"
}
```

---

## 2. Datos de FlightRadar24 (API HTTP)

### Cómo obtenerlos

**No necesitas un fichero**: NiFi consume directamente desde la API usando `InvokeHTTP`.

### Requisitos

1. **API Key de FlightRadar24** (opcional, según endpoint):
   - Algunos endpoints son públicos
   - Para endpoints avanzados, regístrate en https://www.flightradar24.com/

### Configuración en NiFi

- **Procesador**: `InvokeHTTP`
- **Remote URL**: Depende del endpoint (ejemplo: `https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds=...`)
- **Run Schedule**: 1-5 min según límites

### Nota

FlightRadar24 puede requerir autenticación o tener límites de uso. Consulta su documentación oficial.

---

## 3. Logs GPS (Ficheros Locales)

### Cómo obtenerlos

**Necesitas generar o tener ficheros** con logs GPS en formato JSON o JSONL.

### Opción A: Generar datos de ejemplo con script

El proyecto incluye un script para generar logs GPS simulados:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Generar 100 registros (default)
python3 scripts/utils/generate_gps_log_file.py

# Generar número específico de registros
python3 scripts/utils/generate_gps_log_file.py -n 500

# Especificar directorio de salida
python3 scripts/utils/generate_gps_log_file.py -n 200 -d /home/hadoop/data/gps_logs

# Especificar fichero de salida completo
python3 scripts/utils/generate_gps_log_file.py -n 100 -o /home/hadoop/data/gps_logs/mi_archivo.jsonl
```

**Ubicación por defecto**: `/home/hadoop/data/gps_logs/`

**Formato**: JSONL (JSON Lines) - un objeto JSON por línea

### Opción B: Usar datos reales

Si tienes logs GPS reales, asegúrate de que estén en formato JSON o JSONL con la siguiente estructura:

```json
{"vehicle_id": "V001", "timestamp": "2026-02-12 17:00:00", "latitude": 40.7128, "longitude": -74.0060, "speed": 75.5, "route_id": "R001", "status": "IN_TRANSIT"}
{"vehicle_id": "V002", "timestamp": "2026-02-12 17:01:00", "latitude": 34.0522, "longitude": -118.2437, "speed": 0.0, "route_id": "R002", "status": "LOADING"}
```

### Opción C: Dataset de ejemplo pre-generado

Puedes usar el dataset de ejemplo incluido en el proyecto:

```bash
# El script genera automáticamente en:
ls -lh /home/hadoop/data/gps_logs/
```

### Configuración en NiFi

**Procesador**: `GetFile` (para leer ficheros completos) o `TailFile` (para leer logs en tiempo real)

**Propiedades GetFile**:
- **Input Directory**: `/home/hadoop/data/gps_logs`
- **File Filter**: `.*\.jsonl?` (archivos `.json` o `.jsonl`)
- **Keep Source File**: `false` (mueve) o `true` (copia)
- **Run Schedule**: 5 secs

**Propiedades TailFile**:
- **File to Tail**: `/home/hadoop/data/gps_logs/gps_logs_20260212_171628.jsonl`
- **Run Schedule**: 1 sec

---

## Estructura de Datos GPS

### Campos requeridos

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `vehicle_id` | string | Identificador del vehículo | `"V001"` |
| `timestamp` | string | Fecha y hora (formato: `YYYY-MM-DD HH:MM:SS`) | `"2026-02-12 17:00:00"` |
| `latitude` | float | Latitud GPS | `40.7128` |
| `longitude` | float | Longitud GPS | `-74.0060` |
| `speed` | float | Velocidad en km/h | `75.5` |
| `route_id` | string | Identificador de ruta | `"R001"` |
| `status` | string | Estado del vehículo | `"IN_TRANSIT"`, `"LOADING"`, `"UNLOADING"`, `"MAINTENANCE"` |

### Valores válidos

- **vehicle_id**: `V001` a `V008` (en datos de ejemplo)
- **route_id**: `R001` a `R007` (en datos de ejemplo)
- **status**: `IN_TRANSIT`, `LOADING`, `UNLOADING`, `MAINTENANCE`

---

## Preparar el Entorno para NiFi

### 1. Crear directorio para logs GPS

```bash
mkdir -p /home/hadoop/data/gps_logs
chmod 755 /home/hadoop/data/gps_logs
```

### 2. Generar dataset de ejemplo

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

# Generar 200 registros de ejemplo
python3 scripts/utils/generate_gps_log_file.py -n 200
```

### 3. Verificar que el fichero se creó

```bash
ls -lh /home/hadoop/data/gps_logs/
head -3 /home/hadoop/data/gps_logs/*.jsonl
```

### 4. Configurar NiFi

1. Abre NiFi: https://localhost:8443/nifi
2. Importa el flujo desde `ingestion/nifi/transport_monitoring_flow.json`
3. Configura el procesador `GetFile`:
   - **Input Directory**: `/home/hadoop/data/gps_logs`
   - **File Filter**: `.*\.jsonl?`
4. Habilita los procesadores

---

## Generación Continua de Datos

Para mantener un flujo continuo de datos durante pruebas:

### Opción 1: Script periódico

```bash
# Ejecutar cada 5 minutos (ajusta según necesites)
watch -n 300 "python3 /home/hadoop/Documentos/ProyectoBigData/scripts/utils/generate_gps_log_file.py -n 50"
```

### Opción 2: DAG de Airflow

El proyecto incluye el DAG `simulation_data_stream` que genera datos cada 15 minutos automáticamente (envía a Kafka directamente).

### Opción 3: Generar múltiples ficheros

```bash
# Generar varios ficheros para simular múltiples fuentes
for i in {1..10}; do
  python3 scripts/utils/generate_gps_log_file.py -n 100 -o /home/hadoop/data/gps_logs/batch_${i}.jsonl
  sleep 10
done
```

---

## Referencias

- **Guía de NiFi**: `docs/guides/NIFI_FLUJOS.md`
- **Script de generación**: `scripts/utils/generate_gps_log_file.py`
- **Script para Kafka**: `scripts/utils/generate_sample_data.py` (envía directamente a Kafka)
