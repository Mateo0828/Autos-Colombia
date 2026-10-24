from app.repositories.estancia_repository import registrar_salida
from app.services.validacion_service import (
    validar_id_operador,
    validar_placa
)

def crear_salida(placa, id_operador):
    placa = validar_placa(placa)
    id_operador = validar_id_operador(id_operador)

    estancia = registrar_salida(
        placa=placa,
        id_operador=id_operador
    )

    return {
        "mensaje": "Salida registrada correctamente.",
        "placa": placa.upper(),
        "estancia": estancia
    }