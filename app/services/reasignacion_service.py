from app.repositories.estancia_repository import reasignar_celda
from app.services.validacion_service import (
    validar_codigo_celda,
    validar_placa
)


def cambiar_celda(placa, nueva_celda):
    placa = validar_placa(placa)
    nueva_celda = validar_codigo_celda(nueva_celda)

    resultado = reasignar_celda(
        placa=placa,
        nueva_celda=nueva_celda
    )

    return {
        "mensaje": "Celda reasignada correctamente.",
        **resultado
    }