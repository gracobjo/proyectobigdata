#!/usr/bin/env python3
"""
Fase II: Preprocesamiento - Limpieza de Datos
Script Spark SQL para normalizar formatos, gestionar nulos y eliminar duplicados
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, isnan, isnull, trim, upper, 
    to_timestamp, current_timestamp, coalesce
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

def create_spark_session():
    """Crear sesión de Spark (localhost para standalone; evita bind a 192.168.56.1)"""
    return SparkSession.builder \
        .appName("DataCleaning") \
        .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/user/hive/warehouse") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

def clean_transport_data(spark):
    """
    Limpia los datos de transporte desde Kafka/HDFS
    """
    # Leer datos desde Kafka topic 'raw-data'
    # failOnDataLoss=false: si el topic se reinició (p. ej. tras formatear Kafka), no fallar por offsets antiguos
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("subscribe", "raw-data") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Definir schema esperado
    schema = StructType([
        StructField("vehicle_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("speed", DoubleType(), True),
        StructField("route_id", StringType(), True),
        StructField("status", StringType(), True)
    ])
    
    # Parsear JSON y aplicar schema
    from pyspark.sql.functions import from_json
    df_parsed = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")
    
    # Limpieza de datos
    df_cleaned = df_parsed \
        .withColumn("vehicle_id", trim(upper(col("vehicle_id")))) \
        .withColumn("route_id", trim(upper(col("route_id")))) \
        .withColumn("status", trim(upper(col("status")))) \
        .withColumn("timestamp", 
                   to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("latitude", 
                   when((col("latitude") >= -90) & (col("latitude") <= 90), col("latitude"))
                   .otherwise(None)) \
        .withColumn("longitude", 
                   when((col("longitude") >= -180) & (col("longitude") <= 180), col("longitude"))
                   .otherwise(None)) \
        .withColumn("speed", 
                   when((col("speed") >= 0) & (col("speed") <= 200), col("speed"))
                   .otherwise(None)) \
        .withColumn("cleaned_at", current_timestamp()) \
        .dropDuplicates(["vehicle_id", "timestamp"]) \
        .filter(col("vehicle_id").isNotNull()) \
        .filter(col("timestamp").isNotNull())
    
    # Escribir a Kafka topic 'filtered-data'
    # trigger(processingTime='5 seconds'): ejecutar batch cada 5s para no depender solo del default
    query = df_cleaned \
        .selectExpr("CAST(vehicle_id AS STRING) AS key", 
                   "to_json(struct(*)) AS value") \
        .writeStream \
        .trigger(processingTime="10 seconds") \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("topic", "filtered-data") \
        .option("checkpointLocation", "hdfs://localhost:9000/user/hadoop/checkpoints/cleaning") \
        .outputMode("append") \
        .start()
    
    query.awaitTermination()

if __name__ == "__main__":
    spark = create_spark_session()
    clean_transport_data(spark)
    spark.stop()
