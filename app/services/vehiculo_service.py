from app.repositories.estancia_repository import existe_estancia_activa
from app.repositories.vehiculo_repository import (
    actualizar_vehiculo,
    buscar_por_placa,
)
from app.services.validacion_service import validar_placa


class VehiculoNoEncontradoError(Exception):
    pass

class TipoVehiculoConEstanciaActivaError(Exception):
    pass


def consultar_vehiculo(placa):
    placa = validar_placa(placa)

    return buscar_por_placa(placa)

def modificar_vehiculo(
    placa,
    marca=None,
    color=None,
    tipo_vehiculo=None,
    estado_mensualidad=None
):
    placa = validar_placa(placa)

    vehiculo = buscar_por_placa(placa)

    if vehiculo is None:
        raise VehiculoNoEncontradoError(
            "El vehículo solicitado no existe."
        )

    marca_actualizada = (
        vehiculo["marca"]
        if marca is None
        else str(marca).strip()
    )

    color_actualizado = (
        vehiculo["color"]
        if color is None
        else str(color).strip()
    )

    tipo_actualizado = (
        vehiculo["tipo_vehiculo"]
        if tipo_vehiculo is None
        else str(tipo_vehiculo).strip().upper()
    )

    mensualidad_actualizada = (
        vehiculo["estado_mensualidad"]
        if estado_mensualidad is None
        else str(estado_mensualidad).strip().upper()
    )

    if not marca_actualizada:
        raise ValueError(
            "La marca del vehículo es obligatoria."
        )

    if len(marca_actualizada) > 50:
        raise ValueError(
            "La marca no puede superar los 50 caracteres."
        )

    if not color_actualizado:
        raise ValueError(
            "El color del vehículo es obligatorio."
        )

    if len(color_actualizado) > 30:
        raise ValueError(
            "El color no puede superar los 30 caracteres."
        )

    if tipo_actualizado not in (
        "MOTO",
        "AUTOMOVIL",
        "CAMIONETA"
    ):
        raise ValueError(
            "El tipo de vehículo debe ser MOTO, AUTOMOVIL o CAMIONETA."
        )

    if mensualidad_actualizada not in (
        "ACTIVA",
        "INACTIVA"
    ):
        raise ValueError(
            "El estado de mensualidad debe ser ACTIVA o INACTIVA."
        )

    if (
        tipo_actualizado != vehiculo["tipo_vehiculo"]
        and existe_estancia_activa(vehiculo["id_vehiculo"])
    ):
        raise TipoVehiculoConEstanciaActivaError(
            "No es posible cambiar el tipo de vehículo mientras tenga una estancia activa."
        )

    return actualizar_vehiculo(
        placa,
        marca_actualizada,
        color_actualizado,
        tipo_actualizado,
        mensualidad_actualizada
    )
