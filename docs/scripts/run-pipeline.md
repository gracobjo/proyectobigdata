# Scripts de ejecución del pipeline

Orden: 00_start_hdfs (o start_stack) → 01_generate_data → 02_data_cleaning (dejar corriendo) → 03_delay_analysis (dejar corriendo) → 04_mongodb_consumer (dejar corriendo) → 05_verify_mongodb. Opcionales: 06_data_enrichment, 07_network_analysis, 08_import_bottlenecks. Entre cada paso esperar ~30 s. Ver scripts en `scripts/run/`.
