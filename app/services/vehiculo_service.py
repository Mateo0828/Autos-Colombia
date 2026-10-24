from app.repositories.vehiculo_repository import buscar_por_placa


def consultar_vehiculo(placa):
    from app.services.validacion_service import validar_placa
    placa = validar_placa(placa)

    return buscar_por_placa(placa)