
-- =========================================================
-- AUTOS COLOMBIA
-- Pruebas de integridad de pagos y mensualidades
-- Evidencia de Aprendizaje 3
-- =========================================================

-- Ejecutar exclusivamente en la base aislada de pruebas.
-- Los cambios de datos realizados durante las pruebas
-- se revierten mediante ROLLBACK.

BEGIN;


DO $$
DECLARE
    v_id_vehiculo INTEGER;
    v_id_cliente INTEGER;
    v_id_operador INTEGER;
    v_id_pago INTEGER;

    v_hoy DATE :=
        (CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE;

    v_corte DATE :=
        (v_hoy + INTERVAL '1 month')::DATE;

    v_restriccion TEXT;
    v_caso RECORD;

    v_aprobadas INTEGER := 0;

BEGIN

    -- =====================================================
    -- PROTECCION DE LA BASE PRINCIPAL
    -- =====================================================

    IF current_database() <> 'autos_colombia_ea3_pruebas' THEN
        RAISE EXCEPTION
            'Este script debe ejecutarse en la base de pruebas.';
    END IF;


    -- =====================================================
    -- PREPARAR DATOS DE PRUEBA
    -- =====================================================

    SELECT id_vehiculo, id_cliente
    INTO STRICT v_id_vehiculo, v_id_cliente
    FROM vehiculo
    WHERE placa = 'XYZ987';

    SELECT id_operador
    INTO STRICT v_id_operador
    FROM operador
    WHERE usuario = 'operador1';

    IF EXISTS (
        SELECT 1
        FROM pago
        WHERE id_vehiculo = v_id_vehiculo
    ) THEN
        RAISE EXCEPTION
            'El vehiculo XYZ987 debe estar sin pagos.';
    END IF;

    RAISE NOTICE '=== PRUEBAS DE INTEGRIDAD EA3 ===';


    -- =====================================================
    -- PI-01: REGISTRAR UN PAGO VALIDO
    -- =====================================================

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
        250000,
        v_hoy,
        v_hoy,
        v_corte
    )
    RETURNING id_pago INTO v_id_pago;

    UPDATE vehiculo
    SET
        fecha_inicio_mensualidad = v_hoy,
        fecha_corte = v_corte
    WHERE id_vehiculo = v_id_vehiculo;

    v_aprobadas := v_aprobadas + 1;

    RAISE NOTICE
        '[PASS] PI-01: Registro valido de pago y cobertura';


    -- =====================================================
    -- PI-02 A PI-12: OPERACIONES INVALIDAS
    -- =====================================================

    FOR v_caso IN

        SELECT *
        FROM (
            VALUES

            (
                'PI-02',
                'Pago duplicado del mismo periodo',
                'uq_pago_vehiculo_periodo',
                format(
                    'INSERT INTO pago (
                        id_vehiculo, id_cliente, id_operador,
                        valor, fecha_pago,
                        periodo_inicio, periodo_fin
                    )
                    SELECT
                        id_vehiculo, id_cliente, id_operador,
                        valor, fecha_pago,
                        periodo_inicio, periodo_fin
                    FROM pago WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-03',
                'Valor igual a cero',
                'chk_valor_pago',
                format(
                    'UPDATE pago SET valor = 0
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-04',
                'Valor negativo',
                'chk_valor_pago',
                format(
                    'UPDATE pago SET valor = -100
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-05',
                'Periodo con fechas iguales',
                'chk_periodo_pago',
                format(
                    'UPDATE pago
                     SET periodo_fin = periodo_inicio
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-06',
                'Periodo con fechas invertidas',
                'chk_periodo_pago',
                format(
                    'UPDATE pago
                     SET periodo_fin = periodo_inicio - 1
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-07',
                'Vehiculo inexistente',
                'fk_pago_vehiculo',
                format(
                    'UPDATE pago SET id_vehiculo = -1
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-08',
                'Cliente inexistente',
                'fk_pago_cliente',
                format(
                    'UPDATE pago SET id_cliente = -1
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-09',
                'Operador inexistente',
                'fk_pago_operador',
                format(
                    'UPDATE pago SET id_operador = -1
                     WHERE id_pago = %s',
                    v_id_pago
                )
            ),

            (
                'PI-10',
                'Mensualidad sin fecha de corte',
                'chk_fechas_mensualidad',
                format(
                    'UPDATE vehiculo SET fecha_corte = NULL
                     WHERE id_vehiculo = %s',
                    v_id_vehiculo
                )
            ),

            (
                'PI-11',
                'Mensualidad sin fecha de inicio',
                'chk_fechas_mensualidad',
                format(
                    'UPDATE vehiculo
                     SET fecha_inicio_mensualidad = NULL
                     WHERE id_vehiculo = %s',
                    v_id_vehiculo
                )
            ),

            (
                'PI-12',
                'Fecha de corte anterior al inicio',
                'chk_fechas_mensualidad',
                format(
                    'UPDATE vehiculo
                     SET fecha_corte =
                         fecha_inicio_mensualidad - 1
                     WHERE id_vehiculo = %s',
                    v_id_vehiculo
                )
            )

        ) AS casos (
            codigo,
            descripcion,
            restriccion,
            sentencia
        )

    LOOP

        BEGIN

            EXECUTE v_caso.sentencia;

            RAISE EXCEPTION
                '[FAIL] %: La operacion invalida fue aceptada',
                v_caso.codigo;

        EXCEPTION

            WHEN unique_violation
                OR check_violation
                OR foreign_key_violation

            THEN

                GET STACKED DIAGNOSTICS
                    v_restriccion = CONSTRAINT_NAME;

                IF v_restriccion <>
                    v_caso.restriccion THEN

                    RAISE EXCEPTION
                        '[FAIL] %: Restriccion inesperada: %',
                        v_caso.codigo,
                        v_restriccion;

                END IF;

                v_aprobadas := v_aprobadas + 1;

                RAISE NOTICE
                    '[PASS] %: %',
                    v_caso.codigo,
                    v_caso.descripcion;

        END;

    END LOOP;


    -- =====================================================
    -- RESUMEN DE RESULTADOS
    -- =====================================================

    RAISE NOTICE '========================================';
    RAISE NOTICE 'PRUEBAS APROBADAS: % / 12', v_aprobadas;
    RAISE NOTICE '========================================';

    IF v_aprobadas <> 12 THEN
        RAISE EXCEPTION
            'No se aprobaron todas las pruebas.';
    END IF;

END;
$$;


-- =========================================================
-- REVERTIR LOS DATOS GENERADOS DURANTE LAS PRUEBAS
-- =========================================================

ROLLBACK;


-- =========================================================
-- FIN DE LAS PRUEBAS DE INTEGRIDAD DE PAGOS
-- =========================================================
