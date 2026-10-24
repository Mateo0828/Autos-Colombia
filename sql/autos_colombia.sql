-- =========================================================
-- AUTOS COLOMBIA
-- Evidencia de Aprendizaje 1 - Iteración 1
-- Base de datos PostgreSQL
-- =========================================================

-- Permite volver a ejecutar el script desde cero.
DROP TABLE IF EXISTS estancia CASCADE;
DROP TABLE IF EXISTS vehiculo CASCADE;
DROP TABLE IF EXISTS celda CASCADE;
DROP TABLE IF EXISTS operador CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;


-- =========================================================
-- TABLA CLIENTE
-- =========================================================
CREATE TABLE cliente (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL
);


-- =========================================================
-- TABLA OPERADOR
-- =========================================================
CREATE TABLE operador (
    id_operador INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);


-- =========================================================
-- TABLA VEHICULO
-- =========================================================
CREATE TABLE vehiculo (
    id_vehiculo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    marca VARCHAR(50) NOT NULL,
    color VARCHAR(30) NOT NULL,
    tipo_vehiculo VARCHAR(15) NOT NULL,
    estado_mensualidad VARCHAR(10) NOT NULL,
    id_cliente INTEGER NOT NULL,

    CONSTRAINT fk_vehiculo_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_cliente),

    CONSTRAINT chk_tipo_vehiculo
        CHECK (tipo_vehiculo IN ('MOTO', 'AUTOMOVIL', 'CAMIONETA')),

    CONSTRAINT chk_estado_mensualidad
        CHECK (estado_mensualidad IN ('ACTIVA', 'INACTIVA'))
);


-- =========================================================
-- TABLA CELDA
-- =========================================================
CREATE TABLE celda (
    id_celda INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    tipo_celda VARCHAR(10) NOT NULL,
    estado VARCHAR(12) NOT NULL DEFAULT 'DISPONIBLE',

    CONSTRAINT chk_tipo_celda
        CHECK (tipo_celda IN ('MOTO', 'CARRO')),

    CONSTRAINT chk_estado_celda
        CHECK (estado IN ('DISPONIBLE', 'OCUPADA'))
);


-- =========================================================
-- TABLA ESTANCIA
-- =========================================================
CREATE TABLE estancia (
    id_estancia INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_hora_entrada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_hora_salida TIMESTAMP NULL,
    estado VARCHAR(12) NOT NULL DEFAULT 'ACTIVA',

    id_vehiculo INTEGER NOT NULL,
    id_celda INTEGER NOT NULL,
    id_operador_entrada INTEGER NOT NULL,
    id_operador_salida INTEGER NULL,

    CONSTRAINT fk_estancia_vehiculo
        FOREIGN KEY (id_vehiculo)
        REFERENCES vehiculo(id_vehiculo),

    CONSTRAINT fk_estancia_celda
        FOREIGN KEY (id_celda)
        REFERENCES celda(id_celda),

    CONSTRAINT fk_estancia_operador_entrada
        FOREIGN KEY (id_operador_entrada)
        REFERENCES operador(id_operador),

    CONSTRAINT fk_estancia_operador_salida
        FOREIGN KEY (id_operador_salida)
        REFERENCES operador(id_operador),

    CONSTRAINT chk_estado_estancia
        CHECK (estado IN ('ACTIVA', 'FINALIZADA')),

    CONSTRAINT chk_fecha_salida
        CHECK (
            fecha_hora_salida IS NULL
            OR fecha_hora_salida >= fecha_hora_entrada
        )
);


-- =========================================================
-- REGLAS PARA ESTANCIAS ACTIVAS
-- =========================================================

-- Un vehículo no puede tener dos entradas activas simultáneamente.
CREATE UNIQUE INDEX uq_vehiculo_estancia_activa
ON estancia(id_vehiculo)
WHERE estado = 'ACTIVA';

-- Una celda no puede ser utilizada simultáneamente
-- por dos vehículos.
CREATE UNIQUE INDEX uq_celda_estancia_activa
ON estancia(id_celda)
WHERE estado = 'ACTIVA';


-- =========================================================
-- DATOS INICIALES PARA PRUEBAS
-- =========================================================

INSERT INTO cliente (documento, nombre)
VALUES
('1012345678', 'Carlos Rodriguez'),
('1023456789', 'Laura Martinez'),
('1034567890', 'Andres Gomez'),
('1045678901', 'Diana Lopez');


INSERT INTO operador (nombre)
VALUES
('Operador Mañana'),
('Operador Tarde'),
('Operador Noche');


INSERT INTO vehiculo
(placa, marca, color, tipo_vehiculo, estado_mensualidad, id_cliente)
VALUES
('ABC123', 'Renault', 'Blanco', 'AUTOMOVIL', 'ACTIVA', 1),
('DEF456', 'Mazda', 'Rojo', 'AUTOMOVIL', 'ACTIVA', 2),
('GHI789', 'Toyota', 'Gris', 'CAMIONETA', 'ACTIVA', 3),
('MOT01A', 'Yamaha', 'Negro', 'MOTO', 'ACTIVA', 4),
('JKL321', 'Chevrolet', 'Azul', 'AUTOMOVIL', 'INACTIVA', 1);


-- =========================================================
-- 70 CELDAS PARA CARROS/CAMIONETAS
-- =========================================================
INSERT INTO celda (codigo, tipo_celda, estado)
SELECT
    'C' || LPAD(numero::TEXT, 2, '0'),
    'CARRO',
    'DISPONIBLE'
FROM generate_series(1, 70) AS numero;


-- =========================================================
-- 10 CELDAS PARA MOTOCICLETAS
-- =========================================================
INSERT INTO celda (codigo, tipo_celda, estado)
SELECT
    'M' || LPAD(numero::TEXT, 2, '0'),
    'MOTO',
    'DISPONIBLE'
FROM generate_series(1, 10) AS numero;