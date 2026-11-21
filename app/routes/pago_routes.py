
from flask import Blueprint, request, g, current_app

from app.auth_middleware import requerir_roles

from app.services.pago_service import (
    consultar_mensualidad,
    registrar_pago,
    consultar_historial,
    VehiculoNoEncontradoError,
    ConflictoPagoError
)


# =========================================================
# AUTOS COLOMBIA
# Iteracion 3 - Gestion de pagos y mensualidades
# =========================================================

pago_bp = Blueprint("pagos", __name__)


# =========================================================
# CONSULTAR MENSUALIDAD Y PREVISUALIZAR PAGO
# UC-I3-01 / HU-I3-01
# =========================================================

@pago_bp.route(
    "/api/mensualidades/<placa>",
    methods=["GET"]
)
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def obtener_mensualidad(placa):

    try:

        fecha_pago = request.args.get(
            "fecha_pago"
        )

        resultado = consultar_mensualidad(
            placa,
            fecha_pago
        )

        return {
            "estado": "ok",
            **resultado
        }, 200

    except VehiculoNoEncontradoError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except ValueError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 422

    except Exception:

        current_app.logger.exception(
            "Error al consultar la mensualidad."
        )

        return {
            "estado": "error",
            "mensaje": (
                "No fue posible consultar la mensualidad."
            )
        }, 500


# =========================================================
# REGISTRAR PRIMER PAGO O RENOVACION
# UC-I3-02 / UC-I3-03
# HU-I3-02 / HU-I3-03
# =========================================================

@pago_bp.route(
    "/api/pagos",
    methods=["POST"]
)
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def crear_pago():

    try:

        datos = request.get_json(
            silent=True
        )

        resultado = registrar_pago(
            datos,
            g.usuario_actual
        )

        return {
            "estado": "ok",
            **resultado
        }, 201

    except VehiculoNoEncontradoError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except ConflictoPagoError as error:

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

        current_app.logger.exception(
            "Error al registrar el pago."
        )

        return {
            "estado": "error",
            "mensaje": (
                "No fue posible registrar el pago."
            )
        }, 500


# =========================================================
# CONSULTAR HISTORIAL DE PAGOS
# UC-I3-04 / HU-I3-04
# =========================================================

@pago_bp.route(
    "/api/vehiculos/<placa>/pagos",
    methods=["GET"]
)
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def obtener_historial_pagos(placa):

    try:

        resultado = consultar_historial(
            placa
        )

        return {
            "estado": "ok",
            **resultado
        }, 200

    except VehiculoNoEncontradoError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except ValueError as error:

        return {
            "estado": "error",
            "mensaje": str(error)
        }, 422

    except Exception:

        current_app.logger.exception(
            "Error al consultar el historial de pagos."
        )

        return {
            "estado": "error",
            "mensaje": (
                "No fue posible consultar el historial de pagos."
            )
        }, 500
