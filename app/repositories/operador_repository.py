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