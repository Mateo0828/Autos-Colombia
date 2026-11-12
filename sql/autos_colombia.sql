-- =========================================================
-- AUTOS COLOMBIA
-- Evidencia de Aprendizaje 1 - Iteración 1
-- Base de datos PostgreSQL
-- =========================================================

-- Permite volver a ejecutar el script desde cero.
DROP TABLE IF EXISTS sesion CASCADE;
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
-- Usuarios del sistema: ADMINISTRADOR u OPERADOR.
-- Se conserva esta tabla para mantener las relaciones
-- históricas de entrada y salida de las estancias.
-- =========================================================
CREATE TABLE operador (
    id_operador INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,
    rol VARCHAR(20) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_rol_operador
        CHECK (rol IN ('ADMINISTRADOR', 'OPERADOR')),

    CONSTRAINT chk_estado_operador
        CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);

-- =========================================================
-- TABLA SESION
-- Almacena las sesiones autenticadas de los usuarios.
-- El token original nunca se guarda; solo su hash.
-- =========================================================
CREATE TABLE sesion (
    id_sesion INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    id_operador INTEGER NOT NULL,
    creada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira TIMESTAMP NOT NULL,
    revocada BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_sesion_operador
        FOREIGN KEY (id_operador)
        REFERENCES operador(id_operador)
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
    estado VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE',

    CONSTRAINT chk_tipo_celda
        CHECK (tipo_celda IN ('MOTO', 'CARRO')),

    CONSTRAINT chk_estado_celda
    CHECK (
        estado IN (
            'DISPONIBLE',
            'OCUPADA',
            'FUERA_DE_SERVICIO'
        )
    )
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
    ),

    CONSTRAINT chk_cierre_estancia
        CHECK (
            (
                estado = 'ACTIVA'
                AND fecha_hora_salida IS NULL
                AND id_operador_salida IS NULL
            )
            OR
            (
                estado = 'FINALIZADA'
                AND fecha_hora_salida IS NOT NULL
                AND id_operador_salida IS NOT NULL
            )
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


INSERT INTO operador (
    nombre,
    usuario,
    rol,
    estado
)
VALUES
('Operador Mañana', 'operador1', 'OPERADOR', 'ACTIVO'),
('Operador Tarde', 'operador2', 'OPERADOR', 'ACTIVO'),
('Operador Noche', 'operador3', 'OPERADOR', 'ACTIVO'),
('Administrador Autos Colombia', 'admin', 'ADMINISTRADOR', 'ACTIVO');


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