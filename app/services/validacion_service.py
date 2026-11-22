import re

from app.repositories.estancia_repository import (
    existe_estancia_activa
)

from app.repositories.vehiculo_repository import (
    buscar_por_placa
)


def validar_ingreso(placa):
    """
    Verifica las condiciones necesarias para que un
    vehículo pueda ingresar al parqueadero.

    Iteración 1:
    - El vehículo debe estar registrado.
    - No debe tener una estancia activa.

    Iteración 3:
    - Debe contar con un primer pago registrado.
    - La mensualidad debe encontrarse vigente.
    - La vigencia se obtiene del estado calculado
      mediante la fecha de corte.

    Esta función realiza una validación previa.
    El registro efectivo de entrada debe revalidar
    las condiciones dentro de su transacción.

    Referencias:
    RF-I3-11, RN-29, RN-30, HU-I3-05 y UC-I3-05.
    """

    placa = validar_placa(placa)

    vehiculo = buscar_por_placa(placa)

    # Primera condición:
    # El vehículo debe encontrarse registrado.
    if vehiculo is None:

        return {
            "puede_ingresar": False,

            "codigo_motivo": (
                "VEHICULO_NO_REGISTRADO"
            ),

            "motivo": (
                "El vehículo no se encuentra registrado."
            ),

            "vehiculo": None,

            "validaciones": {
                "vehiculo_registrado": False,
                "mensualidad_activa": False,
                "sin_estancia_activa": False
            }
        }

    # Segunda condición:
    # Consultar el estado calculado de la mensualidad.
    # Este atributo ya no corresponde a una columna
    # editable de PostgreSQL.
    mensualidad_activa = (
        vehiculo["estado_mensualidad"] == "ACTIVA"
    )

    # Identificar si existe cobertura inicial.
    tiene_primer_pago = (
        vehiculo["fecha_inicio_mensualidad"] is not None
        and vehiculo["fecha_corte"] is not None
    )

    # Tercera condición:
    # El vehículo no puede tener otra estancia activa.
    tiene_estancia_activa = existe_estancia_activa(
        vehiculo["id_vehiculo"]
    )

    sin_estancia_activa = not tiene_estancia_activa

    # Resultado consolidado de las validaciones.
    puede_ingresar = (
        tiene_primer_pago
        and mensualidad_activa
        and sin_estancia_activa
    )

    # Determinar el motivo del resultado.
    # Los códigos permiten al frontend identificar
    # cada escenario sin interpretar textos.

    if not tiene_primer_pago:

        codigo_motivo = "SIN_PRIMER_PAGO"

        motivo = (
            "El vehículo no tiene un primer pago "
            "de mensualidad registrado."
        )

    elif not mensualidad_activa:

        codigo_motivo = "MENSUALIDAD_VENCIDA"

        motivo = (
            "La mensualidad del vehículo se encuentra "
            "vencida. Debe registrar una renovación "
            "que restablezca su vigencia."
        )

    elif tiene_estancia_activa:

        codigo_motivo = "ESTANCIA_ACTIVA"

        motivo = (
            "El vehículo ya tiene una estancia activa."
        )

    else:

        codigo_motivo = "INGRESO_PERMITIDO"

        motivo = (
            "El vehículo cumple las condiciones "
            "para ingresar."
        )

    return {
        "puede_ingresar": puede_ingresar,
        "codigo_motivo": codigo_motivo,
        "motivo": motivo,
        "vehiculo": vehiculo,

        "validaciones": {
            "vehiculo_registrado": True,
            "mensualidad_activa": mensualidad_activa,
            "sin_estancia_activa": sin_estancia_activa
        }
    }


def validar_id_operador(id_operador):
    """
    Valida el identificador del operador.

    Función conservada de las iteraciones anteriores.
    """

    if id_operador is None:

        raise ValueError(
            "El operador es obligatorio."
        )

    if isinstance(id_operador, bool):

        raise ValueError(
            "El identificador del operador no es válido."
        )

    try:

        id_operador = int(id_operador)

    except (TypeError, ValueError):

        raise ValueError(
            "El identificador del operador debe ser "
            "un número entero."
        )

    if id_operador <= 0:

        raise ValueError(
            "El identificador del operador debe ser "
            "mayor que cero."
        )

    return id_operador


def validar_placa(placa):
    """
    Normaliza y valida la placa del vehículo.
    """

    placa = str(placa).strip().upper()

    if not placa:

        raise ValueError(
            "La placa es obligatoria."
        )

    if len(placa) > 10:

        raise ValueError(
            "La placa no puede superar los 10 caracteres."
        )

    if not re.fullmatch(r"[A-Z0-9]+", placa):

        raise ValueError(
            "La placa solo puede contener letras y números."
        )

    return placa


def validar_codigo_celda(codigo_celda):
    """
    Normaliza y valida el código de la celda.
    """

    codigo_celda = str(codigo_celda).strip().upper()

    if not codigo_celda:

        raise ValueError(
            "La celda es obligatoria."
        )

    if len(codigo_celda) > 10:

        raise ValueError(
            "El código de la celda no puede superar "
            "los 10 caracteres."
        )

    if not re.fullmatch(
        r"[A-Z0-9]+",
        codigo_celda
    ):

        raise ValueError(
            "El código de la celda solo puede contener "
            "letras y números."
        )

    return codigo_celda