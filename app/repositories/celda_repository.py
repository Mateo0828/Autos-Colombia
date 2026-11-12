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
                WHERE estado = 'FUERA_DE_SERVICIO'
            ) AS fuera_de_servicio,

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
                WHERE tipo_celda = 'CARRO'
                  AND estado = 'FUERA_DE_SERVICIO'
            ) AS carro_fuera_de_servicio,

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
            ) AS moto_ocupadas,
            COUNT(*) FILTER (
                WHERE tipo_celda = 'MOTO'
                  AND estado = 'FUERA_DE_SERVICIO'
            ) AS moto_fuera_de_servicio
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
        "fuera_de_servicio": fila[3],
        "carro": {
            "total": fila[4],
            "disponibles": fila[5],
            "ocupadas": fila[6],
            "fuera_de_servicio": fila[7]
        },
        "moto": {
            "total": fila[8],
            "disponibles": fila[9],
            "ocupadas": fila[10],
            "fuera_de_servicio": fila[11]
        }
    }

def consultar_celdas(
    estado=None,
    tipo=None,
    busqueda=None
):
    consulta = """
        SELECT
            id_celda,
            codigo,
            tipo_celda,
            estado
        FROM celda
        WHERE 1 = 1
    """

    parametros = []

    if estado:
        consulta += """
            AND estado = %s
        """
        parametros.append(estado)

    if tipo:
        consulta += """
            AND tipo_celda = %s
        """
        parametros.append(tipo)

    if busqueda:
        consulta += """
            AND UPPER(codigo) LIKE UPPER(%s)
        """
        parametros.append(f"%{busqueda}%")

    consulta += """
        ORDER BY codigo;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                consulta,
                parametros
            )
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

def deshabilitar_celda(codigo):
    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id_celda,
                    codigo,
                    tipo_celda,
                    estado
                FROM celda
                WHERE UPPER(codigo) = UPPER(%s)
                FOR UPDATE;
                """,
                (codigo,)
            )

            celda = cursor.fetchone()

            if celda is None:
                return None

            if celda[3] == "OCUPADA":
                raise ValueError(
                    "No es posible deshabilitar una celda ocupada."
                )

            cursor.execute(
                """
                UPDATE celda
                SET estado = 'FUERA_DE_SERVICIO'
                WHERE id_celda = %s
                RETURNING
                    id_celda,
                    codigo,
                    tipo_celda,
                    estado;
                """,
                (celda[0],)
            )

            fila = cursor.fetchone()

        conexion.commit()

    return {
        "id_celda": fila[0],
        "codigo": fila[1],
        "tipo_celda": fila[2],
        "estado": fila[3]
    }

def habilitar_celda(codigo):
    consulta_busqueda = """
        SELECT id_celda, codigo, tipo_celda, estado
        FROM celda
        WHERE codigo = %s
        FOR UPDATE;
    """

    consulta_actualizacion = """
        UPDATE celda
        SET estado = 'DISPONIBLE'
        WHERE codigo = %s
        RETURNING id_celda, codigo, tipo_celda, estado;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            # 1. Bloqueamos y consultamos la celda
            cursor.execute(consulta_busqueda, (codigo,))
            celda = cursor.fetchone()

            # 2. Si la celda no existe
            if celda is None:
                return None

            # 3. NUEVA VALIDACIÓN:
            # Una celda ocupada nunca puede convertirse manualmente
            # en DISPONIBLE.
            if celda[3] == "OCUPADA":
                raise ValueError(
                    "No es posible habilitar una celda ocupada."
                )

            # 4. Si está FUERA_DE_SERVICIO (o ya DISPONIBLE),
            # se establece como DISPONIBLE.
            cursor.execute(consulta_actualizacion, (codigo,))
            celda_actualizada = cursor.fetchone()

            return {
                "id_celda": celda_actualizada[0],
                "codigo": celda_actualizada[1],
                "tipo_celda": celda_actualizada[2],
                "estado": celda_actualizada[3]
            }