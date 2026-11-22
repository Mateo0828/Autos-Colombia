from app.database import get_connection
from app.services.mensualidad_service import (
    calcular_estado_mensualidad,
    fecha_actual_colombia
)


def buscar_cliente_por_id(id_cliente):
    """
    Consulta un cliente y sus vehículos asociados.

    Iteración 3:
    El estado de mensualidad de cada vehículo se
    calcula dinámicamente a partir de su fecha de
    corte y la fecha actual de Colombia.

    RN-21, RN-29 y RN-38.
    """

    consulta_cliente = """
        SELECT
            id_cliente,
            documento,
            nombre
        FROM cliente
        WHERE id_cliente = %s;
    """

    consulta_vehiculos = """
        SELECT
            id_vehiculo,
            placa,
            marca,
            color,
            tipo_vehiculo,
            fecha_inicio_mensualidad,
            fecha_corte
        FROM vehiculo
        WHERE id_cliente = %s
        ORDER BY id_vehiculo;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute(
                consulta_cliente,
                (id_cliente,)
            )

            cliente = cursor.fetchone()

            if cliente is None:
                return None

            cursor.execute(
                consulta_vehiculos,
                (id_cliente,)
            )

            vehiculos = cursor.fetchall()

    # Utilizar la misma fecha de referencia para todos
    # los vehículos incluidos en esta consulta.
    hoy = fecha_actual_colombia()

    return {
        "id_cliente": cliente[0],
        "documento": cliente[1],
        "nombre": cliente[2],
        "vehiculos": [
            {
                "id_vehiculo": fila[0],
                "placa": fila[1],
                "marca": fila[2],
                "color": fila[3],
                "tipo_vehiculo": fila[4],

                # Estado calculado, no almacenado.
                "estado_mensualidad": (
                    calcular_estado_mensualidad(
                        fila[6],
                        hoy
                    )
                ),

                # Información de cobertura de la I3.
                "fecha_inicio_mensualidad": (
                    fila[5].isoformat()
                    if fila[5] is not None
                    else None
                ),

                "fecha_corte": (
                    fila[6].isoformat()
                    if fila[6] is not None
                    else None
                )
            }
            for fila in vehiculos
        ]
    }


def actualizar_cliente(
    id_cliente,
    documento,
    nombre
):
    """
    Actualiza los datos administrativos del cliente.

    Esta operación no modifica la cobertura ni los
    pagos de sus vehículos asociados.
    """

    consulta = """
        UPDATE cliente
        SET
            documento = %s,
            nombre = %s
        WHERE id_cliente = %s
        RETURNING
            id_cliente,
            documento,
            nombre;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute(
                consulta,
                (
                    documento,
                    nombre,
                    id_cliente
                )
            )

            fila = cursor.fetchone()

        conexion.commit()

    if fila is None:
        return None

    return {
        "id_cliente": fila[0],
        "documento": fila[1],
        "nombre": fila[2]
    }


def buscar_cliente_por_documento(documento):
    """
    Busca un cliente mediante su documento.

    Se utiliza para identificar clientes existentes
    y controlar documentos duplicados.
    """

    consulta = """
        SELECT
            id_cliente,
            documento,
            nombre
        FROM cliente
        WHERE documento = %s;
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute(
                consulta,
                (documento,)
            )

            fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id_cliente": fila[0],
        "documento": fila[1],
        "nombre": fila[2]
    }