#!/usr/bin/env python3
"""
Script para simular un sensor IoT publicando datos GPS a MQTT.
Útil para probar la integración IoT sin hardware real.
"""
import json
import random
import time
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt

# Configuración MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_BASE = "vehicles"
VEHICLES = ['V001', 'V002', 'V003', 'V004', 'V005']
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

def generate_sensor_data(vehicle_id):
    """Genera datos GPS simulando un sensor real"""
    route_id = random.choice(ROUTES)
    status = random.choice(STATUSES)
    
    warehouse = random.choice(list(WAREHOUSES.keys()))
    base_lat, base_lon = WAREHOUSES[warehouse]
    
    latitude = base_lat + random.uniform(-0.1, 0.1)
    longitude = base_lon + random.uniform(-0.1, 0.1)
    
    if status == 'IN_TRANSIT':
        speed = random.uniform(50, 100)
    elif status in ['LOADING', 'UNLOADING']:
        speed = random.uniform(0, 5)
    else:
        speed = 0
    
    # Formato que un sensor real podría enviar
    return {
        "IMEI": f"1234567890{vehicle_id[-3:]}",  # IMEI simulado
        "timestamp": int(datetime.now().timestamp()),
        "lat": round(latitude, 6),
        "lng": round(longitude, 6),
        "speed": round(speed, 2),
        "heading": random.randint(0, 360),
        "altitude": random.uniform(0, 500),
        "satellites": random.randint(8, 15),
        "battery": random.randint(60, 100)
    }

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker"""
    if rc == 0:
        print(f"✓ Conectado al broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"✗ Error de conexión: código {rc}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simular sensor IoT publicando a MQTT")
    parser.add_argument("-v", "--vehicle", type=str, default=None,
                       help="ID del vehículo (default: aleatorio)")
    parser.add_argument("-i", "--interval", type=int, default=5,
                       help="Intervalo entre mensajes en segundos (default: 5)")
    parser.add_argument("-n", "--num-messages", type=int, default=None,
                       help="Número de mensajes a enviar (default: infinito)")
    parser.add_argument("-b", "--broker", type=str, default=MQTT_BROKER,
                       help=f"Broker MQTT (default: {MQTT_BROKER})")
    parser.add_argument("-p", "--port", type=int, default=MQTT_PORT,
                       help=f"Puerto MQTT (default: {MQTT_PORT})")
    
    args = parser.parse_args()
    
    # Seleccionar vehículo
    vehicle_id = args.vehicle if args.vehicle else random.choice(VEHICLES)
    topic = f"{MQTT_TOPIC_BASE}/{vehicle_id}/gps"
    
    print(f"=== Simulador de Sensor IoT ===")
    print(f"Vehículo: {vehicle_id}")
    print(f"Topic MQTT: {topic}")
    print(f"Broker: {args.broker}:{args.port}")
    print(f"Intervalo: {args.interval} segundos")
    print("")
    
    # Crear cliente MQTT
    client = mqtt.Client(client_id=f"sensor-{vehicle_id}")
    client.on_connect = on_connect
    
    try:
        # Conectar al broker
        client.connect(args.broker, args.port, 60)
        client.loop_start()
        
        # Esperar conexión
        time.sleep(1)
        
        count = 0
        while True:
            if args.num_messages and count >= args.num_messages:
                break
            
            # Generar y publicar datos
            data = generate_sensor_data(vehicle_id)
            payload = json.dumps(data)
            
            result = client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                count += 1
                print(f"[{count}] Publicado en {topic}: lat={data['lat']:.4f}, lng={data['lng']:.4f}, speed={data['speed']:.1f}")
            else:
                print(f"✗ Error al publicar: código {result.rc}")
            
            time.sleep(args.interval)
        
        client.loop_stop()
        client.disconnect()
        print(f"\n✓ Enviados {count} mensajes")
        
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nAsegúrate de que:")
        print("  1. El broker MQTT esté ejecutándose (mosquitto)")
        print("  2. El broker esté accesible en el host/puerto especificado")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
