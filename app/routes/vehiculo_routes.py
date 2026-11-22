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


# =========================================================
# CONSULTAR VEHICULO POR PLACA
# Iteraciones 1, 2 y 3
# =========================================================

@vehiculo_bp.route(
    "/api/vehiculos/<placa>",
    methods=["GET"]
)
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


# =========================================================
# VALIDAR INGRESO DE VEHICULO
# Iteraciones 1 y 3
# =========================================================

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


# =========================================================
# MODIFICAR DATOS ADMINISTRATIVOS DEL VEHICULO
# Iteraciones 2 y 3
#
# RN-38:
# La vigencia y cobertura no pueden modificarse
# manualmente, incluso por un administrador.
# =========================================================

@vehiculo_bp.route(
    "/api/vehiculos/<placa>",
    methods=["PUT"]
)
@requerir_roles("ADMINISTRADOR")
def actualizar_vehiculo(placa):

    try:

        datos = request.get_json(silent=True)

        if not isinstance(datos, dict):

            return {
                "estado": "error",
                "mensaje": (
                    "El cuerpo de la solicitud debe "
                    "ser un objeto JSON válido."
                )
            }, 422

        # Conservar la restricción de EA2.
        if "placa" in datos:

            return {
                "estado": "error",
                "mensaje": (
                    "La placa del vehículo no puede "
                    "modificarse."
                )
            }, 422

        # Proteger los atributos de la mensualidad.
        campos_mensualidad = {
            "estado_mensualidad",
            "fecha_inicio_mensualidad",
            "fecha_inicio",
            "fecha_corte",
            "dia_corte",
            "num_pagos",
            "mensualidad",
            "corte_esperado",
            "tarifa"
        }

        if campos_mensualidad.intersection(datos):

            return {
                "estado": "error",
                "mensaje": (
                    "La mensualidad no puede modificarse "
                    "manualmente. Su vigencia se determina "
                    "mediante los pagos registrados."
                )
            }, 422

        # Solo se permiten los campos administrativos.
        campos_permitidos = {
            "marca",
            "color",
            "tipo_vehiculo"
        }

        campos_no_permitidos = (
            set(datos) - campos_permitidos
        )

        if campos_no_permitidos:

            return {
                "estado": "error",
                "mensaje": (
                    "La solicitud contiene campos "
                    "no permitidos: "
                    + ", ".join(
                        sorted(campos_no_permitidos)
                    )
                    + "."
                )
            }, 422

        vehiculo = modificar_vehiculo(
            placa,
            marca=datos.get("marca"),
            color=datos.get("color"),
            tipo_vehiculo=datos.get("tipo_vehiculo")
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
            "mensaje": (
                "No fue posible modificar el vehículo."
            )
        }, 500