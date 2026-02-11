#!/usr/bin/env python3
"""
Script para crear tablas maestras usando Spark SQL directamente
Esto funciona sin necesidad de Hive Metastore completamente configurado
"""

from pyspark.sql import SparkSession

def create_spark_session():
    """Crear sesión de Spark sin Hive (usa catálogo interno de Spark).
    Forzamos 127.0.0.1 para evitar que la Spark UI intente bind a 192.168.56.1 (nodo1 en /etc/hosts).
    """
    return SparkSession.builder \
        .appName("CreateMasterTables") \
        .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/user/hive/warehouse") \
        .config("spark.hadoop.dfs.replication", "1") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .getOrCreate()

def create_tables(spark):
    """Crear tablas maestras"""
    print("=== Creando Tablas Maestras ===")
    
    # Crear tabla master_routes
    print("\n1. Creando tabla master_routes...")
    spark.sql("""
        CREATE TABLE IF NOT EXISTS master_routes (
            route_id STRING,
            route_name STRING,
            origin_city STRING,
            destination_city STRING,
            distance_km DOUBLE,
            estimated_time_minutes INT,
            created_at TIMESTAMP
        ) USING PARQUET
        LOCATION 'hdfs://localhost:9000/user/hive/warehouse/master_routes'
    """)
    
    # Crear tabla master_vehicles
    print("2. Creando tabla master_vehicles...")
    spark.sql("""
        CREATE TABLE IF NOT EXISTS master_vehicles (
            vehicle_id STRING,
            vehicle_type STRING,
            capacity INT,
            company STRING,
            registration_date DATE,
            created_at TIMESTAMP
        ) USING PARQUET
        LOCATION 'hdfs://localhost:9000/user/hive/warehouse/master_vehicles'
    """)
    
    print("\n✓ Tablas creadas exitosamente")

def insert_data(spark):
    """Insertar datos maestros"""
    print("\n=== Insertando Datos Maestros ===")
    
    # Insertar rutas
    print("\n1. Insertando rutas...")
    spark.sql("""
        INSERT INTO master_routes VALUES
        ('R001', 'Ruta_Norte_Sur', 'Almacen_Norte', 'Almacen_Sur', 2800.0, 45, CURRENT_TIMESTAMP()),
        ('R002', 'Ruta_Norte_Este', 'Almacen_Norte', 'Almacen_Este', 1200.0, 20, CURRENT_TIMESTAMP()),
        ('R003', 'Ruta_Sur_Oeste', 'Almacen_Sur', 'Almacen_Oeste', 560.0, 10, CURRENT_TIMESTAMP()),
        ('R004', 'Ruta_Este_Centro', 'Almacen_Este', 'Almacen_Centro', 800.0, 15, CURRENT_TIMESTAMP()),
        ('R005', 'Ruta_Oeste_Centro', 'Almacen_Oeste', 'Almacen_Centro', 4000.0, 60, CURRENT_TIMESTAMP()),
        ('R006', 'Ruta_Norte_Centro', 'Almacen_Norte', 'Almacen_Centro', 200.0, 5, CURRENT_TIMESTAMP()),
        ('R007', 'Ruta_Sur_Este', 'Almacen_Sur', 'Almacen_Este', 3000.0, 50, CURRENT_TIMESTAMP())
    """)
    
    # Insertar vehículos
    print("2. Insertando vehículos...")
    spark.sql("""
        INSERT INTO master_vehicles VALUES
        ('V001', 'Camion', 20, 'TransporteXYZ', DATE '2020-01-15', CURRENT_TIMESTAMP()),
        ('V002', 'Furgoneta', 5, 'TransporteXYZ', DATE '2021-03-20', CURRENT_TIMESTAMP()),
        ('V003', 'Camion', 25, 'LogisticaABC', DATE '2019-11-10', CURRENT_TIMESTAMP()),
        ('V004', 'Furgoneta', 8, 'LogisticaABC', DATE '2022-05-12', CURRENT_TIMESTAMP()),
        ('V005', 'Camion', 30, 'TransporteXYZ', DATE '2020-08-25', CURRENT_TIMESTAMP()),
        ('V006', 'Furgoneta', 6, 'LogisticaABC', DATE '2021-12-01', CURRENT_TIMESTAMP()),
        ('V007', 'Camion', 22, 'TransporteXYZ', DATE '2019-06-18', CURRENT_TIMESTAMP()),
        ('V008', 'Furgoneta', 7, 'LogisticaABC', DATE '2022-02-14', CURRENT_TIMESTAMP())
    """)
    
    print("\n✓ Datos insertados exitosamente")

def verify_data(spark):
    """Verificar datos insertados"""
    print("\n=== Verificando Datos ===")
    
    print("\nRutas:")
    spark.sql("SELECT * FROM master_routes").show()
    
    print("\nVehículos:")
    spark.sql("SELECT * FROM master_vehicles").show()
    
    print("\nConteos:")
    spark.sql("SELECT COUNT(*) as total_routes FROM master_routes").show()
    spark.sql("SELECT COUNT(*) as total_vehicles FROM master_vehicles").show()

if __name__ == "__main__":
    spark = create_spark_session()
    
    try:
        create_tables(spark)
        insert_data(spark)
        verify_data(spark)
        print("\n✅ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()
