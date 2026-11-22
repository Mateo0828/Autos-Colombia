from app.repositories.estancia_repository import (
    registrar_entrada,
    consultar_celda_para_entrada
)

from app.services.validacion_service import (
    validar_codigo_celda,
    validar_id_operador,
    validar_ingreso,
    validar_placa
)


# =========================================================
# VALIDACION PREVIA DE CELDA
# =========================================================

def validar_celda_para_entrada(
    codigo_celda,
    tipo_vehiculo
):
    """
    Comprueba las condiciones iniciales de la celda.

    Los incumplimientos detectados en esta etapa
    corresponden a rechazos ordinarios de la operación.

    El repositorio vuelve a comprobar las condiciones
    después de adquirir los bloqueos transaccionales.
    """

    celda = consultar_celda_para_entrada(
        codigo_celda
    )

    if celda is None:

        raise ValueError(
            "La celda no existe."
        )

    if celda["estado"] == "OCUPADA":

        raise ValueError(
            "La celda seleccionada se encuentra ocupada."
        )

    if celda["estado"] == "FUERA_DE_SERVICIO":

        raise ValueError(
            "La celda seleccionada se encuentra "
            "fuera de servicio."
        )

    if celda["estado"] != "DISPONIBLE":

        raise ValueError(
            "La celda seleccionada no se encuentra "
            "disponible."
        )

    tipo_requerido = (
        "MOTO"
        if tipo_vehiculo == "MOTO"
        else "CARRO"
    )

    if celda["tipo_celda"] != tipo_requerido:

        raise ValueError(
            "La celda seleccionada no es compatible "
            "con el tipo de vehículo."
        )


# =========================================================
# REGISTRO DE ENTRADA
# =========================================================

def crear_entrada(
    placa,
    codigo_celda,
    id_operador
):
    """
    Gestiona el registro de entrada de un vehículo.

    Iteración 1:
    Conserva las condiciones operativas del parqueadero.

    Iteración 2:
    El responsable se obtiene de la sesión autenticada.

    Iteración 3:
    Comprueba la vigencia de la mensualidad y conserva
    la integridad de la operación ante solicitudes
    concurrentes.

    La validación inicial permite identificar rechazos
    ordinarios. La revalidación transaccional detecta
    conflictos posteriores.

    Referencias:
    RF-I3-11, RN-29, RN-30, RN-34,
    RNF-I3-07, HU-I3-05 y DS-01.
    """

    # =====================================================
    # 1. VALIDAR DATOS
    # =====================================================

    placa = validar_placa(
        placa
    )

    codigo_celda = validar_codigo_celda(
        codigo_celda
    )

    id_operador = validar_id_operador(
        id_operador
    )

    # =====================================================
    # 2. VALIDAR CONDICIONES DEL VEHICULO
    # =====================================================

    validacion = validar_ingreso(
        placa
    )

    if not validacion["puede_ingresar"]:

        raise ValueError(
            validacion["motivo"]
        )

    vehiculo = validacion["vehiculo"]

    # =====================================================
    # 3. VALIDAR DISPONIBILIDAD INICIAL DE CELDA
    # =====================================================

    validar_celda_para_entrada(
        codigo_celda=codigo_celda,
        tipo_vehiculo=vehiculo["tipo_vehiculo"]
    )

    # =====================================================
    # 4. REGISTRO TRANSACCIONAL
    # =====================================================
    #
    # El repositorio bloquea el vehículo y la celda.
    #
    # Comprueba nuevamente la vigencia, la existencia
    # de una estancia activa y la disponibilidad de
    # la celda antes de persistir la entrada.

    resultado = registrar_entrada(
        id_vehiculo=vehiculo["id_vehiculo"],
        codigo_celda=codigo_celda,
        id_operador=id_operador,
        tipo_vehiculo=vehiculo["tipo_vehiculo"]
    )

    # =====================================================
    # 5. CONSTRUIR RESPUESTA
    # =====================================================
    #
    # Conserva la estructura JSON utilizada desde EA1.
    # Los datos proceden de la transacción confirmada.

    vehiculo_actualizado = resultado["vehiculo"]

    estancia = {
        clave: valor
        for clave, valor in resultado.items()
        if clave != "vehiculo"
    }

    return {
        "mensaje": (
            "Entrada registrada correctamente."
        ),

        "vehiculo": vehiculo_actualizado,

        "estancia": estancia
    }