-- =========================================================
-- AUTOS COLOMBIA
-- Pruebas de integridad de cierre de estancias
-- P-14 a P-19
--
-- Todas las pruebas se ejecutan dentro de una transacción
-- y al final se hace ROLLBACK para no modificar la base.
-- =========================================================

BEGIN;


-- =========================================================
-- P-14
-- ACTIVA sin fecha ni operador de salida
-- Resultado esperado: PERMITIDA
-- =========================================================
DO $$
BEGIN
    INSERT INTO estancia (
        id_vehiculo,
        id_celda,
        id_operador_entrada,
        estado,
        fecha_hora_salida,
        id_operador_salida
    )
    VALUES (
        1,
        1,
        1,
        'ACTIVA',
        NULL,
        NULL
    );

    RAISE NOTICE 'P-14 PASS: estancia ACTIVA válida aceptada.';
END;
$$;


-- Limpiar la estancia creada por P-14 dentro de la transacción
DELETE FROM estancia
WHERE id_vehiculo = 1
  AND id_celda = 1
  AND estado = 'ACTIVA';


-- =========================================================
-- P-15
-- FINALIZADA sin fecha de salida
-- Resultado esperado: RECHAZADA
-- =========================================================
DO $$
BEGIN
    BEGIN
        INSERT INTO estancia (
            id_vehiculo,
            id_celda,
            id_operador_entrada,
            estado,
            fecha_hora_salida,
            id_operador_salida
        )
        VALUES (
            1,
            1,
            1,
            'FINALIZADA',
            NULL,
            2
        );

        RAISE EXCEPTION
            'P-15 FAIL: se permitió una FINALIZADA sin fecha de salida.';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'P-15 PASS: FINALIZADA sin fecha de salida fue rechazada.';
    END;
END;
$$;


-- =========================================================
-- P-16
-- FINALIZADA sin operador de salida
-- Resultado esperado: RECHAZADA
-- =========================================================
DO $$
BEGIN
    BEGIN
        INSERT INTO estancia (
            id_vehiculo,
            id_celda,
            id_operador_entrada,
            estado,
            fecha_hora_salida,
            id_operador_salida
        )
        VALUES (
            1,
            1,
            1,
            'FINALIZADA',
            CURRENT_TIMESTAMP,
            NULL
        );

        RAISE EXCEPTION
            'P-16 FAIL: se permitió una FINALIZADA sin operador de salida.';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'P-16 PASS: FINALIZADA sin operador de salida fue rechazada.';
    END;
END;
$$;


-- =========================================================
-- P-17
-- ACTIVA con fecha de salida
-- Resultado esperado: RECHAZADA
-- =========================================================
DO $$
BEGIN
    BEGIN
        INSERT INTO estancia (
            id_vehiculo,
            id_celda,
            id_operador_entrada,
            estado,
            fecha_hora_salida,
            id_operador_salida
        )
        VALUES (
            1,
            1,
            1,
            'ACTIVA',
            CURRENT_TIMESTAMP,
            NULL
        );

        RAISE EXCEPTION
            'P-17 FAIL: se permitió una ACTIVA con fecha de salida.';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'P-17 PASS: ACTIVA con fecha de salida fue rechazada.';
    END;
END;
$$;


-- =========================================================
-- P-18
-- ACTIVA con operador de salida
-- Resultado esperado: RECHAZADA
-- =========================================================
DO $$
BEGIN
    BEGIN
        INSERT INTO estancia (
            id_vehiculo,
            id_celda,
            id_operador_entrada,
            estado,
            fecha_hora_salida,
            id_operador_salida
        )
        VALUES (
            1,
            1,
            1,
            'ACTIVA',
            NULL,
            2
        );

        RAISE EXCEPTION
            'P-18 FAIL: se permitió una ACTIVA con operador de salida.';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'P-18 PASS: ACTIVA con operador de salida fue rechazada.';
    END;
END;
$$;


-- =========================================================
-- P-19
-- FINALIZADA con fecha y operador de salida
-- Resultado esperado: PERMITIDA
-- =========================================================
DO $$
BEGIN
    INSERT INTO estancia (
        id_vehiculo,
        id_celda,
        id_operador_entrada,
        estado,
        fecha_hora_salida,
        id_operador_salida
    )
    VALUES (
        1,
        1,
        1,
        'FINALIZADA',
        CURRENT_TIMESTAMP,
        2
    );

    RAISE NOTICE
        'P-19 PASS: estancia FINALIZADA válida aceptada.';
END;
$$;


-- =========================================================
-- No dejar datos de prueba
-- =========================================================
ROLLBACK;