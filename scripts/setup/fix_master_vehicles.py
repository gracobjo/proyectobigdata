#!/usr/bin/env python3
"""
Solo crea y rellena master_vehicles en HDFS.
Usar si create_tables_spark.py dejó master_routes con datos pero master_vehicles sin directorio.
"""

from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("FixMasterVehicles") \
        .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/user/hive/warehouse") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .getOrCreate()

    print("Creando tabla master_vehicles si no existe...")
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

    print("Insertando datos de vehículos...")
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

    print("Comprobando...")
    spark.sql("SELECT COUNT(*) as total FROM master_vehicles").show()
    spark.sql("SELECT * FROM master_vehicles").show(10, truncate=False)
    spark.stop()
    print("✓ master_vehicles listo.")

if __name__ == "__main__":
    main()
