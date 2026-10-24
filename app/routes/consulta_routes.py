from flask import Blueprint

from app.services.consulta_service import (
    obtener_estado_parqueadero,
    obtener_vehiculos_dentro
)

consulta_bp = Blueprint("consulta", __name__)


@consulta_bp.route("/api/estancias/activas", methods=["GET"])
def listar_vehiculos_dentro():
    try:
        resultado = obtener_vehiculos_dentro()

        return {
            "estado": "ok",
            **resultado
        }

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible consultar los vehículos dentro."
        }, 500

@consulta_bp.route("/api/parqueadero/estado", methods=["GET"])
def consultar_estado_general():
    try:
        resultado = obtener_estado_parqueadero()

        return {
            "estado": "ok",
            **resultado
        }

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible consultar el estado del parqueadero."
        }, 500