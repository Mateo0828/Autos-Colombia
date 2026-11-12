from app.database import get_connection


def buscar_por_placa(placa):
    consulta = """
        SELECT
            v.id_vehiculo,
            v.placa,
            v.marca,
            v.color,
            v.tipo_vehiculo,
            v.estado_mensualidad,
            c.id_cliente,
            c.documento AS documento_cliente,
            c.nombre AS nombre_cliente
        FROM vehiculo v
        INNER JOIN cliente c
            ON v.id_cliente = c.id_cliente
        WHERE UPPER(v.placa) = UPPER(%s);
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (placa,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_vehiculo": fila[0],
        "placa": fila[1],
        "marca": fila[2],
        "color": fila[3],
        "tipo_vehiculo": fila[4],
        "estado_mensualidad": fila[5],
        "cliente": {
            "id_cliente": fila[6],
            "documento": fila[7],
            "nombre": fila[8]
        }
    }

def actualizar_vehiculo(
    placa,
    marca,
    color,
    tipo_vehiculo,
    estado_mensualidad
):
    consulta = """
        UPDATE vehiculo
        SET
            marca = %s,
            color = %s,
            tipo_vehiculo = %s,
            estado_mensualidad = %s
        WHERE UPPER(placa) = UPPER(%s)
        RETURNING
            id_vehiculo,
            placa,
            marca,
            color,
            tipo_vehiculo,
            estado_mensualidad,
            id_cliente;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (
                    marca,
                    color,
                    tipo_vehiculo,
                    estado_mensualidad,
                    placa
                )
            )

            fila = cursor.fetchone()

        conexion.commit()

    if fila is None:
        return None

    return {
        "id_vehiculo": fila[0],
        "placa": fila[1],
        "marca": fila[2],
        "color": fila[3],
        "tipo_vehiculo": fila[4],
        "estado_mensualidad": fila[5],
        "id_cliente": fila[6]
    }
