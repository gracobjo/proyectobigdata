#!/usr/bin/env python3
"""
Fase III: Minería y Acción - Análisis de Retrasos en Tiempo Real
Implementa Structured Streaming para calcular medias de retrasos en ventanas de 15 minutos
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, window, avg, count, max as spark_max, min as spark_min,
    sum as spark_sum, current_timestamp, to_json, struct, when, lit, from_json
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, BooleanType

def create_spark_session():
    """Crear sesión de Spark (localhost para standalone; evita bind a 192.168.56.1)"""
    return SparkSession.builder \
        .appName("DelayAnalysis") \
        .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/user/hive/warehouse") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

def analyze_delays(spark):
    """
    Analiza retrasos en ventanas de tiempo de 15 minutos
    """
    # Leer desde Kafka 'filtered-data' (salida de data_cleaning; sin campos de enriquecimiento)
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("subscribe", "filtered-data") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Schema = salida de data_cleaning (filtered-data)
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
    
    # Parsear JSON; is_delayed heurístico (speed < 10), route_name/estimated_time_minutes nulos
    df_parsed = df.select(
        from_json(col("value").cast("string"), schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select("data.*", "kafka_timestamp") \
        .withColumn("is_delayed", when(col("speed") < 10, True).otherwise(False)) \
        .withColumn("route_name", lit(None).cast(StringType())) \
        .withColumn("estimated_time_minutes", lit(None).cast(DoubleType()))
    
    # Calcular métricas en ventanas de 15 minutos
    windowed_agg = df_parsed \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), "15 minutes"),
            col("route_id"),
            col("route_name")
        ) \
        .agg(
            count("*").alias("total_vehicles"),
            avg("speed").alias("avg_speed"),
            spark_sum(when(col("is_delayed") == True, 1).otherwise(0)).alias("delayed_count"),
            spark_max("speed").alias("max_speed"),
            spark_min("speed").alias("min_speed"),
            avg("estimated_time_minutes").alias("avg_estimated_time")
        ) \
        .withColumn("delay_percentage", 
                   when(col("total_vehicles") > 0, 
                        (col("delayed_count") / col("total_vehicles")) * 100).otherwise(None)) \
        .withColumn("analysis_timestamp", current_timestamp()) \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("route_id"),
            col("route_name"),
            col("total_vehicles"),
            col("avg_speed"),
            col("delayed_count"),
            col("delay_percentage"),
            col("max_speed"),
            col("min_speed"),
            col("analysis_timestamp")
        )
    
    # Escribir agregados a HDFS (sink Parquet solo admite outputMode append)
    query_hive = windowed_agg \
        .writeStream \
        .trigger(processingTime="10 seconds") \
        .outputMode("append") \
        .format("parquet") \
        .option("path", "hdfs://localhost:9000/user/hive/warehouse/delay_aggregates") \
        .option("checkpointLocation",
                "hdfs://localhost:9000/user/hadoop/checkpoints/delay_hive") \
        .partitionBy("route_id") \
        .start()
    
    # Publicar en Kafka (topic alerts) para servicios externos
    query_for_services = windowed_agg \
        .selectExpr("CAST(route_id AS STRING) AS key", 
                   "to_json(struct(*)) AS value") \
        .writeStream \
        .trigger(processingTime="10 seconds") \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("topic", "alerts") \
        .option("checkpointLocation",
                "hdfs://localhost:9000/user/hadoop/checkpoints/delay_kafka") \
        .outputMode("update") \
        .start()
    
    # Consola para debugging
    query_console = windowed_agg \
        .writeStream \
        .trigger(processingTime="10 seconds") \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .start()
    
    # Esperar terminación
    spark.streams.awaitAnyTermination()

def ensure_delay_aggregates_dir(spark):
    """El directorio de agregados se crea al escribir con writeStream (no se usa Hive en standalone)."""
    pass

if __name__ == "__main__":
    spark = create_spark_session()
    ensure_delay_aggregates_dir(spark)
    analyze_delays(spark)
    spark.stop()
