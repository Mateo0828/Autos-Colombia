-- =========================================================
-- AUTOS COLOMBIA
-- Migración de Base de Datos
-- Iteración 1 -> Iteración 2
-- =========================================================

-- Este script actualiza una base existente de la Iteración 1
-- sin eliminar clientes, vehículos, estancias ni celdas.
-- Puede ejecutarse nuevamente sin duplicar estructuras.


-- =========================================================
-- 1. AMPLIAR TABLA OPERADOR
-- =========================================================

ALTER TABLE operador
ADD COLUMN IF NOT EXISTS usuario VARCHAR(50);

ALTER TABLE operador
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

ALTER TABLE operador
ADD COLUMN IF NOT EXISTS rol VARCHAR(20);

ALTER TABLE operador
ADD COLUMN IF NOT EXISTS estado VARCHAR(10);

ALTER TABLE operador
ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP;


-- Completar información para operadores existentes de EA1.
UPDATE operador
SET usuario = CASE
    WHEN id_operador = 1 THEN 'operador1'
    WHEN id_operador = 2 THEN 'operador2'
    WHEN id_operador = 3 THEN 'operador3'
    ELSE 'operador_' || id_operador
END
WHERE usuario IS NULL;


UPDATE operador
SET usuario = LOWER(TRIM(usuario));


UPDATE operador
SET rol = 'OPERADOR'
WHERE rol IS NULL;


UPDATE operador
SET estado = 'ACTIVO'
WHERE estado IS NULL;


UPDATE operador
SET fecha_creacion = CURRENT_TIMESTAMP
WHERE fecha_creacion IS NULL;


-- Crear administrador inicial si todavía no existe.
INSERT INTO operador (
    nombre,
    usuario,
    password_hash,
    rol,
    estado,
    fecha_creacion
)
SELECT
    'Administrador Autos Colombia',
    'admin',
    NULL,
    'ADMINISTRADOR',
    'ACTIVO',
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1
    FROM operador
    WHERE usuario = 'admin'
);


-- Aplicar restricciones definitivas.
ALTER TABLE operador
ALTER COLUMN usuario SET NOT NULL;

ALTER TABLE operador
ALTER COLUMN rol SET NOT NULL;

ALTER TABLE operador
ALTER COLUMN estado SET NOT NULL;

ALTER TABLE operador
ALTER COLUMN estado SET DEFAULT 'ACTIVO';

ALTER TABLE operador
ALTER COLUMN fecha_creacion SET NOT NULL;

ALTER TABLE operador
ALTER COLUMN fecha_creacion SET DEFAULT CURRENT_TIMESTAMP;


ALTER TABLE operador
DROP CONSTRAINT IF EXISTS operador_usuario_key;

ALTER TABLE operador
ADD CONSTRAINT operador_usuario_key
    UNIQUE (usuario);


ALTER TABLE operador
DROP CONSTRAINT IF EXISTS chk_rol_operador;

ALTER TABLE operador
ADD CONSTRAINT chk_rol_operador
    CHECK (rol IN ('ADMINISTRADOR', 'OPERADOR'));


ALTER TABLE operador
DROP CONSTRAINT IF EXISTS chk_estado_operador;

ALTER TABLE operador
ADD CONSTRAINT chk_estado_operador
    CHECK (estado IN ('ACTIVO', 'INACTIVO'));


-- =========================================================
-- 2. CREAR TABLA SESION
-- =========================================================

CREATE TABLE IF NOT EXISTS sesion (
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
-- 3. AMPLIAR ESTADOS DE CELDA
-- =========================================================

ALTER TABLE celda
ALTER COLUMN estado TYPE VARCHAR(20);


ALTER TABLE celda
DROP CONSTRAINT IF EXISTS chk_estado_celda;


ALTER TABLE celda
ADD CONSTRAINT chk_estado_celda
    CHECK (
        estado IN (
            'DISPONIBLE',
            'OCUPADA',
            'FUERA_DE_SERVICIO'
        )
    );


-- =========================================================
-- FIN DE LA MIGRACIÓN ITERACIÓN 2
-- =========================================================