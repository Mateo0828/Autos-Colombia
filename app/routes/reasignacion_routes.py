from flask import Blueprint, request

from app.services.reasignacion_service import cambiar_celda


reasignacion_bp = Blueprint("reasignacion", __name__)


@reasignacion_bp.route(
    "/api/estancias/<placa>/reasignar-celda",
    methods=["PUT"]
)
def reasignar_celda_estancia(placa):
    try:
        datos = request.get_json(silent=True)

        if not datos:
            return {
                "estado": "error",
                "mensaje": "Debe enviar los datos de la nueva celda."
            }, 400

        resultado = cambiar_celda(
            placa=placa,
            nueva_celda=datos.get("nueva_celda", "")
        )

        return {
            "estado": "ok",
            **resultado
        }, 200

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible reasignar la celda."
        }, 500