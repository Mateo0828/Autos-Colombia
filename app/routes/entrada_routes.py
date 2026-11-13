from flask import Blueprint, g, request
from psycopg.errors import UniqueViolation

from app.services.entrada_service import crear_entrada
from app.auth_middleware import requerir_roles

entrada_bp = Blueprint("entrada", __name__)


@entrada_bp.route("/api/entradas", methods=["POST"])
@requerir_roles("ADMINISTRADOR", "OPERADOR")
def registrar_entrada():
    try:
        datos = request.get_json(silent=True)

        if not datos:
            return {
                "estado": "error",
                "mensaje": "Debe enviar los datos de la entrada."
            }, 400

        resultado = crear_entrada(
            placa=datos.get("placa", ""),
            codigo_celda=datos.get("codigo_celda", ""),
            id_operador=g.usuario_actual["id_operador"]
        )

        return {
            "estado": "ok",
            **resultado
        }, 201

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 400
    
    except UniqueViolation:
        return {
            "estado": "error",
            "mensaje": (
                "No fue posible registrar la entrada porque "
                "el vehículo o la celda ya se encuentran en uso."
            )
        }, 409   
    
    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible registrar la entrada."
        }, 500