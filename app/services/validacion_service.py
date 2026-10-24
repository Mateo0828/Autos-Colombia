from app.repositories.estancia_repository import existe_estancia_activa
from app.repositories.vehiculo_repository import buscar_por_placa


def validar_ingreso(placa):
    placa = placa.strip()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    vehiculo = buscar_por_placa(placa)

    if vehiculo is None:
        return {
            "puede_ingresar": False,
            "motivo": "El vehículo no se encuentra registrado.",
            "vehiculo": None,
            "validaciones": {
                "vehiculo_registrado": False,
                "mensualidad_activa": False,
                "sin_estancia_activa": False
            }
        }

    mensualidad_activa = (
        vehiculo["estado_mensualidad"] == "ACTIVA"
    )

    tiene_estancia_activa = existe_estancia_activa(
        vehiculo["id_vehiculo"]
    )

    sin_estancia_activa = not tiene_estancia_activa

    puede_ingresar = (
        mensualidad_activa
        and sin_estancia_activa
    )

    if not mensualidad_activa:
        motivo = "La mensualidad del vehículo se encuentra inactiva."
    elif tiene_estancia_activa:
        motivo = "El vehículo ya tiene una estancia activa."
    else:
        motivo = "El vehículo cumple las condiciones para ingresar."

    return {
        "puede_ingresar": puede_ingresar,
        "motivo": motivo,
        "vehiculo": vehiculo,
        "validaciones": {
            "vehiculo_registrado": True,
            "mensualidad_activa": mensualidad_activa,
            "sin_estancia_activa": sin_estancia_activa
        }
    }