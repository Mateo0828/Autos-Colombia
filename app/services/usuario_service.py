from werkzeug.security import generate_password_hash

from app.repositories.operador_repository import (
    actualizar_estado_usuario,
    actualizar_usuario,
    buscar_operador_por_id,
    buscar_operador_por_usuario,
    consultar_usuarios,
    contar_administradores_activos,
    crear_usuario as crear_usuario_repository,
)
from app.repositories.sesion_repository import revocar_sesiones_por_operador

class UsuarioDuplicadoError(Exception):
    pass

class UsuarioNoEncontradoError(Exception):
    pass

class UltimoAdministradorError(Exception):
    pass

class AutoInactivacionError(Exception):
    pass

def listar_usuarios():
    usuarios = consultar_usuarios()

    return [
        {
            "id_operador": usuario["id_operador"],
            "nombre": usuario["nombre"],
            "usuario": usuario["usuario"],
            "rol": usuario["rol"],
            "estado": usuario["estado"],
            "fecha_creacion": usuario["fecha_creacion"].isoformat()
        }
        for usuario in usuarios
    ]

def crear_usuario(nombre, usuario, password, rol):
    nombre = "" if nombre is None else str(nombre).strip()
    usuario = "" if usuario is None else str(usuario).strip().lower()
    password = "" if password is None else str(password)
    rol = "" if rol is None else str(rol).strip().upper()

    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    if not usuario:
        raise ValueError("El usuario es obligatorio.")

    if not password:
        raise ValueError("La contraseña es obligatoria.")

    if len(password) < 8:
        raise ValueError(
            "La contraseña debe tener mínimo 8 caracteres."
        )

    if rol not in ("ADMINISTRADOR", "OPERADOR"):
        raise ValueError(
            "El rol debe ser ADMINISTRADOR u OPERADOR."
        )

    if buscar_operador_por_usuario(usuario) is not None:
        raise UsuarioDuplicadoError(
            "El nombre de usuario ya se encuentra registrado."
        )

    password_hash = generate_password_hash(password)

    nuevo_usuario = crear_usuario_repository(
        nombre,
        usuario,
        password_hash,
        rol
    )

    return {
        "id_operador": nuevo_usuario["id_operador"],
        "nombre": nuevo_usuario["nombre"],
        "usuario": nuevo_usuario["usuario"],
        "rol": nuevo_usuario["rol"],
        "estado": nuevo_usuario["estado"],
        "fecha_creacion": nuevo_usuario["fecha_creacion"].isoformat()
    }

def modificar_usuario(
    id_operador,
    nombre=None,
    rol=None,
    password=None
):
    operador = buscar_operador_por_id(id_operador)

    if operador is None:
        raise UsuarioNoEncontradoError(
            "El usuario solicitado no existe."
        )

    nombre_actualizado = (
        operador["nombre"]
        if nombre is None
        else str(nombre).strip()
    )

    rol_actualizado = (
        operador["rol"]
        if rol is None
        else str(rol).strip().upper()
    )

    if not nombre_actualizado:
        raise ValueError("El nombre es obligatorio.")

    if rol_actualizado not in ("ADMINISTRADOR", "OPERADOR"):
        raise ValueError(
            "El rol debe ser ADMINISTRADOR u OPERADOR."
        )

    if (
        operador["rol"] == "ADMINISTRADOR"
        and operador["estado"] == "ACTIVO"
        and rol_actualizado != "ADMINISTRADOR"
        and contar_administradores_activos() <= 1
    ):
        raise UltimoAdministradorError(
            "No es posible modificar el rol del último administrador activo."
        )

    password_hash = None

    if password is not None:
        password = str(password)

        if len(password) < 8:
            raise ValueError(
                "La contraseña debe tener mínimo 8 caracteres."
            )

        password_hash = generate_password_hash(password)

    usuario_actualizado = actualizar_usuario(
        id_operador,
        nombre_actualizado,
        rol_actualizado,
        password_hash
    )

    return {
        "id_operador": usuario_actualizado["id_operador"],
        "nombre": usuario_actualizado["nombre"],
        "usuario": usuario_actualizado["usuario"],
        "rol": usuario_actualizado["rol"],
        "estado": usuario_actualizado["estado"],
        "fecha_creacion": usuario_actualizado["fecha_creacion"].isoformat()
    }

def cambiar_estado_usuario(
    id_operador,
    nuevo_estado,
    id_operador_actual
):
    operador = buscar_operador_por_id(id_operador)

    if operador is None:
        raise UsuarioNoEncontradoError(
            "El usuario solicitado no existe."
        )

    nuevo_estado = (
        ""
        if nuevo_estado is None
        else str(nuevo_estado).strip().upper()
    )

    if nuevo_estado not in ("ACTIVO", "INACTIVO"):
        raise ValueError(
            "El estado debe ser ACTIVO o INACTIVO."
        )

    if (
        id_operador == id_operador_actual
        and nuevo_estado == "INACTIVO"
    ):
        raise AutoInactivacionError(
            "No es posible inactivar el usuario de la sesión actual."
        )

    if (
        operador["rol"] == "ADMINISTRADOR"
        and operador["estado"] == "ACTIVO"
        and nuevo_estado == "INACTIVO"
        and contar_administradores_activos() <= 1
    ):
        raise UltimoAdministradorError(
            "No es posible inactivar el último administrador activo."
        )

    usuario_actualizado = actualizar_estado_usuario(
        id_operador,
        nuevo_estado
    )

    if nuevo_estado == "INACTIVO":
        revocar_sesiones_por_operador(id_operador)

    return {
        "id_operador": usuario_actualizado["id_operador"],
        "nombre": usuario_actualizado["nombre"],
        "usuario": usuario_actualizado["usuario"],
        "rol": usuario_actualizado["rol"],
        "estado": usuario_actualizado["estado"],
        "fecha_creacion": usuario_actualizado["fecha_creacion"].isoformat()
    }
