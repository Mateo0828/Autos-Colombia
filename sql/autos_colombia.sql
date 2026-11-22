
-- =========================================================
-- AUTOS COLOMBIA
-- Evidencias de Aprendizaje 1, 2 y 3
-- Base de datos PostgreSQL
-- =========================================================
-- Iteración 1: Entrada y salida de vehículos.
-- Iteración 2: Gestión de usuarios y celdas.
-- Iteración 3: Gestión de pagos y mensualidades.
-- =========================================================

-- ADVERTENCIA:
-- Este script reconstruye la base de datos desde cero.
-- Para conservar datos existentes de EA2, utilizar
-- migracion_iteracion3.sql.

BEGIN;


-- =========================================================
-- ELIMINAR TABLAS EXISTENTES
-- =========================================================

DROP TABLE IF EXISTS pago CASCADE;
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
-- Conserva el historial de las operaciones realizadas.
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
-- Ampliada en la Iteración 3.
--
-- La vigencia de la mensualidad se calcula a partir
-- de las fechas de cobertura, no de un estado manual.
-- =========================================================

CREATE TABLE vehiculo (
    id_vehiculo INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    marca VARCHAR(50) NOT NULL,
    color VARCHAR(30) NOT NULL,
    tipo_vehiculo VARCHAR(15) NOT NULL,

    fecha_inicio_mensualidad DATE NULL,
    fecha_corte DATE NULL,

    id_cliente INTEGER NOT NULL,

    CONSTRAINT fk_vehiculo_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES cliente(id_cliente),

    CONSTRAINT chk_tipo_vehiculo
        CHECK (
            tipo_vehiculo IN (
                'MOTO',
                'AUTOMOVIL',
                'CAMIONETA'
            )
        ),

    CONSTRAINT chk_fechas_mensualidad
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
        )
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
-- Conserva las restricciones de EA1 y EA2.
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
-- TABLA PAGO
-- Incorporada en la Iteración 3.
-- Cada pago corresponde a un vehículo y un período mensual.
-- =========================================================

CREATE TABLE pago (
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
-- REGLAS PARA ESTANCIAS ACTIVAS
-- =========================================================

-- Un vehículo no puede tener dos entradas activas
-- simultáneamente.

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

-- CLIENTES

INSERT INTO cliente (documento, nombre)
VALUES
('1012345678', 'Carlos Rodriguez'),
('1023456789', 'Laura Martinez'),
('1034567890', 'Andres Gomez'),
('1045678901', 'Diana Lopez');


-- USUARIOS

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


-- VEHICULOS
-- Se conservan los vehículos originales.
-- Las coberturas de demostración se incorporarán
-- mediante registros de pago coherentes.

INSERT INTO vehiculo (
    placa,
    marca,
    color,
    tipo_vehiculo,
    id_cliente
)
VALUES
('ABC123', 'Renault', 'Blanco', 'AUTOMOVIL', 1),
('DEF456', 'Mazda', 'Rojo', 'AUTOMOVIL', 2),
('GHI789', 'Toyota', 'Gris', 'CAMIONETA', 3),
('MOT01A', 'Yamaha', 'Negro', 'MOTO', 4),
('JKL321', 'Chevrolet', 'Azul', 'AUTOMOVIL', 1);


-- =========================================================
-- DATOS DE DEMOSTRACION DE LA ITERACION 3
-- Gestión de pagos y mensualidades.
-- RNF-I3-12: fechas relativas a la fecha actual.
-- =========================================================

-- Vehículos adicionales para probar el primer pago
-- y el límite de vigencia de la mensualidad.

INSERT INTO vehiculo (
    placa,
    marca,
    color,
    tipo_vehiculo,
    id_cliente
)
VALUES
('XYZ987', 'Mazda', 'Gris', 'AUTOMOVIL', 2),
('MOT02A', 'Honda', 'Negro', 'MOTO', 4),
('COR001', 'Nissan', 'Blanco', 'AUTOMOVIL', 3);


-- =========================================================
-- GENERAR PAGOS DE DEMOSTRACION
-- =========================================================

-- Las fechas se calculan utilizando la fecha local
-- de Colombia en el momento de ejecutar el script.
--
-- Cada período se calcula desde la fecha inicial
-- de la mensualidad, conservando el día de corte.
--
-- Los vehículos XYZ987 y MOT02A no reciben pagos
-- iniciales para permitir probar esa funcionalidad.

WITH referencia AS (
    SELECT
        (CURRENT_TIMESTAMP AT TIME ZONE
            'America/Bogota')::DATE AS hoy
),

-- Determinar una fecha inicial que permita obtener
-- exactamente un corte igual a la fecha actual.
--
-- En meses cortos puede ser necesario utilizar dos
-- períodos para conservar correctamente el día original.

limite AS (
    SELECT
        hoy,
        CASE
            WHEN (
                (hoy - INTERVAL '1 month')
                + INTERVAL '1 month'
            )::DATE = hoy
            THEN 1
            ELSE 2
        END AS cantidad
    FROM referencia
),

-- Definir los escenarios iniciales de demostración.

planes AS (
    SELECT
        'ABC123' AS placa,
        hoy - 10 AS fecha_inicio,
        1 AS cantidad_pagos
    FROM referencia

    UNION ALL

    SELECT
        'DEF456',
        hoy - 25,
        1
    FROM referencia

    UNION ALL

    SELECT
        'GHI789',
        hoy - 15,
        1
    FROM referencia

    UNION ALL

    SELECT
        'MOT01A',
        hoy - 12,
        1
    FROM referencia

    UNION ALL

    SELECT
        'JKL321',
        hoy - 35,
        1
    FROM referencia

    UNION ALL

    SELECT
        'COR001',
        (
            hoy - make_interval(months => cantidad)
        )::DATE,
        cantidad
    FROM limite
),

-- Generar períodos mensuales utilizando siempre
-- la fecha de inicio como referencia.

periodos AS (
    SELECT
        p.placa,

        (
            p.fecha_inicio
            + make_interval(months => n)
        )::DATE AS periodo_inicio,

        (
            p.fecha_inicio
            + make_interval(months => n + 1)
        )::DATE AS periodo_fin

    FROM planes p

    CROSS JOIN LATERAL generate_series(
        0,
        p.cantidad_pagos - 1
    ) AS serie(n)
)

-- Registrar pagos ficticios de demostración.

INSERT INTO pago (
    id_vehiculo,
    id_cliente,
    id_operador,
    valor,
    fecha_pago,
    periodo_inicio,
    periodo_fin
)
SELECT
    v.id_vehiculo,
    v.id_cliente,
    o.id_operador,

    CASE
        WHEN v.tipo_vehiculo = 'MOTO'
            THEN 100000
        ELSE 250000
    END,

    p.periodo_inicio,
    p.periodo_inicio,
    p.periodo_fin

FROM periodos p

INNER JOIN vehiculo v
    ON v.placa = p.placa

INNER JOIN operador o
    ON o.usuario = 'operador1'

ORDER BY v.id_vehiculo, p.periodo_inicio;


-- =========================================================
-- ACTUALIZAR COBERTURA DE LOS VEHICULOS DE DEMOSTRACION
-- =========================================================

-- Las fechas de mensualidad deben corresponder
-- exactamente a los períodos de los pagos registrados.

UPDATE vehiculo v
SET
    fecha_inicio_mensualidad = cobertura.fecha_inicio,
    fecha_corte = cobertura.fecha_corte

FROM (
    SELECT
        id_vehiculo,
        MIN(periodo_inicio) AS fecha_inicio,
        MAX(periodo_fin) AS fecha_corte

    FROM pago

    GROUP BY id_vehiculo
) AS cobertura

WHERE v.id_vehiculo = cobertura.id_vehiculo;


-- =========================================================
-- AUTOS COLOMBIA - EVIDENCIA DE APRENDIZAJE 3
-- Datos de demostracion para fechas especiales
-- =========================================================
--
-- Referencias:
-- RN-27: Conservacion del dia original de corte.
-- RN-28: Ajuste de meses con menor cantidad de dias.
-- RN-29: Determinacion de vigencia.
-- RNF-I3-12: Datos de demostracion reproducibles.
-- PG-08: Fechas especiales del calendario.
--
-- Vehiculos:
-- CAL030: Dia original 30.
-- CAL031: Dia original 31.
-- CAL029: Primer pago el 29 de febrero.
--
-- Ejecutar exclusivamente en bases de demostracion
-- o pruebas.
--
-- El bloque es atomico e idempotente:
-- conserva los escenarios existentes y no duplica pagos.
--
-- Las fechas historicas se calculan con referencia
-- a la fecha local de Colombia.
-- =========================================================

DO $$
DECLARE

    v_hoy DATE :=
        (
            CURRENT_TIMESTAMP AT TIME ZONE
            'America/Bogota'
        )::DATE;

    v_inicio_30 DATE;

    v_inicio_31 DATE;

    v_inicio_29 DATE;

    v_anio_bisiesto INTEGER;

    v_escenario RECORD;

    v_id_cliente INTEGER;

    v_id_vehiculo INTEGER;

    v_id_operador INTEGER;

    v_cantidad INTEGER;

    v_periodo_inicio DATE;

    v_periodo_fin DATE;

    v_corte DATE;

    v_creados INTEGER := 0;

    v_existentes INTEGER := 0;

BEGIN

    -- =====================================================
    -- 1. IDENTIFICAR USUARIO RESPONSABLE
    -- =====================================================

    SELECT id_operador
    INTO STRICT v_id_operador
    FROM operador
    WHERE usuario = 'operador1';


    -- =====================================================
    -- 2. DETERMINAR FECHAS INICIALES
    -- =====================================================
    --
    -- Para los dias 30 y 31 se utiliza enero del
    -- anio anterior, garantizando que los escenarios
    -- incluyan febrero y la recuperacion del dia.
    --
    -- Para el dia 29 se busca el ultimo 29 de febrero
    -- anterior o igual a la fecha de referencia.

    v_inicio_30 := make_date(
        EXTRACT(YEAR FROM v_hoy)::INTEGER - 1,
        1,
        30
    );

    v_inicio_31 := make_date(
        EXTRACT(YEAR FROM v_hoy)::INTEGER - 1,
        1,
        31
    );

    v_anio_bisiesto :=
        EXTRACT(YEAR FROM v_hoy)::INTEGER;

    LOOP

        IF (
            MOD(v_anio_bisiesto, 400) = 0
            OR (
                MOD(v_anio_bisiesto, 4) = 0
                AND MOD(v_anio_bisiesto, 100) <> 0
            )
        ) THEN

            IF make_date(
                v_anio_bisiesto, 2, 29
            ) <= v_hoy THEN

                v_inicio_29 := make_date(
                    v_anio_bisiesto,
                    2,
                    29
                );

                EXIT;

            END IF;

        END IF;

        v_anio_bisiesto :=
            v_anio_bisiesto - 1;

    END LOOP;


    -- =====================================================
    -- 3. CREAR ESCENARIOS DE DEMOSTRACION
    -- =====================================================

    FOR v_escenario IN

        SELECT *
        FROM (
            VALUES

            (
                'CAL030',
                'EA3CAL030',
                'Demostracion calendario dia 30',
                'Renault',
                'Blanco',
                'AUTOMOVIL',
                v_inicio_30
            ),

            (
                'CAL031',
                'EA3CAL031',
                'Demostracion calendario dia 31',
                'Toyota',
                'Gris',
                'CAMIONETA',
                v_inicio_31
            ),

            (
                'CAL029',
                'EA3CAL029',
                'Demostracion calendario bisiesto',
                'Honda',
                'Negro',
                'MOTO',
                v_inicio_29
            )

        ) AS escenarios (

            placa,
            documento,
            nombre_cliente,
            marca,
            color,
            tipo_vehiculo,
            fecha_inicio

        )

    LOOP

        -- -------------------------------------------------
        -- 3.1. Proteger registros existentes.
        -- -------------------------------------------------

        IF EXISTS (

            SELECT 1
            FROM vehiculo
            WHERE placa = v_escenario.placa

        ) THEN

            -- No actualizar ni reemplazar datos
            -- que puedan haber sido utilizados
            -- durante una demostracion anterior.

            IF NOT EXISTS (

                SELECT 1
                FROM vehiculo v
                INNER JOIN cliente c
                    ON c.id_cliente = v.id_cliente
                WHERE v.placa = v_escenario.placa
                  AND c.documento =
                      v_escenario.documento
                  AND v.fecha_inicio_mensualidad
                      IS NOT NULL
                  AND EXTRACT(
                      DAY FROM v.fecha_inicio_mensualidad
                  ) = EXTRACT(
                      DAY FROM v_escenario.fecha_inicio
                  )
                  AND (
                      v_escenario.placa <> 'CAL029'
                      OR EXTRACT(
                          MONTH FROM
                          v.fecha_inicio_mensualidad
                      ) = 2
                  )

            ) THEN

                RAISE EXCEPTION
                    'Colision con escenario existente: %',
                    v_escenario.placa;

            END IF;

            v_existentes := v_existentes + 1;

            RAISE NOTICE
                'Escenario existente conservado: %',
                v_escenario.placa;

            CONTINUE;

        END IF;


        -- -------------------------------------------------
        -- 3.2. Registrar cliente de demostracion.
        -- -------------------------------------------------

        INSERT INTO cliente (
            documento,
            nombre
        )
        VALUES (
            v_escenario.documento,
            v_escenario.nombre_cliente
        )
        ON CONFLICT (documento)
        DO NOTHING;

        SELECT id_cliente
        INTO STRICT v_id_cliente
        FROM cliente
        WHERE documento =
            v_escenario.documento;


        -- -------------------------------------------------
        -- 3.3. Registrar vehiculo sin cobertura inicial.
        -- -------------------------------------------------

        INSERT INTO vehiculo (
            placa,
            marca,
            color,
            tipo_vehiculo,
            id_cliente
        )
        VALUES (
            v_escenario.placa,
            v_escenario.marca,
            v_escenario.color,
            v_escenario.tipo_vehiculo,
            v_id_cliente
        )
        RETURNING id_vehiculo
        INTO v_id_vehiculo;


        -- -------------------------------------------------
        -- 3.4. Generar mensualidades consecutivas.
        -- -------------------------------------------------
        --
        -- Cada periodo se calcula desde la fecha
        -- original de inicio.
        --
        -- No se calcula el siguiente periodo desde
        -- un corte previamente reducido en febrero.
        --
        -- Se generan pagos hasta obtener el primer
        -- corte estrictamente posterior a hoy.

        v_cantidad := 0;

        v_corte := v_escenario.fecha_inicio;

        WHILE v_corte <= v_hoy LOOP

            v_periodo_inicio := (
                v_escenario.fecha_inicio
                + make_interval(
                    months => v_cantidad
                )
            )::DATE;

            v_periodo_fin := (
                v_escenario.fecha_inicio
                + make_interval(
                    months => v_cantidad + 1
                )
            )::DATE;

            INSERT INTO pago (
                id_vehiculo,
                id_cliente,
                id_operador,
                valor,
                fecha_pago,
                periodo_inicio,
                periodo_fin
            )
            VALUES (
                v_id_vehiculo,
                v_id_cliente,
                v_id_operador,

                CASE

                    WHEN v_escenario.tipo_vehiculo
                        = 'MOTO'

                    THEN 100000

                    ELSE 250000

                END,

                v_periodo_inicio,
                v_periodo_inicio,
                v_periodo_fin
            );

            v_cantidad :=
                v_cantidad + 1;

            v_corte :=
                v_periodo_fin;

        END LOOP;


        -- -------------------------------------------------
        -- 3.5. Actualizar cobertura.
        -- -------------------------------------------------

        UPDATE vehiculo
        SET
            fecha_inicio_mensualidad =
                v_escenario.fecha_inicio,

            fecha_corte =
                v_corte

        WHERE id_vehiculo =
            v_id_vehiculo;


        -- -------------------------------------------------
        -- 3.6. Informar resultado.
        -- -------------------------------------------------

        v_creados := v_creados + 1;

        RAISE NOTICE
            'Vehiculo: %, Inicio: %, Corte: %, Pagos: %',
            v_escenario.placa,
            v_escenario.fecha_inicio,
            v_corte,
            v_cantidad;

    END LOOP;


    -- =====================================================
    -- 4. RESUMEN
    -- =====================================================

    RAISE NOTICE
        'Escenarios nuevos: %',
        v_creados;

    RAISE NOTICE
        'Escenarios existentes conservados: %',
        v_existentes;

    RAISE NOTICE
        'Semillas de calendario EA3 procesadas.';

END;
$$;


-- =========================================================
-- FIN DE SEMILLAS ESPECIALES
-- =========================================================


-- =========================================================
-- FIN DE LOS DATOS DE DEMOSTRACION DE LA ITERACION 3
-- =========================================================

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


-- =========================================================
-- CONFIRMAR CREACION DE LA BASE DE DATOS
-- =========================================================

COMMIT;


-- =========================================================
-- FIN DEL SCRIPT AUTOS COLOMBIA
-- =========================================================
