import re

from app.repositories.registro_repository import registrar_cliente_vehiculo
from app.repositories.vehiculo_repository import buscar_por_placa
from app.services.validacion_service import validar_placa


class PlacaDuplicadaError(Exception):
    pass


def crear_registro(
    documento,
    nombre,
    placa,
    marca,
    color,
    tipo_vehiculo
):
    documento = (
        ""
        if documento is None
        else str(documento).strip()
    )

    nombre = (
        ""
        if nombre is None
        else str(nombre).strip()
    )

    marca = (
        ""
        if marca is None
        else str(marca).strip()
    )

    color = (
        ""
        if color is None
        else str(color).strip()
    )

    tipo_vehiculo = (
        ""
        if tipo_vehiculo is None
        else str(tipo_vehiculo).strip().upper()
    )

    if not documento:
        raise ValueError(
            "El documento del cliente es obligatorio."
        )

    if len(documento) > 20:
        raise ValueError(
            "El documento no puede superar los 20 caracteres."
        )

    if not re.fullmatch(r"[A-Za-z0-9]+", documento):
        raise ValueError(
            "El documento solo puede contener letras y números."
        )

    if not nombre:
        raise ValueError(
            "El nombre del cliente es obligatorio."
        )

    if len(nombre) > 100:
        raise ValueError(
            "El nombre del cliente no puede superar los 100 caracteres."
        )

    placa = validar_placa(
        "" if placa is None else placa
    )

    if buscar_por_placa(placa) is not None:
        raise PlacaDuplicadaError(
            "La placa ya se encuentra registrada."
        )

    if not marca:
        raise ValueError(
            "La marca del vehículo es obligatoria."
        )

    if len(marca) > 50:
        raise ValueError(
            "La marca no puede superar los 50 caracteres."
        )

    if not color:
        raise ValueError(
            "El color del vehículo es obligatorio."
        )

    if len(color) > 30:
        raise ValueError(
            "El color no puede superar los 30 caracteres."
        )

    if tipo_vehiculo not in (
        "MOTO",
        "AUTOMOVIL",
        "CAMIONETA"
    ):
        raise ValueError(
            "El tipo de vehículo debe ser MOTO, AUTOMOVIL o CAMIONETA."
        )

    return registrar_cliente_vehiculo(
        documento,
        nombre,
        placa,
        marca,
        color,
        tipo_vehiculo
    )
