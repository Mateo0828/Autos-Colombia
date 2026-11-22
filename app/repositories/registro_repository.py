from app.database import get_connection
from app.services.mensualidad_service import (
    calcular_estado_mensualidad
)


def registrar_cliente_vehiculo(
    documento,
    nombre,
    placa,
    marca,
    color,
    tipo_vehiculo
):
    """
    Registra un vehículo asociado a un cliente nuevo
    o existente dentro de una única transacción.

    Iteración 3:
    Los vehículos nuevos se registran sin cobertura
    de mensualidad. Su activación requiere el registro
    del primer pago, conforme a la RN-32.
    """

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

            # Crear vehículo asociado sin cobertura inicial.
            # La mensualidad se activa únicamente mediante
            # el registro del primer pago.
            cursor.execute(
                """
                INSERT INTO vehiculo (
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    fecha_inicio_mensualidad,
                    fecha_corte,
                    id_cliente
                )
                VALUES (
                    %s, %s, %s, %s, NULL, NULL, %s
                )
                RETURNING
                    id_vehiculo,
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    fecha_inicio_mensualidad,
                    fecha_corte;
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

            # Estado calculado dinámicamente.
            "estado_mensualidad": calcular_estado_mensualidad(
                vehiculo[6]
            ),

            # Información de cobertura de la Iteración 3.
            "fecha_inicio_mensualidad": (
                vehiculo[5].isoformat()
                if vehiculo[5] is not None
                else None
            ),
            "fecha_corte": (
                vehiculo[6].isoformat()
                if vehiculo[6] is not None
                else None
            )
        }
    }