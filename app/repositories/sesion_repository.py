from app.database import get_connection


def crear_sesion(token_hash, id_operador, expira):
    consulta = """
        INSERT INTO sesion (
            token_hash,
            id_operador,
            expira
        )
        VALUES (%s, %s, %s)
        RETURNING
            id_sesion,
            creada,
            expira,
            revocada;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                (
                    token_hash,
                    id_operador,
                    expira
                )
            )

            fila = cursor.fetchone()

        conexion.commit()

    return {
        "id_sesion": fila[0],
        "creada": fila[1],
        "expira": fila[2],
        "revocada": fila[3]
    }

def buscar_sesion_por_token_hash(token_hash):
    consulta = """
        SELECT
            s.id_sesion,
            s.token_hash,
            s.creada,
            s.expira,
            s.revocada,
            o.id_operador,
            o.nombre,
            o.usuario,
            o.rol,
            o.estado
        FROM sesion s
        INNER JOIN operador o
            ON s.id_operador = o.id_operador
        WHERE s.token_hash = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (token_hash,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_sesion": fila[0],
        "token_hash": fila[1],
        "creada": fila[2],
        "expira": fila[3],
        "revocada": fila[4],
        "usuario": {
            "id_operador": fila[5],
            "nombre": fila[6],
            "usuario": fila[7],
            "rol": fila[8],
            "estado": fila[9]
        }
    }

def revocar_sesion_por_token_hash(token_hash):
    consulta = """
        UPDATE sesion
        SET revocada = TRUE
        WHERE token_hash = %s
          AND revocada = FALSE
        RETURNING id_sesion;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (token_hash,))
            fila = cursor.fetchone()

        conexion.commit()

    return fila is not None

def revocar_sesiones_por_operador(id_operador):
    consulta = """
        UPDATE sesion
        SET revocada = TRUE
        WHERE id_operador = %s
          AND revocada = FALSE;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_operador,))
            cantidad = cursor.rowcount

        conexion.commit()

    return cantidad
