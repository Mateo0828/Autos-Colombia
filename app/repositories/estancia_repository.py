from app.database import get_connection


def existe_estancia_activa(id_vehiculo):
    consulta = """
        SELECT EXISTS (
            SELECT 1
            FROM estancia
            WHERE id_vehiculo = %s
              AND estado = 'ACTIVA'
        );
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta, (id_vehiculo,))
            resultado = cursor.fetchone()

    return resultado[0]

def registrar_entrada(
    id_vehiculo,
    codigo_celda,
    id_operador,
    tipo_vehiculo
):
    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            # Verificar que el operador exista.
            cursor.execute(
                """
                SELECT id_operador, nombre
                FROM operador
                WHERE id_operador = %s;
                """,
                (id_operador,)
            )

            operador = cursor.fetchone()

            if operador is None:
                raise ValueError("El operador no existe.")

            # Bloquear temporalmente la celda mientras
            # se realiza el registro de entrada.
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
                (codigo_celda,)
            )

            celda = cursor.fetchone()

            if celda is None:
                raise ValueError("La celda no existe.")

            id_celda = celda[0]
            codigo = celda[1]
            tipo_celda = celda[2]
            estado_celda = celda[3]

            if estado_celda != "DISPONIBLE":
                raise ValueError("La celda seleccionada se encuentra ocupada.")

            tipo_requerido = (
                "MOTO"
                if tipo_vehiculo == "MOTO"
                else "CARRO"
            )

            if tipo_celda != tipo_requerido:
                raise ValueError(
                    "La celda seleccionada no es compatible "
                    "con el tipo de vehículo."
                )

            # Crear estancia activa.
            cursor.execute(
                """
                INSERT INTO estancia (
                    id_vehiculo,
                    id_celda,
                    id_operador_entrada,
                    estado
                )
                VALUES (%s, %s, %s, 'ACTIVA')
                RETURNING
                    id_estancia,
                    fecha_hora_entrada;
                """,
                (
                    id_vehiculo,
                    id_celda,
                    id_operador
                )
            )

            estancia = cursor.fetchone()

            # La celda pasa a estar ocupada.
            cursor.execute(
                """
                UPDATE celda
                SET estado = 'OCUPADA'
                WHERE id_celda = %s;
                """,
                (id_celda,)
            )

        conexion.commit()

    return {
        "id_estancia": estancia[0],
        "fecha_hora_entrada": estancia[1].isoformat(),
        "estado": "ACTIVA",
        "celda": {
            "id_celda": id_celda,
            "codigo": codigo,
            "tipo_celda": tipo_celda,
            "estado": "OCUPADA"
        },
        "operador": {
            "id_operador": operador[0],
            "nombre": operador[1]
        }
    }

def registrar_salida(placa, id_operador):
    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            # Verificar que el operador exista.
            cursor.execute(
                """
                SELECT id_operador, nombre
                FROM operador
                WHERE id_operador = %s;
                """,
                (id_operador,)
            )

            operador = cursor.fetchone()

            if operador is None:
                raise ValueError("El operador no existe.")

            # Buscar la estancia activa del vehículo.
            cursor.execute(
                """
                SELECT
                    e.id_estancia,
                    e.id_celda,
                    e.fecha_hora_entrada,
                    c.codigo,
                    c.tipo_celda
                FROM estancia e
                INNER JOIN vehiculo v
                    ON e.id_vehiculo = v.id_vehiculo
                INNER JOIN celda c
                    ON e.id_celda = c.id_celda
                WHERE UPPER(v.placa) = UPPER(%s)
                  AND e.estado = 'ACTIVA'
                FOR UPDATE OF e, c;
                """,
                (placa,)
            )

            estancia = cursor.fetchone()

            if estancia is None:
                raise ValueError(
                    "El vehículo no tiene una estancia activa."
                )

            id_estancia = estancia[0]
            id_celda = estancia[1]
            fecha_hora_entrada = estancia[2]
            codigo_celda = estancia[3]
            tipo_celda = estancia[4]

            # Finalizar la estancia.
            cursor.execute(
                """
                UPDATE estancia
                SET
                    fecha_hora_salida = CURRENT_TIMESTAMP,
                    id_operador_salida = %s,
                    estado = 'FINALIZADA'
                WHERE id_estancia = %s
                RETURNING fecha_hora_salida;
                """,
                (
                    id_operador,
                    id_estancia
                )
            )

            fecha_hora_salida = cursor.fetchone()[0]

            # Liberar la celda.
            cursor.execute(
                """
                UPDATE celda
                SET estado = 'DISPONIBLE'
                WHERE id_celda = %s;
                """,
                (id_celda,)
            )

        conexion.commit()

    return {
        "id_estancia": id_estancia,
        "fecha_hora_entrada": fecha_hora_entrada.isoformat(),
        "fecha_hora_salida": fecha_hora_salida.isoformat(),
        "estado": "FINALIZADA",
        "celda": {
            "id_celda": id_celda,
            "codigo": codigo_celda,
            "tipo_celda": tipo_celda,
            "estado": "DISPONIBLE"
        },
        "operador_salida": {
            "id_operador": operador[0],
            "nombre": operador[1]
        }
    }