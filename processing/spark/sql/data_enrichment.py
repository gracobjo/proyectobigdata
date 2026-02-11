#!/usr/bin/env python3
"""
Fase II: Transformación - Enriquecimiento de Datos
Cruce de streaming de Kafka con datos maestros almacenados en Hive
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, current_timestamp, to_date
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType,
    IntegerType, DateType
)

# Rutas HDFS de tablas maestras (creadas por scripts/setup/create_tables_spark.py)
HDFS_BASE = "hdfs://localhost:9000/user/hive/warehouse"

def create_spark_session():
    """Crear sesión de Spark (localhost para standalone; sin Hive; evita bind a 192.168.56.1)"""
    return SparkSession.builder \
        .appName("DataEnrichment") \
        .config("spark.sql.warehouse.dir", f"{HDFS_BASE}") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

def enrich_transport_data(spark):
    """
    Enriquece los datos de transporte con información maestra
    """
    # Leer datos filtrados desde Kafka
    df_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("subscribe", "filtered-data") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    from pyspark.sql.functions import from_json

    # Esquemas para tablas maestras (evitan "Unable to infer schema" si el directorio está vacío o hay 0 ficheros)
    schema_routes = StructType([
        StructField("route_id", StringType(), True),
        StructField("route_name", StringType(), True),
        StructField("origin_city", StringType(), True),
        StructField("destination_city", StringType(), True),
        StructField("distance_km", DoubleType(), True),
        StructField("estimated_time_minutes", IntegerType(), True),
        StructField("created_at", TimestampType(), True),
    ])
    schema_vehicles = StructType([
        StructField("vehicle_id", StringType(), True),
        StructField("vehicle_type", StringType(), True),
        StructField("capacity", IntegerType(), True),
        StructField("company", StringType(), True),
        StructField("registration_date", DateType(), True),
        StructField("created_at", TimestampType(), True),
    ])
    schema = StructType([
        StructField("vehicle_id", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("speed", DoubleType(), True),
        StructField("route_id", StringType(), True),
        StructField("status", StringType(), True),
        StructField("cleaned_at", TimestampType(), True)
    ])
    
    df_parsed = df_stream.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")
    
    # Leer datos maestros desde HDFS (esquema explícito por si el directorio está vacío o Spark no infiere)
    routes_df = spark.read.schema(schema_routes).parquet(f"{HDFS_BASE}/master_routes") \
        .select("route_id", "route_name", "origin_city", "destination_city", "distance_km", "estimated_time_minutes")
    vehicles_df = spark.read.schema(schema_vehicles).parquet(f"{HDFS_BASE}/master_vehicles") \
        .select("vehicle_id", "vehicle_type", "capacity", "company", "registration_date")
    
    # Enriquecer con información de rutas y vehículos
    df_enriched = df_parsed \
        .join(routes_df, "route_id", "left") \
        .join(vehicles_df, "vehicle_id", "left")
    
    # Calcular campos derivados
    df_final = df_enriched \
        .withColumn("is_delayed", 
                   when(col("speed") < col("estimated_time_minutes") / 60.0 * 10, True)
                   .otherwise(False)) \
        .withColumn("enriched_at", current_timestamp()) \
        .withColumn("partition_date", to_date(col("timestamp")))
    
    # Escribir a HDFS para análisis posterior (partitionBy requiere nombres de columna)
    query = df_final \
        .writeStream \
        .trigger(processingTime="10 seconds") \
        .format("parquet") \
        .option("path", "hdfs://localhost:9000/user/hadoop/processed/enriched") \
        .option("checkpointLocation", "hdfs://localhost:9000/user/hadoop/checkpoints/enrichment") \
        .outputMode("append") \
        .partitionBy("route_id", "partition_date") \
        .start()
    
    query.awaitTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    enrich_transport_data(spark)
    spark.stop()
