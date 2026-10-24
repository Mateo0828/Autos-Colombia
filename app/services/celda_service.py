from app.repositories.celda_repository import consultar_disponibles


def obtener_celdas_disponibles(tipo_vehiculo):
    tipo_vehiculo = tipo_vehiculo.upper().strip()

    tipos_validos = ["MOTO", "AUTOMOVIL", "CAMIONETA"]

    if tipo_vehiculo not in tipos_validos:
        raise ValueError("Tipo de vehículo no válido.")

    return consultar_disponibles(tipo_vehiculo)