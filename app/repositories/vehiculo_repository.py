from app.database import get_connection

from app.services.mensualidad_service import (
    calcular_estado_mensualidad
)


# =========================================================
# EXCEPCIONES DEL REPOSITORIO
# =========================================================

class TipoVehiculoConEstanciaActivaError(Exception):
    """
    Impide modificar el tipo de un vehículo que
    actualmente se encuentra dentro del parqueadero.
    """

    pass


# =========================================================
# CONSULTAR VEHICULO POR PLACA
# =========================================================

def buscar_por_placa(placa):
    """
    Consulta la información administrativa del vehículo,
    su cliente asociado y las fechas de mensualidad.

    Iteración 3:
    El estado de mensualidad se calcula dinámicamente
    a partir de la fecha de corte.

    Referencias:
    RN-29, RN-32 y RN-38.
    """

    consulta = """
        SELECT
            v.id_vehiculo,
            v.placa,
            v.marca,
            v.color,
            v.tipo_vehiculo,
            v.fecha_inicio_mensualidad,
            v.fecha_corte,
            c.id_cliente,
            c.documento AS documento_cliente,
            c.nombre AS nombre_cliente
        FROM vehiculo v
        INNER JOIN cliente c
            ON v.id_cliente = c.id_cliente
        WHERE UPPER(v.placa) = UPPER(%s);
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            cursor.execute(
                consulta,
                (placa,)
            )

            fila = cursor.fetchone()

    if fila is None:

        return None

    fecha_inicio = fila[5]

    fecha_corte = fila[6]

    return {
        "id_vehiculo": fila[0],

        "placa": fila[1],

        "marca": fila[2],

        "color": fila[3],

        "tipo_vehiculo": fila[4],

        "estado_mensualidad": (
            calcular_estado_mensualidad(
                fecha_corte
            )
        ),

        "fecha_inicio_mensualidad": (
            fecha_inicio.isoformat()
            if fecha_inicio is not None
            else None
        ),

        "fecha_corte": (
            fecha_corte.isoformat()
            if fecha_corte is not None
            else None
        ),

        "cliente": {
            "id_cliente": fila[7],

            "documento": fila[8],

            "nombre": fila[9]
        }
    }


# =========================================================
# ACTUALIZACION TRANSACCIONAL DEL VEHICULO
# =========================================================

def actualizar_vehiculo(
    placa,
    marca=None,
    color=None,
    tipo_vehiculo=None
):
    """
    Actualiza exclusivamente los atributos administrativos
    permitidos del vehículo.

    Iteración 2:
    Impide modificar el tipo cuando existe una estancia
    activa.

    Iteración 3:
    - No permite modificar manualmente la mensualidad.
    - Bloquea el vehículo durante la actualización.
    - Comprueba la estancia activa dentro de la transacción.
    - Conserva los atributos que no fueron suministrados.
    - Calcula nuevamente el estado de mensualidad.

    El bloqueo es compatible con los mecanismos utilizados
    durante el registro de entradas y pagos.

    Referencias:
    RN-29, RN-34 y RN-38.
    """

    with get_connection() as conexion:
        with conexion.cursor() as cursor:

            # =============================================
            # 1. BLOQUEAR Y CONSULTAR VEHICULO
            # =============================================
            #
            # Comparte el mismo bloqueo de fila utilizado
            # por los módulos de entradas y pagos.

            cursor.execute(
                """
                SELECT
                    id_vehiculo,
                    marca,
                    color,
                    tipo_vehiculo
                FROM vehiculo
                WHERE UPPER(placa) = UPPER(%s)
                FOR UPDATE;
                """,
                (placa,)
            )

            vehiculo = cursor.fetchone()

            if vehiculo is None:

                return None

            id_vehiculo = vehiculo[0]

            marca_actual = vehiculo[1]

            color_actual = vehiculo[2]

            tipo_actual = vehiculo[3]

            # =============================================
            # 2. DETERMINAR ATRIBUTOS ACTUALIZADOS
            # =============================================
            #
            # Los atributos omitidos se conservan a partir
            # de la información obtenida bajo el bloqueo.

            marca_actualizada = (
                marca_actual
                if marca is None
                else marca
            )

            color_actualizado = (
                color_actual
                if color is None
                else color
            )

            tipo_actualizado = (
                tipo_actual
                if tipo_vehiculo is None
                else tipo_vehiculo
            )

            # =============================================
            # 3. COMPROBAR ESTANCIA ACTIVA
            # =============================================
            #
            # La restricción solo se aplica cuando existe
            # un cambio efectivo del tipo de vehículo.

            if tipo_actualizado != tipo_actual:

                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM estancia
                        WHERE id_vehiculo = %s
                          AND estado = 'ACTIVA'
                    );
                    """,
                    (id_vehiculo,)
                )

                tiene_estancia_activa = (
                    cursor.fetchone()[0]
                )

                if tiene_estancia_activa:

                    raise TipoVehiculoConEstanciaActivaError(
                        "No es posible cambiar el tipo de "
                        "vehículo mientras tenga una "
                        "estancia activa."
                    )

            # =============================================
            # 4. ACTUALIZAR ATRIBUTOS ADMINISTRATIVOS
            # =============================================
            #
            # RN-38:
            # Las fechas de cobertura y los pagos no
            # pueden modificarse mediante esta operación.

            cursor.execute(
                """
                UPDATE vehiculo
                SET
                    marca = %s,
                    color = %s,
                    tipo_vehiculo = %s
                WHERE id_vehiculo = %s
                RETURNING
                    id_vehiculo,
                    placa,
                    marca,
                    color,
                    tipo_vehiculo,
                    fecha_inicio_mensualidad,
                    fecha_corte,
                    id_cliente;
                """,
                (
                    marca_actualizada,
                    color_actualizado,
                    tipo_actualizado,
                    id_vehiculo
                )
            )

            fila = cursor.fetchone()

            if fila is None:

                raise RuntimeError(
                    "No fue posible actualizar el vehículo."
                )

            # =============================================
            # 5. CONSTRUIR RESPUESTA
            # =============================================

            fecha_inicio = fila[5]

            fecha_corte = fila[6]

            resultado = {
                "id_vehiculo": fila[0],

                "placa": fila[1],

                "marca": fila[2],

                "color": fila[3],

                "tipo_vehiculo": fila[4],

                "estado_mensualidad": (
                    calcular_estado_mensualidad(
                        fecha_corte
                    )
                ),

                "fecha_inicio_mensualidad": (
                    fecha_inicio.isoformat()
                    if fecha_inicio is not None
                    else None
                ),

                "fecha_corte": (
                    fecha_corte.isoformat()
                    if fecha_corte is not None
                    else None
                ),

                "id_cliente": fila[7]
            }

        # =============================================
        # 6. CONFIRMAR TRANSACCION
        # =============================================

        conexion.commit()

    return resultado