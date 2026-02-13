# Fuentes de los flujos importables

Definiciones “en bruto” de los flows. **No** subas estos JSON a NiFi; les falta el formato que exige la importación en 2.7.

Para generar de nuevo los JSON importables desde aquí:

```bash
cd /home/hadoop/Documentos/ProyectoBigData/ingestion/nifi

# Flujo GPS
python3 fix_flow_property_descriptors.py source/gps_transport_flow_nifi27.json gps_transport_flow_importable.json

# Flujo completo (OpenWeather + FlightRadar24 + GPS)
python3 fix_flow_property_descriptors.py source/transport_monitoring_flow_nifi27.json transport_monitoring_flow_nifi27_importable.json
```

Los ficheros resultantes (`*_importable.json`) son los que debes usar en **Upload flow definition**.
