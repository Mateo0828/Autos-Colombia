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

def consultar_estado_parqueadero():
    consulta = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE estado = 'DISPONIBLE'
            ) AS disponibles,
            COUNT(*) FILTER (
                WHERE estado = 'OCUPADA'
            ) AS ocupadas,

            COUNT(*) FILTER (
                WHERE tipo_celda = 'CARRO'
            ) AS total_carro,
            COUNT(*) FILTER (
                WHERE tipo_celda = 'CARRO'
                  AND estado = 'DISPONIBLE'
            ) AS carro_disponibles,
            COUNT(*) FILTER (
                WHERE tipo_celda = 'CARRO'
                  AND estado = 'OCUPADA'
            ) AS carro_ocupadas,

            COUNT(*) FILTER (
                WHERE tipo_celda = 'MOTO'
            ) AS total_moto,
            COUNT(*) FILTER (
                WHERE tipo_celda = 'MOTO'
                  AND estado = 'DISPONIBLE'
            ) AS moto_disponibles,
            COUNT(*) FILTER (
                WHERE tipo_celda = 'MOTO'
                  AND estado = 'OCUPADA'
            ) AS moto_ocupadas
        FROM celda;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            fila = cursor.fetchone()

    return {
        "total": fila[0],
        "disponibles": fila[1],
        "ocupadas": fila[2],
        "carro": {
            "total": fila[3],
            "disponibles": fila[4],
            "ocupadas": fila[5]
        },
        "moto": {
            "total": fila[6],
            "disponibles": fila[7],
            "ocupadas": fila[8]
        }
    }