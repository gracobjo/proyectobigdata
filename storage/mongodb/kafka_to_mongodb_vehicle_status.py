#!/usr/bin/env python3
"""
Consumidor Kafka → MongoDB: Mantiene el último estado conocido de cada vehículo
Lee de 'filtered-data' y actualiza la colección vehicle_status en MongoDB
"""

import json
import sys
from datetime import datetime
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configuración (127.0.0.1 para standalone)
KAFKA_BOOTSTRAP = "127.0.0.1:9092"
KAFKA_TOPIC = "filtered-data"
MONGO_URI = "mongodb://127.0.0.1:27017/"
MONGO_DB = "transport_db"
MONGO_COLLECTION = "vehicle_status"

def connect_mongodb():
    """Conectar a MongoDB y crear índices si no existen"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        
        # Crear índices según schema
        collection.create_index([("vehicle_id", 1), ("timestamp", -1)])
        collection.create_index([("route_id", 1), ("timestamp", -1)])
        collection.create_index("status")
        collection.create_index("is_delayed")
        print(f"✓ Conectado a MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
        return client, collection
    except ConnectionFailure as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        print("Asegúrate de que MongoDB esté ejecutándose: sudo systemctl status mongodb o docker ps | grep mongo")
        sys.exit(1)

def parse_filtered_message(msg_value):
    """Parsear mensaje JSON del topic filtered-data"""
    try:
        data = json.loads(msg_value.decode('utf-8'))
        # Convertir timestamp string a datetime
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        if isinstance(data.get('cleaned_at'), str):
            data['cleaned_at'] = datetime.fromisoformat(data['cleaned_at'].replace('Z', '+00:00'))
        # Calcular is_delayed si no está (heurística: speed < 10)
        if 'is_delayed' not in data:
            data['is_delayed'] = data.get('speed', 0) < 10
        return data
    except Exception as e:
        print(f"⚠ Error parseando mensaje: {e}")
        return None

def enrich_with_master_data(data, routes_collection, vehicles_collection):
    """Enriquecer con datos maestros desde MongoDB (si existen)"""
    # Buscar ruta
    route = routes_collection.find_one({'route_id': data.get('route_id')})
    if route:
        data['route_name'] = route.get('route_name')
    
    # Buscar vehículo
    vehicle = vehicles_collection.find_one({'vehicle_id': data.get('vehicle_id')})
    if vehicle:
        data['vehicle_type'] = vehicle.get('vehicle_type')
        data['company'] = vehicle.get('company')
    
    return data

def main():
    """Función principal: consumir filtered-data y actualizar vehicle_status"""
    print("=== Consumidor Kafka → MongoDB (vehicle_status) ===")
    print(f"Kafka: {KAFKA_BOOTSTRAP}, topic: {KAFKA_TOPIC}")
    print(f"MongoDB: {MONGO_URI}{MONGO_DB}.{MONGO_COLLECTION}\n")
    
    # Conectar a MongoDB
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        mongo_client.server_info()
    except ConnectionFailure as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        sys.exit(1)
    
    db = mongo_client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    routes_collection = db.get_collection('master_routes')  # Opcional: si existen en MongoDB
    vehicles_collection = db.get_collection('master_vehicles')  # Opcional
    
    # Crear índices
    collection.create_index([("vehicle_id", 1), ("timestamp", -1)])
    collection.create_index([("route_id", 1), ("timestamp", -1)])
    collection.create_index("status")
    collection.create_index("is_delayed")
    
    # Crear consumer de Kafka
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            auto_offset_reset='latest',  # Solo nuevos mensajes
            enable_auto_commit=True,
            group_id='mongodb-vehicle-status-consumer',
            value_deserializer=lambda m: m
        )
        print(f"✓ Conectado a Kafka, consumiendo desde {KAFKA_TOPIC}\n")
    except Exception as e:
        print(f"❌ Error conectando a Kafka: {e}")
        sys.exit(1)
    
    processed_count = 0
    error_count = 0
    
    try:
        for message in consumer:
            data = parse_filtered_message(message.value)
            if not data:
                error_count += 1
                continue
            
            try:
                # Enriquecer con datos maestros (opcional)
                try:
                    data = enrich_with_master_data(data, routes_collection, vehicles_collection)
                except:
                    pass  # Si no hay tablas maestras en MongoDB, continuar sin enriquecer
                
                # Insertar documento (mantener histórico o solo último estado)
                # Opción: insertar siempre (histórico completo)
                collection.insert_one(data)
                
                # Opción alternativa: solo último estado (descomentar para usar)
                # collection.update_one(
                #     {'vehicle_id': data['vehicle_id']},
                #     {'$set': data},
                #     upsert=True
                # )
                
                if processed_count % 10 == 0:
                    print(f"✓ Procesados: {processed_count} | Último: {data.get('vehicle_id')} @ {data.get('timestamp')}")
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error insertando en MongoDB: {e}")
                error_count += 1
    
    except KeyboardInterrupt:
        print("\n\n=== Interrupción recibida ===")
    finally:
        consumer.close()
        mongo_client.close()
        print(f"\nTotal procesados: {processed_count}, Errores: {error_count}")

if __name__ == "__main__":
    main()
