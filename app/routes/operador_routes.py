from flask import Blueprint
from app.auth_middleware import requerir_roles
from app.services.operador_service import obtener_operadores


operador_bp = Blueprint("operador", __name__)


@operador_bp.route("/api/operadores", methods=["GET"])
@requerir_roles("ADMINISTRADOR")
def listar_operadores():
    try:
        operadores = obtener_operadores()

        return {
            "estado": "ok",
            "cantidad": len(operadores),
            "operadores": operadores
        }

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible consultar los operadores."
        }, 500