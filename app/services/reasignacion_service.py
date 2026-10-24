from app.repositories.estancia_repository import reasignar_celda


def cambiar_celda(placa, nueva_celda):
    placa = str(placa).strip()
    nueva_celda = str(nueva_celda).strip()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    if not nueva_celda:
        raise ValueError("La nueva celda es obligatoria.")

    resultado = reasignar_celda(
        placa=placa,
        nueva_celda=nueva_celda
    )

    return {
        "mensaje": "Celda reasignada correctamente.",
        **resultado
    }