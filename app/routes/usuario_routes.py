from flask import Blueprint, g, request

from app.auth_middleware import requerir_roles

from app.services.usuario_service import (
    AutoInactivacionError,
    UltimoAdministradorError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
    cambiar_estado_usuario,
    crear_usuario,
    listar_usuarios,
    modificar_usuario,
)

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/api/usuarios", methods=["GET"])
@requerir_roles("ADMINISTRADOR")
def consultar_usuarios():
    usuarios = listar_usuarios()

    return {
        "estado": "ok",
        "usuarios": usuarios
    }, 200

@usuario_bp.route("/api/usuarios", methods=["POST"])
@requerir_roles("ADMINISTRADOR")
def registrar_usuario():
    try:
        datos = request.get_json(silent=True) or {}

        usuario = crear_usuario(
            datos.get("nombre"),
            datos.get("usuario"),
            datos.get("password"),
            datos.get("rol")
        )

        return {
            "estado": "ok",
            "usuario": usuario
        }, 201

    except UsuarioDuplicadoError as error:
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
            "mensaje": "No fue posible registrar el usuario."
        }, 500

@usuario_bp.route("/api/usuarios/<int:id_operador>", methods=["PUT"])
@requerir_roles("ADMINISTRADOR")
def actualizar_usuario(id_operador):
    try:
        datos = request.get_json(silent=True) or {}

        if "usuario" in datos:
            return {
                "estado": "error",
                "mensaje": "El nombre de usuario no puede modificarse."
            }, 422

        usuario = modificar_usuario(
            id_operador,
            nombre=datos.get("nombre"),
            rol=datos.get("rol"),
            password=datos.get("password")
        )

        return {
            "estado": "ok",
            "usuario": usuario
        }, 200

    except UsuarioNoEncontradoError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except UltimoAdministradorError as error:
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
            "mensaje": "No fue posible modificar el usuario."
        }, 500

@usuario_bp.route(
    "/api/usuarios/<int:id_operador>/estado",
    methods=["PATCH"]
)
@requerir_roles("ADMINISTRADOR")
def actualizar_estado_usuario(id_operador):
    try:
        datos = request.get_json(silent=True) or {}

        usuario = cambiar_estado_usuario(
            id_operador,
            datos.get("estado"),
            g.usuario_actual["id_operador"]
        )

        return {
            "estado": "ok",
            "usuario": usuario
        }, 200

    except UsuarioNoEncontradoError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 404

    except AutoInactivacionError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 409

    except UltimoAdministradorError as error:
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
            "mensaje": "No fue posible actualizar el estado del usuario."
        }, 500
