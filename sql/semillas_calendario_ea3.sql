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