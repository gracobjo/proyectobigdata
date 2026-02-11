// Diseño lógico de colecciones MongoDB para estado de vehículos y agregados de retrasos
// Este fichero sirve como documentación del modelo NoSQL para MongoDB.

// Base de datos recomendada
//   transport_db

// Colección: vehicle_status
// - Guarda el histórico (o al menos la última foto) del estado de cada vehículo.
// - Índices pensados para búsquedas por vehículo, ruta y retrasos.
/*
db.createCollection("vehicle_status");
db.vehicle_status.createIndex({ vehicle_id: 1, timestamp: -1 });
db.vehicle_status.createIndex({ route_id: 1, timestamp: -1 });
db.vehicle_status.createIndex({ status: 1 });
db.vehicle_status.createIndex({ is_delayed: 1 });

// Documento tipo:
{
  vehicle_id: "V001",
  timestamp: ISODate("2025-01-01T10:00:00Z"),
  latitude: 40.712800,
  longitude: -74.006000,
  speed: 80.5,
  route_id: "R001",
  route_name: "Ruta_Norte_Sur",
  status: "IN_TRANSIT",
  is_delayed: false,
  vehicle_type: "Camion",
  company: "TransporteXYZ"
}
*/

// Colección: route_delay_aggregates
// - Guarda las agregaciones por ventana de 15 minutos y ruta.
// - Pensada para dashboards y APIs de reporting rápido.
/*
db.createCollection("route_delay_aggregates");
db.route_delay_aggregates.createIndex({ route_id: 1, window_start: -1 });

// Documento tipo:
{
  route_id: "R001",
  route_name: "Ruta_Norte_Sur",
  window_start: ISODate("2025-01-01T10:00:00Z"),
  window_end: ISODate("2025-01-01T10:15:00Z"),
  total_vehicles: 125,
  avg_speed: 72.3,
  delayed_count: 15,
  delay_percentage: 12.0,
  max_speed: 102.5,
  min_speed: 40.0,
  analysis_timestamp: ISODate("2025-01-01T10:16:00Z")
}
*/

// Colección opcional: bottlenecks
// - Resumen de cuellos de botella detectados por análisis de grafos.
/*
db.createCollection("bottlenecks");
db.bottlenecks.createIndex({ node_id: 1 });

// Documento tipo:
{
  node_id: "A",
  node_name: "Almacen_Norte",
  degree: 4,
  pagerank: 0.12,
  detected_at: ISODate("2025-01-01T00:00:00Z")
}
*/
