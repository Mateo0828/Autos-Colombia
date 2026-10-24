from app.repositories.vehiculo_repository import buscar_por_placa


def consultar_vehiculo(placa):
    placa = placa.strip()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    return buscar_por_placa(placa)