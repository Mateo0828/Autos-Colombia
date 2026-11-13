from functools import wraps

from flask import g, request

from app.services.auth_service import validar_sesion


def requerir_roles(*roles_permitidos):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
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

            usuario = sesion["usuario"]

            if usuario["rol"] not in roles_permitidos:
                return {
                    "estado": "error",
                    "mensaje": "No tiene permisos para realizar esta acción."
                }, 403

            g.usuario_actual = usuario
            g.token_actual = token

            return funcion(*args, **kwargs)

        return envoltura

    return decorador
