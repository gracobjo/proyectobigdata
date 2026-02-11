#!/usr/bin/env python3
"""
Script para verificar datos en MongoDB
Uso: python storage/mongodb/verify_data.py
"""
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://127.0.0.1:27017/"
MONGO_DB = "transport_db"

def main():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[MONGO_DB]
        
        print("=== Verificación de datos en MongoDB ===\n")
        
        # Verificar route_delay_aggregates
        collection_alerts = db['route_delay_aggregates']
        count_alerts = collection_alerts.count_documents({})
        print(f"📊 route_delay_aggregates: {count_alerts} documentos")
        
        if count_alerts > 0:
            print("\nÚltimos 5 documentos:")
            for doc in collection_alerts.find().sort("window_start", -1).limit(5):
                print(f"  - Ruta: {doc.get('route_id')}, Ventana: {doc.get('window_start')}, "
                      f"Retraso: {doc.get('delay_percentage', 0):.1f}%, "
                      f"Vehículos: {doc.get('total_vehicles', 0)}")
            
            # Estadísticas
            pipeline = [
                {"$group": {
                    "_id": "$route_id",
                    "avg_delay": {"$avg": "$delay_percentage"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"avg_delay": -1}}
            ]
            print("\nPromedio de retraso por ruta:")
            for stat in collection_alerts.aggregate(pipeline):
                print(f"  - {stat['_id']}: {stat['avg_delay']:.1f}% (ventanas: {stat['count']})")
        else:
            print("  ⚠ No hay datos aún. Ejecuta delay_analysis.py para generar agregados.")
        
        # Verificar vehicle_status
        collection_vehicles = db['vehicle_status']
        count_vehicles = collection_vehicles.count_documents({})
        print(f"\n🚗 vehicle_status: {count_vehicles} documentos")
        
        if count_vehicles > 0:
            delayed = collection_vehicles.count_documents({"is_delayed": True})
            print(f"  - Vehículos en retraso: {delayed}")
        
        # Verificar bottlenecks
        collection_bottlenecks = db['bottlenecks']
        count_bottlenecks = collection_bottlenecks.count_documents({})
        print(f"\n🔗 bottlenecks: {count_bottlenecks} documentos")
        
        if count_bottlenecks > 0:
            print("  Top 5 bottlenecks (por grado):")
            for doc in collection_bottlenecks.find().sort("degree", -1).limit(5):
                print(f"  - {doc.get('node_id', 'N/A')}: grado {doc.get('degree', 0)}")
        
        print("\n✓ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Asegúrate de que MongoDB esté ejecutándose")

if __name__ == "__main__":
    main()
