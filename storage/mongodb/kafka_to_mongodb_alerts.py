#!/usr/bin/env python3
"""
Consumidor Kafka → MongoDB: Persiste agregados de retrasos desde el topic 'alerts'
Escribe en la colección route_delay_aggregates de MongoDB
"""

import json
import sys
from datetime import datetime
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# Configuración (127.0.0.1 para standalone)
KAFKA_BOOTSTRAP = "127.0.0.1:9092"
KAFKA_TOPIC = "alerts"
MONGO_URI = "mongodb://127.0.0.1:27017/"
MONGO_DB = "transport_db"
MONGO_COLLECTION = "route_delay_aggregates"

def connect_mongodb():
    """Conectar a MongoDB y crear índices si no existen"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        
        # Crear índices según schema
        collection.create_index([("route_id", 1), ("window_start", -1)])
        print(f"✓ Conectado a MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
        return client, collection
    except ConnectionFailure as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        print("Asegúrate de que MongoDB esté ejecutándose: sudo systemctl status mongodb o docker ps | grep mongo")
        sys.exit(1)

def parse_alert_message(msg_value):
    """Parsear mensaje JSON del topic alerts"""
    try:
        data = json.loads(msg_value.decode('utf-8'))
        # Convertir timestamps ISO a datetime
        data['window_start'] = datetime.fromisoformat(data['window_start'].replace('Z', '+00:00'))
        data['window_end'] = datetime.fromisoformat(data['window_end'].replace('Z', '+00:00'))
        data['analysis_timestamp'] = datetime.fromisoformat(data['analysis_timestamp'].replace('Z', '+00:00'))
        return data
    except Exception as e:
        print(f"⚠ Error parseando mensaje: {e}")
        return None

def main():
    """Función principal: consumir alerts y escribir en MongoDB"""
    print("=== Consumidor Kafka → MongoDB (alerts) ===")
    print(f"Kafka: {KAFKA_BOOTSTRAP}, topic: {KAFKA_TOPIC}")
    print(f"MongoDB: {MONGO_URI}{MONGO_DB}.{MONGO_COLLECTION}\n")
    
    # Conectar a MongoDB
    mongo_client, collection = connect_mongodb()
    
    # Crear consumer de Kafka
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='mongodb-alerts-consumer',
            value_deserializer=lambda m: m
        )
        print(f"✓ Conectado a Kafka, consumiendo desde {KAFKA_TOPIC}\n")
    except Exception as e:
        print(f"❌ Error conectando a Kafka: {e}")
        print("Asegúrate de que Kafka esté ejecutándose: jps | grep Kafka")
        sys.exit(1)
    
    processed_count = 0
    error_count = 0
    
    try:
        for message in consumer:
            data = parse_alert_message(message.value)
            if not data:
                error_count += 1
                continue
            
            try:
                # Insertar documento en MongoDB
                # Usar route_id + window_start como clave única para evitar duplicados
                result = collection.update_one(
                    {
                        'route_id': data['route_id'],
                        'window_start': data['window_start']
                    },
                    {'$set': data},
                    upsert=True
                )
                
                if result.upserted_id:
                    print(f"✓ Insertado: {data['route_id']} @ {data['window_start']} ({data['total_vehicles']} vehículos, {data['delay_percentage']:.1f}% retraso)")
                else:
                    print(f"↻ Actualizado: {data['route_id']} @ {data['window_start']}")
                
                processed_count += 1
                
            except DuplicateKeyError:
                # Ya existe (aunque usamos upsert, puede pasar en concurrencia)
                print(f"⚠ Duplicado ignorado: {data['route_id']} @ {data['window_start']}")
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
