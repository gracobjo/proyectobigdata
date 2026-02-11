-- Datos maestros de ejemplo para el proyecto
-- Insertar en Hive después de crear las tablas

USE default;

-- Insertar datos maestros de rutas
INSERT INTO master_routes VALUES
('R001', 'Ruta_Norte_Sur', 'Almacen_Norte', 'Almacen_Sur', 2800.0, 45, CURRENT_TIMESTAMP()),
('R002', 'Ruta_Norte_Este', 'Almacen_Norte', 'Almacen_Este', 1200.0, 20, CURRENT_TIMESTAMP()),
('R003', 'Ruta_Sur_Oeste', 'Almacen_Sur', 'Almacen_Oeste', 560.0, 10, CURRENT_TIMESTAMP()),
('R004', 'Ruta_Este_Centro', 'Almacen_Este', 'Almacen_Centro', 800.0, 15, CURRENT_TIMESTAMP()),
('R005', 'Ruta_Oeste_Centro', 'Almacen_Oeste', 'Almacen_Centro', 4000.0, 60, CURRENT_TIMESTAMP()),
('R006', 'Ruta_Norte_Centro', 'Almacen_Norte', 'Almacen_Centro', 200.0, 5, CURRENT_TIMESTAMP()),
('R007', 'Ruta_Sur_Este', 'Almacen_Sur', 'Almacen_Este', 3000.0, 50, CURRENT_TIMESTAMP());

-- Insertar datos maestros de vehículos
INSERT INTO master_vehicles VALUES
('V001', 'Camion', 20, 'TransporteXYZ', '2020-01-15', CURRENT_TIMESTAMP()),
('V002', 'Furgoneta', 5, 'TransporteXYZ', '2021-03-20', CURRENT_TIMESTAMP()),
('V003', 'Camion', 25, 'LogisticaABC', '2019-11-10', CURRENT_TIMESTAMP()),
('V004', 'Furgoneta', 8, 'LogisticaABC', '2022-05-12', CURRENT_TIMESTAMP()),
('V005', 'Camion', 30, 'TransporteXYZ', '2020-08-25', CURRENT_TIMESTAMP()),
('V006', 'Furgoneta', 6, 'LogisticaABC', '2021-12-01', CURRENT_TIMESTAMP()),
('V007', 'Camion', 22, 'TransporteXYZ', '2019-06-18', CURRENT_TIMESTAMP()),
('V008', 'Furgoneta', 7, 'LogisticaABC', '2022-02-14', CURRENT_TIMESTAMP());
