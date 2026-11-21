
from calendar import monthrange
from datetime import date, datetime
from zoneinfo import ZoneInfo


# =========================================================
# CONFIGURACION DE MENSUALIDADES
# Tarifas establecidas desde la Iteracion 1.
# =========================================================

ZONA_HORARIA = ZoneInfo("America/Bogota")

TARIFAS_MENSUALES = {
    "AUTOMOVIL": 250000,
    "CAMIONETA": 250000,
    "MOTO": 100000
}


# =========================================================
# FECHA ACTUAL DE COLOMBIA
# =========================================================

def fecha_actual_colombia():
    return datetime.now(ZONA_HORARIA).date()


# =========================================================
# DETERMINACION DE TARIFAS
# RN-20, RN-21 y RN-35
# =========================================================

def obtener_tarifa(tipo_vehiculo):
    tipo = str(tipo_vehiculo).strip().upper()

    if tipo not in TARIFAS_MENSUALES:
        raise ValueError(
            "El tipo de vehiculo no tiene una tarifa valida."
        )

    return TARIFAS_MENSUALES[tipo]


# =========================================================
# VALIDACION DE LA FECHA EFECTIVA DEL PAGO
# =========================================================

def validar_fecha_pago(valor, hoy=None):
    if hoy is None:
        hoy = fecha_actual_colombia()

    if not isinstance(valor, str):
        raise ValueError(
            "La fecha de pago es obligatoria."
        )

    try:
        fecha_pago = date.fromisoformat(valor)

        if fecha_pago.isoformat() != valor:
            raise ValueError

    except ValueError:
        raise ValueError(
            "La fecha de pago debe tener el formato YYYY-MM-DD."
        )

    if fecha_pago > hoy:
        raise ValueError(
            "La fecha de pago no puede ser futura."
        )

    return fecha_pago


# =========================================================
# CALCULO DE FECHAS DE CORTE
# RN-23, RN-24, RN-27 y RN-28
# =========================================================

def calcular_fecha_corte(fecha_inicio, meses):
    if type(fecha_inicio) is not date:
        raise ValueError(
            "La fecha de inicio no es valida."
        )

    if type(meses) is not int or meses < 0:
        raise ValueError(
            "La cantidad de meses debe ser un entero no negativo."
        )

    # Calcular el mes de destino desde la fecha original.
    mes_total = (
        fecha_inicio.year * 12
        + fecha_inicio.month - 1
        + meses
    )

    anio, mes_indice = divmod(mes_total, 12)

    mes = mes_indice + 1

    # Determinar el ultimo dia del mes de destino.
    ultimo_dia = monthrange(anio, mes)[1]

    # Conservar el dia original cuando exista.
    dia = min(fecha_inicio.day, ultimo_dia)

    return date(anio, mes, dia)


# =========================================================
# ESTADO CALCULADO DE LA MENSUALIDAD
# RN-29 y RN-38
# =========================================================

def calcular_estado_mensualidad(fecha_corte, hoy=None):
    if hoy is None:
        hoy = fecha_actual_colombia()

    if fecha_corte is None:
        return "INACTIVA"

    if hoy < fecha_corte:
        return "ACTIVA"

    return "INACTIVA"


# =========================================================
# PROYECCION DEL PROXIMO PAGO
# RN-23 a RN-28, RN-35 y RN-37
#
# Esta funcion no modifica la base de datos.
# Se reutiliza al consultar y al registrar un pago.
# =========================================================

def proyectar_pago(
    tipo_vehiculo,
    fecha_pago,
    fecha_inicio_mensualidad,
    fecha_corte,
    num_pagos,
    hoy=None
):
    if hoy is None:
        hoy = fecha_actual_colombia()

    if type(fecha_pago) is not date:
        raise ValueError(
            "La fecha de pago no es valida."
        )

    if fecha_pago > hoy:
        raise ValueError(
            "La fecha de pago no puede ser futura."
        )

    valor = obtener_tarifa(tipo_vehiculo)

    # -----------------------------------------------------
    # PRIMER PAGO
    # -----------------------------------------------------

    if num_pagos == 0:

        if (
            fecha_inicio_mensualidad is not None
            or fecha_corte is not None
        ):
            raise RuntimeError(
                "La mensualidad presenta fechas inconsistentes."
            )

        tipo_pago = "PRIMER_PAGO"

        nueva_fecha_inicio = fecha_pago

        periodo_inicio = fecha_pago

        periodo_fin = calcular_fecha_corte(
            nueva_fecha_inicio,
            1
        )

    # -----------------------------------------------------
    # RENOVACION
    # -----------------------------------------------------

    else:

        if (
            fecha_inicio_mensualidad is None
            or fecha_corte is None
        ):
            raise RuntimeError(
                "La mensualidad no tiene fechas de cobertura."
            )

        if fecha_corte != calcular_fecha_corte(
            fecha_inicio_mensualidad,
            num_pagos
        ):
            raise RuntimeError(
                "La cobertura no coincide con los pagos registrados."
            )

        if fecha_pago < fecha_inicio_mensualidad:
            raise ValueError(
                "La fecha de pago no puede ser anterior "
                "al inicio de la mensualidad."
            )

        tipo_pago = "RENOVACION"

        nueva_fecha_inicio = fecha_inicio_mensualidad

        periodo_inicio = fecha_corte

        periodo_fin = calcular_fecha_corte(
            nueva_fecha_inicio,
            num_pagos + 1
        )

    # -----------------------------------------------------
    # ESTADO RESULTANTE
    # -----------------------------------------------------

    estado_resultante = calcular_estado_mensualidad(
        periodo_fin,
        hoy
    )

    advertencia = None

    if estado_resultante == "INACTIVA":
        advertencia = (
            "El periodo pagado no cubre la fecha actual. "
            "La mensualidad permanece inactiva."
        )

    return {
        "tipo": tipo_pago,
        "valor": valor,
        "fecha_pago": fecha_pago,
        "fecha_inicio": nueva_fecha_inicio,
        "dia_corte": nueva_fecha_inicio.day,
        "periodo_inicio": periodo_inicio,
        "periodo_fin": periodo_fin,
        "corte_esperado": fecha_corte,
        "estado_resultante": estado_resultante,
        "num_pagos_resultante": num_pagos + 1,
        "advertencia": advertencia
    }
