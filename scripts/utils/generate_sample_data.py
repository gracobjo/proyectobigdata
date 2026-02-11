#!/usr/bin/env python3
"""
Script para generar datos de ejemplo simulando logs GPS
Útil para testing y desarrollo
"""

import json
import random
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer

# Configuración (127.0.0.1 para modo standalone; evita problemas con localhost→IPv6)
KAFKA_BOOTSTRAP_SERVERS = '127.0.0.1:9092'
KAFKA_TOPIC = 'raw-data'
NUM_MESSAGES = 1000
VEHICLES = ['V001', 'V002', 'V003', 'V004', 'V005', 'V006', 'V007', 'V008']
ROUTES = ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007']
STATUSES = ['IN_TRANSIT', 'LOADING', 'UNLOADING', 'MAINTENANCE']

# Coordenadas aproximadas de almacenes
WAREHOUSES = {
    'A': (40.7128, -74.0060),  # Almacen_Norte
    'B': (34.0522, -118.2437), # Almacen_Sur
    'C': (41.8781, -87.6298),  # Almacen_Este
    'D': (37.7749, -122.4194), # Almacen_Oeste
    'E': (39.9526, -75.1652),  # Almacen_Centro
}

def generate_gps_data():
    """Genera un mensaje de datos GPS simulado"""
    vehicle_id = random.choice(VEHICLES)
    route_id = random.choice(ROUTES)
    status = random.choice(STATUSES)
    
    # Generar coordenadas cerca de un almacén aleatorio
    warehouse = random.choice(list(WAREHOUSES.keys()))
    base_lat, base_lon = WAREHOUSES[warehouse]
    
    # Añadir variación aleatoria
    latitude = base_lat + random.uniform(-0.1, 0.1)
    longitude = base_lon + random.uniform(-0.1, 0.1)
    
    # Velocidad según estado
    if status == 'IN_TRANSIT':
        speed = random.uniform(50, 100)
    elif status in ['LOADING', 'UNLOADING']:
        speed = random.uniform(0, 5)
    else:
        speed = 0
    
    timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
    
    return {
        'vehicle_id': vehicle_id,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'latitude': round(latitude, 6),
        'longitude': round(longitude, 6),
        'speed': round(speed, 2),
        'route_id': route_id,
        'status': status
    }

def main(num_messages=None):
    """Función principal. num_messages: si se pasa, usa este valor en lugar de NUM_MESSAGES."""
    n = num_messages if num_messages is not None else NUM_MESSAGES
    print(f"Generando {n} mensajes de ejemplo...")
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        for i in range(n):
            data = generate_gps_data()
            producer.send(KAFKA_TOPIC, value=data)
            
            if (i + 1) % 100 == 0:
                print(f"Enviados {i + 1}/{n} mensajes...")
            
            time.sleep(0.1)  # Pequeña pausa para simular tiempo real
        
        producer.flush()
        print(f"\n✓ {n} mensajes enviados exitosamente a {KAFKA_TOPIC}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Asegúrate de que Kafka esté ejecutándose y el topic 'raw-data' exista")

if __name__ == '__main__':
    import sys
    n = None
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            pass
    main(num_messages=n)
