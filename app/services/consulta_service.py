from app.repositories.estancia_repository import consultar_vehiculos_dentro
from app.repositories.celda_repository import consultar_estado_parqueadero

def obtener_vehiculos_dentro():
    vehiculos = consultar_vehiculos_dentro()

    return {
        "cantidad": len(vehiculos),
        "vehiculos": vehiculos
    }

def obtener_estado_parqueadero():
    estado_celdas = consultar_estado_parqueadero()
    vehiculos_dentro = consultar_vehiculos_dentro()

    return {
        "vehiculos_dentro": len(vehiculos_dentro),
        "celdas": estado_celdas
    }