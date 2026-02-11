#!/usr/bin/env python3
"""
Importa resultados de análisis de grafos (bottlenecks) desde HDFS a MongoDB
Lee los Parquet de network_bottlenecks y los escribe en MongoDB
"""

import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pyspark.sql import SparkSession

# Configuración
MONGO_URI = "mongodb://127.0.0.1:27017/"
MONGO_DB = "transport_db"
MONGO_COLLECTION = "bottlenecks"
HDFS_BOTTLENECKS_PATH = "hdfs://localhost:9000/user/hive/warehouse/network_bottlenecks"

def create_spark_session():
    """Crear sesión de Spark"""
    return SparkSession.builder \
        .appName("ImportBottlenecksToMongoDB") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .getOrCreate()

def main():
    """Leer bottlenecks desde HDFS y escribir en MongoDB"""
    print("=== Importar Bottlenecks a MongoDB ===")
    print(f"HDFS: {HDFS_BOTTLENECKS_PATH}")
    print(f"MongoDB: {MONGO_URI}{MONGO_DB}.{MONGO_COLLECTION}\n")
    
    # Conectar a MongoDB
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        db = mongo_client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        collection.create_index("node_id")
        print("✓ Conectado a MongoDB\n")
    except ConnectionFailure as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        sys.exit(1)
    
    # Leer desde HDFS con Spark
    spark = create_spark_session()
    try:
        df = spark.read.parquet(HDFS_BOTTLENECKS_PATH)
        print(f"✓ Leídos {df.count()} registros desde HDFS\n")
        
        # Convertir a lista de diccionarios
        rows = df.collect()
        
        # Insertar en MongoDB
        from datetime import datetime
        documents = []
        for row in rows:
            doc = {
                'node_id': row['id'] if 'id' in row else row.get('node_id', ''),
                'node_name': row.get('name', ''),
                'degree': int(row.get('degree', 0)),
                'detected_at': datetime.now()
            }
            documents.append(doc)
        
        if documents:
            # Limpiar colección antes de insertar (o usar upsert)
            collection.delete_many({})
            result = collection.insert_many(documents)
            print(f"✓ Insertados {len(result.inserted_ids)} bottlenecks en MongoDB")
            
            # Mostrar algunos
            for doc in documents[:5]:
                print(f"  - {doc['node_id']}: grado {doc['degree']}")
        else:
            print("⚠ No hay datos para insertar")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()
        mongo_client.close()

if __name__ == "__main__":
    main()
