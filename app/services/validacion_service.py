from app.repositories.estancia_repository import existe_estancia_activa
from app.repositories.vehiculo_repository import buscar_por_placa
import re


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

def validar_id_operador(id_operador):
    if id_operador is None:
        raise ValueError("El operador es obligatorio.")

    if isinstance(id_operador, bool):
        raise ValueError("El identificador del operador no es válido.")

    try:
        id_operador = int(id_operador)
    except (TypeError, ValueError):
        raise ValueError(
            "El identificador del operador debe ser un número entero."
        )

    if id_operador <= 0:
        raise ValueError(
            "El identificador del operador debe ser mayor que cero."
        )

    return id_operador

def validar_placa(placa):
    placa = str(placa).strip().upper()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    if len(placa) > 10:
        raise ValueError("La placa no puede superar los 10 caracteres.")

    if not re.fullmatch(r"[A-Z0-9]+", placa):
        raise ValueError(
            "La placa solo puede contener letras y números."
        )

    return placa


def validar_codigo_celda(codigo_celda):
    codigo_celda = str(codigo_celda).strip().upper()

    if not codigo_celda:
        raise ValueError("La celda es obligatoria.")

    if len(codigo_celda) > 10:
        raise ValueError(
            "El código de la celda no puede superar los 10 caracteres."
        )

    if not re.fullmatch(r"[A-Z0-9]+", codigo_celda):
        raise ValueError(
            "El código de la celda solo puede contener letras y números."
        )

    return codigo_celda