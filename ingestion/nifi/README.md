# Configuración de Apache NiFi

## Descripción

Este directorio contiene las configuraciones y templates para los flujos de ingesta de datos en NiFi.

## Flujos de Datos

### 1. Ingesta de API de OpenWeather

- **Procesador**: InvokeHTTP
- **Frecuencia**: Cada 5 minutos
- **Destino**: Topic Kafka `raw-data`

### 2. Ingesta de API de FlightRadar24

- **Procesador**: InvokeHTTP
- **Frecuencia**: Cada 1 minuto
- **Destino**: Topic Kafka `raw-data`

### 3. Procesamiento de Logs GPS

- **Procesador**: GetFile / TailFile
- **Filtrado**: RouteOnAttribute
- **Destino**: Topic Kafka `filtered-data` y HDFS `/user/hadoop/raw`

## Template

Importar el template `transport_monitoring_template.xml` en NiFi para configurar automáticamente todos los flujos.

## Configuración Manual

1. Crear Process Group "Transport Monitoring"
2. Configurar procesadores según las especificaciones
3. Conectar con Kafka mediante PublishKafka processors
4. Configurar PutHDFS para almacenamiento raw

## Manejo de Erros

- Back-pressure configurado en todos los procesadores
- Retry automático en caso de fallos de conexión
- Alerta por email en caso de fallos críticos
