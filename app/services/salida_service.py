from app.repositories.estancia_repository import registrar_salida


def crear_salida(placa, id_operador):
    placa = str(placa).strip()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    if id_operador is None:
        raise ValueError("El operador es obligatorio.")

    estancia = registrar_salida(
        placa=placa,
        id_operador=id_operador
    )

    return {
        "mensaje": "Salida registrada correctamente.",
        "placa": placa.upper(),
        "estancia": estancia
    }