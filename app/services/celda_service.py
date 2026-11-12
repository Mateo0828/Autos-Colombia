from app.repositories.celda_repository import (
    consultar_celdas,
    consultar_disponibles,
    deshabilitar_celda,
    habilitar_celda,
)

from app.services.validacion_service import validar_codigo_celda


class CeldaNoEncontradaError(Exception):
    pass

class CeldaOcupadaError(Exception):
    pass


def obtener_celdas_disponibles(tipo_vehiculo):
    tipo_vehiculo = tipo_vehiculo.upper().strip()

    tipos_validos = ["MOTO", "AUTOMOVIL", "CAMIONETA"]

    if tipo_vehiculo not in tipos_validos:
        raise ValueError("Tipo de vehículo no válido.")

    return consultar_disponibles(tipo_vehiculo)

def listar_celdas(
    estado=None,
    tipo=None,
    busqueda=None
):
    estado = (
        None
        if estado is None or str(estado).strip() == ""
        else str(estado).strip().upper()
    )

    tipo = (
        None
        if tipo is None or str(tipo).strip() == ""
        else str(tipo).strip().upper()
    )

    busqueda = (
        None
        if busqueda is None or str(busqueda).strip() == ""
        else str(busqueda).strip()
    )

    if estado not in (
        None,
        "DISPONIBLE",
        "OCUPADA",
        "FUERA_DE_SERVICIO"
    ):
        raise ValueError(
            "El estado debe ser DISPONIBLE, OCUPADA o FUERA_DE_SERVICIO."
        )

    if tipo not in (
        None,
        "CARRO",
        "MOTO"
    ):
        raise ValueError(
            "El tipo de celda debe ser CARRO o MOTO."
        )

    return consultar_celdas(
        estado=estado,
        tipo=tipo,
        busqueda=busqueda
    )

def poner_celda_fuera_de_servicio(codigo):
    codigo = validar_codigo_celda(codigo)

    try:
        celda = deshabilitar_celda(codigo)

    except ValueError as error:
        raise CeldaOcupadaError(str(error))

    if celda is None:
        raise CeldaNoEncontradaError(
            "La celda solicitada no existe."
        )

    return celda


def poner_celda_disponible(codigo):
    codigo = validar_codigo_celda(codigo)

    try:
        celda = habilitar_celda(codigo)
    except ValueError as error:
        raise CeldaOcupadaError(str(error))

    if celda is None:
        raise CeldaNoEncontradaError(
            f"No existe una celda con el código {codigo}."
        )

    return celda