#!/usr/bin/env python3
"""
Fase II: Transformación - Análisis de Grafos
Usa GraphFrames para modelar la red de transporte y calcular caminos más cortos
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when
from graphframes import GraphFrame

HDFS_WAREHOUSE = "hdfs://localhost:9000/user/hive/warehouse"

def create_spark_session():
    """Crear sesión de Spark con GraphFrames (localhost para standalone; evita bind a 192.168.56.1)"""
    # GraphFrames: --packages io.graphframes:graphframes-spark3_2.12:0.10.0 + PYSPARK_PYTHON=venv/bin/python
    return SparkSession.builder \
        .appName("NetworkAnalysis") \
        .config("spark.sql.warehouse.dir", HDFS_WAREHOUSE) \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

def create_transport_graph(spark):
    """
    Crea un grafo de la red de transporte
    Nodos: Almacenes/Ciudades
    Aristas: Rutas entre almacenes
    """
    # Crear vértices (nodos) - Almacenes/Ciudades
    vertices = spark.createDataFrame([
        ("A", "Almacen_Norte", 40.7128, -74.0060, "Norte"),
        ("B", "Almacen_Sur", 34.0522, -118.2437, "Sur"),
        ("C", "Almacen_Este", 41.8781, -87.6298, "Este"),
        ("D", "Almacen_Oeste", 37.7749, -122.4194, "Oeste"),
        ("E", "Almacen_Centro", 39.9526, -75.1652, "Centro")
    ], ["id", "name", "latitude", "longitude", "region"])
    
    # Crear aristas (rutas) - Conexiones entre almacenes
    edges = spark.createDataFrame([
        ("A", "B", "Ruta_AB", 2800.0, 45),  # distancia en km, tiempo en minutos
        ("A", "C", "Ruta_AC", 1200.0, 20),
        ("B", "D", "Ruta_BD", 560.0, 10),
        ("C", "E", "Ruta_CE", 800.0, 15),
        ("D", "E", "Ruta_DE", 4000.0, 60),
        ("A", "E", "Ruta_AE", 200.0, 5),
        ("B", "C", "Ruta_BC", 3000.0, 50)
    ], ["src", "dst", "route_id", "distance_km", "time_minutes"])
    
    # Crear GraphFrame
    graph = GraphFrame(vertices, edges)
    
    return graph

def analyze_network(graph, spark):
    """
    Realiza análisis de la red de transporte
    """
    print("=== Análisis de Red de Transporte ===\n")
    
    # 1. Calcular grados de los nodos (número de conexiones)
    print("1. Grados de los nodos:")
    degrees = graph.degrees
    degrees.show()
    
    # 2. Encontrar el camino más corto entre dos almacenes
    print("\n2. Camino más corto de A a D:")
    paths = graph.find("(a)-[e]->(b); (b)-[e2]->(c); (c)-[e3]->(d)") \
        .filter("a.id = 'A' AND d.id = 'D'")
    paths.show(truncate=False)
    
    # 3. Detectar comunidades críticas usando PageRank
    print("\n3. PageRank - Importancia de nodos:")
    page_rank = graph.pageRank(resetProbability=0.15, maxIter=10)
    page_rank.vertices.select("id", "name", "pagerank") \
        .orderBy(col("pagerank").desc()) \
        .show()
    
    # 4. Encontrar triángulos (rutas alternativas)
    print("\n4. Triángulos en la red:")
    triangles = graph.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)")
    print(f"Número de triángulos encontrados: {triangles.count()}")
    
    # 5. Motifs - Patrones de conexión
    print("\n5. Motifs - Patrones de conexión:")
    motifs = graph.find("(a)-[e1]->(b); (b)-[e2]->(c)")
    motifs.show(truncate=False)
    
    # Guardar resultados en HDFS (standalone sin Hive)
    page_rank.vertices.write.mode("overwrite").parquet(f"{HDFS_WAREHOUSE}/network_pagerank")
    degrees.write.mode("overwrite").parquet(f"{HDFS_WAREHOUSE}/network_degrees")
    
    return graph

def detect_bottlenecks(graph, spark):
    """
    Detecta cuellos de botella en la red
    """
    # Calcular betweenness centrality (nodos críticos)
    print("\n=== Detección de Cuellos de Botella ===")
    
    # Nodos con mayor número de conexiones pueden ser cuellos de botella
    degrees = graph.degrees
    bottlenecks = degrees.filter(col("degree") >= 3)
    
    print("Nodos potencialmente críticos (grado >= 3):")
    bottlenecks.show()
    
    # Guardar en HDFS
    bottlenecks.write.mode("overwrite").parquet(f"{HDFS_WAREHOUSE}/network_bottlenecks")

if __name__ == "__main__":
    spark = create_spark_session()
    
    # Crear grafo
    graph = create_transport_graph(spark)
    
    # Análisis de red
    analyze_network(graph, spark)
    
    # Detección de cuellos de botella
    detect_bottlenecks(graph, spark)
    
    spark.stop()
