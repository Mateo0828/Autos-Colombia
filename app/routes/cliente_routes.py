from flask import Blueprint, request

from app.auth_middleware import requerir_roles

from app.services.cliente_service import (
    ClienteNoEncontradoError,
    DocumentoDuplicadoError,
    consultar_cliente,
    modificar_cliente,
)


cliente_bp = Blueprint("clientes", __name__)


@cliente_bp.route("/api/clientes/<int:id_cliente>", methods=["GET"])
@requerir_roles("ADMINISTRADOR")
def obtener_cliente(id_cliente):
    try:
        cliente = consultar_cliente(id_cliente)

        return {
            "estado": "ok",
            "cliente": cliente
        }, 200

    except ClienteNoEncontradoError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible consultar el cliente."
        }, 500

@cliente_bp.route("/api/clientes/<int:id_cliente>", methods=["PUT"])
@requerir_roles("ADMINISTRADOR")
def actualizar_cliente(id_cliente):
    try:
        datos = request.get_json(silent=True) or {}

        cliente = modificar_cliente(
            id_cliente,
            documento=datos.get("documento"),
            nombre=datos.get("nombre")
        )

        return {
            "estado": "ok",
            "cliente": cliente
        }, 200

    except ClienteNoEncontradoError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except DocumentoDuplicadoError as error:
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
            "mensaje": "No fue posible modificar el cliente."
        }, 500
