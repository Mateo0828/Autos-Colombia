from app.database import get_connection


def consultar_disponibles(tipo_vehiculo):
    if tipo_vehiculo == "MOTO":
        tipo_celda = "MOTO"
    else:
        tipo_celda = "CARRO"

    consulta = """
        SELECT
            id_celda,
            codigo,
            tipo_celda,
            estado
        FROM celda
        WHERE tipo_celda = %s
          AND estado = 'DISPONIBLE'
        ORDER BY codigo;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (tipo_celda,))
            filas = cursor.fetchall()

    return [
        {
            "id_celda": fila[0],
            "codigo": fila[1],
            "tipo_celda": fila[2],
            "estado": fila[3]
        }
        for fila in filas
    ]