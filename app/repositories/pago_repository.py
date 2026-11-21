
# =========================================================
# AUTOS COLOMBIA
# Iteracion 3 - Gestion de pagos
# Repositorio de pagos y mensualidades
# =========================================================

# Las funciones reciben un cursor con row_factory=dict_row.
# La conexion y la transaccion son administradas por
# el servicio que invoca al repositorio.
#
# No se realizan commits independientes en este archivo.


# =========================================================
# CONSULTAR INFORMACION DE LA MENSUALIDAD
# =========================================================

def buscar_mensualidad(cursor, placa, bloquear=False):

    # Cuando se registra un pago, bloquear primero el
    # vehiculo para impedir renovaciones simultaneas.

    if bloquear:

        cursor.execute(
            """
            SELECT id_vehiculo
            FROM vehiculo
            WHERE UPPER(placa) = UPPER(%s)
            FOR UPDATE;
            """,
            (placa,)
        )

        if cursor.fetchone() is None:
            return None

    # Consultar los datos despues de adquirir el bloqueo.
    # Esto permite obtener la cobertura y cantidad de pagos
    # actualizadas si otra transaccion termino mientras
    # se esperaba el bloqueo.

    cursor.execute(
        """
        SELECT
            v.id_vehiculo,
            v.placa,
            v.marca,
            v.color,
            v.tipo_vehiculo,
            v.fecha_inicio_mensualidad,
            v.fecha_corte,

            c.id_cliente,
            c.documento AS documento_cliente,
            c.nombre AS nombre_cliente,

            (
                SELECT COUNT(*)
                FROM pago p
                WHERE p.id_vehiculo = v.id_vehiculo
            ) AS num_pagos

        FROM vehiculo v

        INNER JOIN cliente c
            ON v.id_cliente = c.id_cliente

        WHERE UPPER(v.placa) = UPPER(%s);
        """,
        (placa,)
    )

    return cursor.fetchone()


# =========================================================
# INSERTAR UN NUEVO PAGO
# =========================================================

def insertar_pago(
    cursor,
    id_vehiculo,
    id_cliente,
    id_operador,
    valor,
    fecha_pago,
    periodo_inicio,
    periodo_fin
):

    cursor.execute(
        """
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
            %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING
            id_pago,
            id_vehiculo,
            id_cliente,
            id_operador,
            valor,
            fecha_pago,
            fecha_registro,
            periodo_inicio,
            periodo_fin;
        """,
        (
            id_vehiculo,
            id_cliente,
            id_operador,
            valor,
            fecha_pago,
            periodo_inicio,
            periodo_fin
        )
    )

    return cursor.fetchone()


# =========================================================
# ACTUALIZAR COBERTURA DE MENSUALIDAD
# =========================================================

def actualizar_cobertura(
    cursor,
    id_vehiculo,
    fecha_inicio_mensualidad,
    fecha_corte
):

    cursor.execute(
        """
        UPDATE vehiculo
        SET
            fecha_inicio_mensualidad = %s,
            fecha_corte = %s
        WHERE id_vehiculo = %s

        RETURNING
            id_vehiculo,
            fecha_inicio_mensualidad,
            fecha_corte;
        """,
        (
            fecha_inicio_mensualidad,
            fecha_corte,
            id_vehiculo
        )
    )

    fila = cursor.fetchone()

    if fila is None:
        raise RuntimeError(
            "No fue posible actualizar la mensualidad."
        )

    return fila


# =========================================================
# CONSULTAR HISTORIAL DE PAGOS POR VEHICULO
# =========================================================

def consultar_historial_pagos(cursor, id_vehiculo):

    cursor.execute(
        """
        SELECT
            p.id_pago,
            p.id_vehiculo,
            p.id_cliente,
            p.valor,
            p.fecha_pago,
            p.fecha_registro,
            p.periodo_inicio,
            p.periodo_fin,

            o.id_operador,
            o.usuario AS usuario_operador,
            o.nombre AS nombre_operador

        FROM pago p

        INNER JOIN operador o
            ON p.id_operador = o.id_operador

        WHERE p.id_vehiculo = %s

        ORDER BY
            p.fecha_pago DESC,
            p.id_pago DESC;
        """,
        (id_vehiculo,)
    )

    return cursor.fetchall()
