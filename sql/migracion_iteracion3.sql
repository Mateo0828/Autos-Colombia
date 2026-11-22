
-- =========================================================
-- AUTOS COLOMBIA
-- Migración de Base de Datos
-- Iteración 2 -> Iteración 3
-- Gestión de pagos y mensualidades
-- =========================================================

-- Este script actualiza una base existente de la Iteración 2
-- conservando clientes, vehículos, usuarios, sesiones,
-- celdas y estancias.
--
-- No genera pagos históricos inexistentes.
-- Puede ejecutarse nuevamente sin eliminar los pagos
-- registrados ni duplicar estructuras.

BEGIN;


-- =========================================================
-- 1. AMPLIAR TABLA VEHICULO
-- =========================================================

ALTER TABLE vehiculo
ADD COLUMN IF NOT EXISTS fecha_inicio_mensualidad DATE;

ALTER TABLE vehiculo
ADD COLUMN IF NOT EXISTS fecha_corte DATE;


-- =========================================================
-- 2. ELIMINAR EL ESTADO MANUAL DE MENSUALIDAD
-- =========================================================

-- A partir de la Iteración 3, el estado de la mensualidad
-- se calcula desde la cobertura pagada y la fecha actual.
-- No podrá modificarse manualmente.

ALTER TABLE vehiculo
DROP CONSTRAINT IF EXISTS chk_estado_mensualidad;

ALTER TABLE vehiculo
DROP COLUMN IF EXISTS estado_mensualidad;


-- =========================================================
-- 3. INTEGRIDAD DE LAS FECHAS DE MENSUALIDAD
-- =========================================================

-- Un vehículo sin pagos debe tener ambas fechas en NULL.
-- Un vehículo con pagos debe tener ambas fechas definidas
-- y una fecha de corte posterior a la fecha de inicio.

ALTER TABLE vehiculo
DROP CONSTRAINT IF EXISTS chk_fechas_mensualidad;

ALTER TABLE vehiculo
ADD CONSTRAINT chk_fechas_mensualidad
    CHECK (
        (
            fecha_inicio_mensualidad IS NULL
            AND fecha_corte IS NULL
        )
        OR
        (
            fecha_inicio_mensualidad IS NOT NULL
            AND fecha_corte IS NOT NULL
            AND fecha_corte > fecha_inicio_mensualidad
        )
    );


-- =========================================================
-- 4. CREAR TABLA PAGO
-- =========================================================

CREATE TABLE IF NOT EXISTS pago (
    id_pago INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_vehiculo INTEGER NOT NULL,
    id_cliente INTEGER NOT NULL,
    id_operador INTEGER NOT NULL,

    valor NUMERIC(12,2) NOT NULL,

    fecha_pago DATE NOT NULL,

    fecha_registro TIMESTAMP NOT NULL
        DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota'),

    periodo_inicio DATE NOT NULL,
    periodo_fin DATE NOT NULL,

    CONSTRAINT fk_pago_vehiculo
        FOREIGN KEY (id_vehiculo)
        REFERENCES vehiculo(id_vehiculo),

    CONSTRAINT fk_pago_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_cliente),

    CONSTRAINT fk_pago_operador
        FOREIGN KEY (id_operador)
        REFERENCES operador(id_operador),

    CONSTRAINT uq_pago_vehiculo_periodo
        UNIQUE (id_vehiculo, periodo_inicio),

    CONSTRAINT chk_valor_pago
        CHECK (valor > 0),

    CONSTRAINT chk_periodo_pago
        CHECK (periodo_fin > periodo_inicio)
);


-- =========================================================
-- 5. CONFIRMAR MIGRACION
-- =========================================================

COMMIT;


-- =========================================================
-- FIN DE LA MIGRACION ITERACION 3
-- =========================================================
