from flask import Blueprint, request

from app.services.vehiculo_service import (
    TipoVehiculoConEstanciaActivaError,
    VehiculoNoEncontradoError,
    consultar_vehiculo,
    modificar_vehiculo,
)
from app.services.validacion_service import validar_ingreso
from app.auth_middleware import requerir_roles

vehiculo_bp = Blueprint("vehiculo", __name__)


@vehiculo_bp.route("/api/vehiculos/<placa>", methods=["GET"])
@requerir_roles("ADMINISTRADOR", "OPERADOR")
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
@requerir_roles("ADMINISTRADOR", "OPERADOR")
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

@vehiculo_bp.route("/api/vehiculos/<placa>", methods=["PUT"])
@requerir_roles("ADMINISTRADOR")
def actualizar_vehiculo(placa):
    try:
        datos = request.get_json(silent=True) or {}

        if "placa" in datos:
            return {
                "estado": "error",
                "mensaje": "La placa del vehículo no puede modificarse."
            }, 422

        vehiculo = modificar_vehiculo(
            placa,
            marca=datos.get("marca"),
            color=datos.get("color"),
            tipo_vehiculo=datos.get("tipo_vehiculo"),
            estado_mensualidad=datos.get("estado_mensualidad")
        )

        return {
            "estado": "ok",
            "vehiculo": vehiculo
        }, 200

    except VehiculoNoEncontradoError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except TipoVehiculoConEstanciaActivaError as error:
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
            "mensaje": "No fue posible modificar el vehículo."
        }, 500
