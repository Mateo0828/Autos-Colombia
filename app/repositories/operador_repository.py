from app.database import get_connection


def consultar_operadores():
    consulta = """
        SELECT
            id_operador,
            nombre
        FROM operador
        ORDER BY id_operador;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            filas = cursor.fetchall()

    return [
        {
            "id_operador": fila[0],
            "nombre": fila[1]
        }
        for fila in filas
    ]

def buscar_operador_por_usuario(usuario):
    consulta = """
        SELECT
            id_operador,
            nombre,
            usuario,
            password_hash,
            rol,
            estado,
            fecha_creacion
        FROM operador
        WHERE usuario = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (usuario,))
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_operador": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "password_hash": fila[3],
        "rol": fila[4],
        "estado": fila[5],
        "fecha_creacion": fila[6]
    }
