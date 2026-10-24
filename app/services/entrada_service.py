from app.repositories.estancia_repository import registrar_entrada
from app.services.validacion_service import validar_ingreso


def crear_entrada(placa, codigo_celda, id_operador):
    placa = str(placa).strip()
    codigo_celda = str(codigo_celda).strip()

    if not placa:
        raise ValueError("La placa es obligatoria.")

    if not codigo_celda:
        raise ValueError("La celda es obligatoria.")

    if id_operador is None:
        raise ValueError("El operador es obligatorio.")

    validacion = validar_ingreso(placa)

    if not validacion["puede_ingresar"]:
        raise ValueError(validacion["motivo"])

    vehiculo = validacion["vehiculo"]

    estancia = registrar_entrada(
        id_vehiculo=vehiculo["id_vehiculo"],
        codigo_celda=codigo_celda,
        id_operador=id_operador,
        tipo_vehiculo=vehiculo["tipo_vehiculo"]
    )

    return {
        "mensaje": "Entrada registrada correctamente.",
        "vehiculo": {
            "id_vehiculo": vehiculo["id_vehiculo"],
            "placa": vehiculo["placa"],
            "marca": vehiculo["marca"],
            "color": vehiculo["color"],
            "tipo_vehiculo": vehiculo["tipo_vehiculo"]
        },
        "estancia": estancia
    }