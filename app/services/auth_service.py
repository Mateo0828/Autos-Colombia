import hashlib
import secrets
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from app.repositories.operador_repository import buscar_operador_por_usuario
from app.repositories.sesion_repository import (
    buscar_sesion_por_token_hash,
    crear_sesion,
    revocar_sesion_por_token_hash,
)

DURACION_SESION_HORAS = 8


def generar_token():
    return secrets.token_urlsafe(32)


def calcular_token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def iniciar_sesion(usuario, password):
    usuario = "" if usuario is None else str(usuario).strip().lower()
    password = "" if password is None else str(password)

    if not usuario:
        raise ValueError("El usuario es obligatorio.")

    if not password:
        raise ValueError("La contraseña es obligatoria.")

    operador = buscar_operador_por_usuario(usuario)

    if operador is None:
        return None

    if operador["estado"] != "ACTIVO":
        return None

    if not operador["password_hash"]:
        return None

    if not check_password_hash(
        operador["password_hash"],
        password
    ):
        return None

    token = generar_token()
    token_hash = calcular_token_hash(token)

    expira = datetime.now() + timedelta(
        hours=DURACION_SESION_HORAS
    )

    sesion = crear_sesion(
        token_hash,
        operador["id_operador"],
        expira
    )

    return {
        "token": token,
        "expira": sesion["expira"],
        "usuario": {
            "id_operador": operador["id_operador"],
            "nombre": operador["nombre"],
            "usuario": operador["usuario"],
            "rol": operador["rol"]
        }
    }

def validar_sesion(token):
    token = "" if token is None else str(token).strip()

    if not token:
        return None

    token_hash = calcular_token_hash(token)

    sesion = buscar_sesion_por_token_hash(token_hash)

    if sesion is None:
        return None

    if sesion["revocada"]:
        return None

    if sesion["expira"] <= datetime.now():
        return None

    if sesion["usuario"]["estado"] != "ACTIVO":
        return None

    return {
        "id_sesion": sesion["id_sesion"],
        "usuario": {
            "id_operador": sesion["usuario"]["id_operador"],
            "nombre": sesion["usuario"]["nombre"],
            "usuario": sesion["usuario"]["usuario"],
            "rol": sesion["usuario"]["rol"]
        }
    }

def cerrar_sesion(token):
    token = "" if token is None else str(token).strip()

    if not token:
        return False

    token_hash = calcular_token_hash(token)

    return revocar_sesion_por_token_hash(token_hash)
