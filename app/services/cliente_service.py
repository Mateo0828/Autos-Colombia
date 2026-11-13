import re

from app.repositories.cliente_repository import (
    actualizar_cliente,
    buscar_cliente_por_documento,
    buscar_cliente_por_id,
)

class ClienteNoEncontradoError(Exception):
    pass

class DocumentoDuplicadoError(Exception):
    pass


def consultar_cliente(id_cliente):
    cliente = buscar_cliente_por_id(id_cliente)

    if cliente is None:
        raise ClienteNoEncontradoError(
            "El cliente solicitado no existe."
        )

    return cliente

def modificar_cliente(
    id_cliente,
    documento=None,
    nombre=None
):
    cliente = buscar_cliente_por_id(id_cliente)

    if cliente is None:
        raise ClienteNoEncontradoError(
            "El cliente solicitado no existe."
        )

    documento_actualizado = (
        cliente["documento"]
        if documento is None
        else str(documento).strip()
    )

    nombre_actualizado = (
        cliente["nombre"]
        if nombre is None
        else str(nombre).strip()
    )

    if not documento_actualizado:
        raise ValueError(
            "El documento del cliente es obligatorio."
        )

    if len(documento_actualizado) > 20:
        raise ValueError(
            "El documento no puede superar los 20 caracteres."
        )

    if not re.fullmatch(
        r"[A-Za-z0-9]+",
        documento_actualizado
    ):
        raise ValueError(
            "El documento solo puede contener letras y números."
        )

    if not nombre_actualizado:
        raise ValueError(
            "El nombre del cliente es obligatorio."
        )

    if len(nombre_actualizado) > 100:
        raise ValueError(
            "El nombre del cliente no puede superar los 100 caracteres."
        )

    cliente_con_documento = buscar_cliente_por_documento(
        documento_actualizado
    )

    if (
        cliente_con_documento is not None
        and cliente_con_documento["id_cliente"] != id_cliente
    ):
        raise DocumentoDuplicadoError(
            "El documento ya se encuentra registrado para otro cliente."
        )

    cliente_actualizado = actualizar_cliente(
        id_cliente,
        documento_actualizado,
        nombre_actualizado
    )

    return {
        "id_cliente": cliente_actualizado["id_cliente"],
        "documento": cliente_actualizado["documento"],
        "nombre": cliente_actualizado["nombre"]
    }
