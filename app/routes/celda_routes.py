from flask import Blueprint, request

from app.services.celda_service import (
    CeldaEstadoConflictoError,
    CeldaNoEncontradaError,
    listar_celdas,
    obtener_celdas_disponibles,
    poner_celda_disponible,
    poner_celda_fuera_de_servicio,
)

from app.auth_middleware import requerir_roles

celda_bp = Blueprint("celda", __name__)


@celda_bp.route("/api/celdas/disponibles", methods=["GET"])
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def consultar_celdas_disponibles():
    try:
        tipo_vehiculo = request.args.get("tipo_vehiculo", "")

        celdas = obtener_celdas_disponibles(tipo_vehiculo)

        return {
            "estado": "ok",
            "cantidad": len(celdas),
            "celdas": celdas
        }

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400

@celda_bp.route("/api/celdas", methods=["GET"])
@requerir_roles("ADMINISTRADOR")
def consultar_todas_las_celdas():
    try:
        estado = request.args.get("estado")
        tipo = request.args.get("tipo")
        busqueda = request.args.get("q")

        celdas = listar_celdas(
            estado=estado,
            tipo=tipo,
            busqueda=busqueda
        )

        return {
            "estado": "ok",
            "cantidad": len(celdas),
            "celdas": celdas
        }, 200

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 422

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible consultar las celdas."
        }, 500

@celda_bp.route(
    "/api/celdas/<codigo>/deshabilitar",
    methods=["PATCH"]
)
@requerir_roles("ADMINISTRADOR")
def deshabilitar_celda(codigo):
    try:
        celda = poner_celda_fuera_de_servicio(codigo)

        return {
            "estado": "ok",
            "celda": celda
        }, 200

    except CeldaNoEncontradaError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except CeldaEstadoConflictoError as error:
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
            "mensaje": "No fue posible deshabilitar la celda."
        }, 500


@celda_bp.route(
    "/api/celdas/<codigo>/habilitar",
    methods=["PATCH"]
)
@requerir_roles("ADMINISTRADOR")
def habilitar_celda(codigo):
    try:
        celda = poner_celda_disponible(codigo)

        return {
            "estado": "ok",
            "celda": celda
        }, 200

    except CeldaNoEncontradaError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except CeldaEstadoConflictoError as error:
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
            "mensaje": "No fue posible habilitar la celda."
        }, 500