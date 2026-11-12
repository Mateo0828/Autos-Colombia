from flask import Blueprint, request

from app.auth_middleware import requerir_roles
from app.services.registro_service import (
    PlacaDuplicadaError,
    crear_registro,
)


registro_bp = Blueprint("registros", __name__)


@registro_bp.route("/api/registros", methods=["POST"])
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def registrar_cliente_y_vehiculo():
    try:
        datos = request.get_json(silent=True) or {}

        resultado = crear_registro(
            datos.get("documento"),
            datos.get("nombre"),
            datos.get("placa"),
            datos.get("marca"),
            datos.get("color"),
            datos.get("tipo_vehiculo")
        )

        return {
            "estado": "ok",
            **resultado
        }, 201

    except PlacaDuplicadaError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 409

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 422

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible registrar el cliente y el vehículo."
        }, 500
