from flask import Blueprint

from app.services.vehiculo_service import consultar_vehiculo
from app.services.validacion_service import validar_ingreso

vehiculo_bp = Blueprint("vehiculo", __name__)


@vehiculo_bp.route("/api/vehiculos/<placa>", methods=["GET"])
def obtener_vehiculo(placa):
    try:
        vehiculo = consultar_vehiculo(placa)

        if vehiculo is None:
            return {
                "estado": "error",
                "mensaje": "Vehículo no encontrado"
            }, 404

        return {
            "estado": "ok",
            "vehiculo": vehiculo
        }

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400
    
@vehiculo_bp.route(
    "/api/vehiculos/<placa>/validar-ingreso",
    methods=["GET"]
)
def validar_ingreso_vehiculo(placa):
    try:
        resultado = validar_ingreso(placa)

        return {
            "estado": "ok",
            **resultado
        }

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400