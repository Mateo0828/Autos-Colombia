from flask import Blueprint, request

from app.services.reasignacion_service import (
    cambiar_celda
)

from app.auth_middleware import requerir_roles


reasignacion_bp = Blueprint(
    "reasignacion",
    __name__
)


@reasignacion_bp.route(
    "/api/estancias/<placa>/reasignar-celda",
    methods=["PUT"]
)
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def reasignar_celda_estancia(placa):
    """
    Reasigna la celda de un vehículo que posee
    una estancia activa.

    Conserva las reglas funcionales de la Iteración 1
    e incorpora el control de autenticación y roles
    utilizado desde la Iteración 2.

    La operación no modifica la mensualidad ni
    el historial de pagos del vehículo.
    """

    try:

        datos = request.get_json(silent=True)

        if not isinstance(datos, dict) or not datos:

            return {
                "estado": "error",
                "mensaje": (
                    "Debe enviar los datos de la nueva celda."
                )
            }, 400

        resultado = cambiar_celda(
            placa=placa,
            nueva_celda=datos.get(
                "nueva_celda",
                ""
            )
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
            "mensaje": (
                "No fue posible reasignar la celda."
            )
        }, 500