from flask import Blueprint, request

from app.services.salida_service import crear_salida


salida_bp = Blueprint("salida", __name__)


@salida_bp.route("/api/salidas", methods=["POST"])
def registrar_salida():
    try:
        datos = request.get_json(silent=True)

        if not datos:
            return {
                "estado": "error",
                "mensaje": "Debe enviar los datos de la salida."
            }, 400

        resultado = crear_salida(
            placa=datos.get("placa", ""),
            id_operador=datos.get("id_operador")
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
            "mensaje": "No fue posible registrar la salida."
        }, 500