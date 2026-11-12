from app.database import get_connection


def buscar_cliente_por_id(id_cliente):
    consulta_cliente = """
        SELECT
            id_cliente,
            documento,
            nombre
        FROM cliente
        WHERE id_cliente = %s;
    """

    consulta_vehiculos = """
        SELECT
            id_vehiculo,
            placa,
            marca,
            color,
            tipo_vehiculo,
            estado_mensualidad
        FROM vehiculo
        WHERE id_cliente = %s
        ORDER BY id_vehiculo;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta_cliente,
                (id_cliente,)
            )
            cliente = cursor.fetchone()

            if cliente is None:
                return None

            cursor.execute(
                consulta_vehiculos,
                (id_cliente,)
            )
            vehiculos = cursor.fetchall()

    return {
        "id_cliente": cliente[0],
        "documento": cliente[1],
        "nombre": cliente[2],
        "vehiculos": [
            {
                "id_vehiculo": fila[0],
                "placa": fila[1],
                "marca": fila[2],
                "color": fila[3],
                "tipo_vehiculo": fila[4],
                "estado_mensualidad": fila[5]
            }
            for fila in vehiculos
        ]
    }

def actualizar_cliente(
    id_cliente,
    documento,
    nombre
):
    consulta = """
        UPDATE cliente
        SET
            documento = %s,
            nombre = %s
        WHERE id_cliente = %s
        RETURNING
            id_cliente,
            documento,
            nombre;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (
                    documento,
                    nombre,
                    id_cliente
                )
            )

            fila = cursor.fetchone()

        conexion.commit()

    if fila is None:
        return None

    return {
        "id_cliente": fila[0],
        "documento": fila[1],
        "nombre": fila[2]
    }

def buscar_cliente_por_documento(documento):
    consulta = """
        SELECT
            id_cliente,
            documento,
            nombre
        FROM cliente
        WHERE documento = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (documento,)
            )
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_cliente": fila[0],
        "documento": fila[1],
        "nombre": fila[2]
    }
