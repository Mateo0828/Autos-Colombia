from flask import Blueprint, request

from app.services.celda_service import obtener_celdas_disponibles


celda_bp = Blueprint("celda", __name__)


@celda_bp.route("/api/celdas/disponibles", methods=["GET"])
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