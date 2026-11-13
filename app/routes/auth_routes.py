from flask import Blueprint, request

from app.services.auth_service import (
    cerrar_sesion,
    iniciar_sesion,
    validar_sesion,
)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    try:
        datos = request.get_json(silent=True) or {}

        resultado = iniciar_sesion(
            datos.get("usuario"),
            datos.get("password")
        )

        if resultado is None:
            return {
                "estado": "error",
                "mensaje": "Usuario o contraseña incorrectos."
            }, 401

        return {
            "estado": "ok",
            "token": resultado["token"],
            "expira": resultado["expira"].isoformat(),
            "usuario": resultado["usuario"]
        }, 200

    except ValueError as error:
        return {
            "estado": "error",
            "mensaje": str(error)
        }, 422

    except Exception:
        return {
            "estado": "error",
            "mensaje": "No fue posible iniciar sesión."
        }, 500

@auth_bp.route("/api/auth/me", methods=["GET"])
def obtener_usuario_actual():
    autorizacion = request.headers.get("Authorization", "")

    if not autorizacion.startswith("Bearer "):
        return {
            "estado": "error",
            "mensaje": "Sesión no válida o expirada."
        }, 401

    token = autorizacion[7:].strip()

    sesion = validar_sesion(token)

    if sesion is None:
        return {
            "estado": "error",
            "mensaje": "Sesión no válida o expirada."
        }, 401

    return {
        "estado": "ok",
        "usuario": sesion["usuario"]
    }, 200

@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    autorizacion = request.headers.get("Authorization", "")

    if not autorizacion.startswith("Bearer "):
        return {
            "estado": "error",
            "mensaje": "Sesión no válida o expirada."
        }, 401

    token = autorizacion[7:].strip()

    sesion = validar_sesion(token)

    if sesion is None:
        return {
            "estado": "error",
            "mensaje": "Sesión no válida o expirada."
        }, 401

    cerrar_sesion(token)

    return {
        "estado": "ok",
        "mensaje": "Sesión cerrada correctamente."
    }, 200
