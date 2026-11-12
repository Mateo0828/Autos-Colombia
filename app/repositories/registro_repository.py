from app.database import get_connection


def registrar_cliente_vehiculo(
    documento,
    nombre,
    placa,
    marca,
    color,
    tipo_vehiculo
):
    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            # Buscar cliente por documento.
            cursor.execute(
                """
                SELECT
                    id_cliente,
                    documento,
                    nombre
                FROM cliente
                WHERE documento = %s;
                """,
                (documento,)
            )

            cliente = cursor.fetchone()

            # Si no existe, crear el cliente.
            if cliente is None:
                cursor.execute(
                    """
                    INSERT INTO cliente (
                        documento,
                        nombre
                    )
                    VALUES (%s, %s)
                    RETURNING
                        id_cliente,
                        documento,
                        nombre;
                    """,
                    (
                        documento,
                        nombre
                    )
                )

                cliente = cursor.fetchone()

            id_cliente = cliente[0]

            # Crear vehículo asociado.
            cursor.execute(
                """
                INSERT INTO vehiculo (
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    estado_mensualidad,
                    id_cliente
                )
                VALUES (%s, %s, %s, %s, 'ACTIVA', %s)
                RETURNING
                    id_vehiculo,
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    estado_mensualidad;
                """,
                (
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    id_cliente
                )
            )

            vehiculo = cursor.fetchone()

        conexion.commit()

    return {
        "cliente": {
            "id_cliente": cliente[0],
            "documento": cliente[1],
            "nombre": cliente[2]
        },
        "vehiculo": {
            "id_vehiculo": vehiculo[0],
            "placa": vehiculo[1],
            "marca": vehiculo[2],
            "color": vehiculo[3],
            "tipo_vehiculo": vehiculo[4],
            "estado_mensualidad": vehiculo[5]
        }
    }
