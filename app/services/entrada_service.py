from app.repositories.estancia_repository import (
    registrar_entrada
)

from app.services.validacion_service import (
    validar_codigo_celda,
    validar_id_operador,
    validar_ingreso,
    validar_placa
)


def crear_entrada(
    placa,
    codigo_celda,
    id_operador
):
    """
    Gestiona el registro de entrada de un vehículo.

    Realiza una validación inicial de los datos y
    verifica las condiciones de ingreso.

    Iteración 3:
    La mensualidad debe encontrarse vigente para
    autorizar la entrada.

    La operación transaccional del repositorio vuelve
    a comprobar la cobertura, la estancia activa y
    la disponibilidad de la celda.

    El identificador del operador es suministrado
    por la ruta a partir de la sesión autenticada.

    Referencias:
    RF-I3-11, RN-29, RN-30 y HU-I3-05.
    """

    # =============================================
    # 1. VALIDAR DATOS DE LA SOLICITUD
    # =============================================

    placa = validar_placa(placa)

    codigo_celda = validar_codigo_celda(
        codigo_celda
    )

    id_operador = validar_id_operador(
        id_operador
    )

    # =============================================
    # 2. VALIDACION PREVIA DE INGRESO
    # =============================================

    validacion = validar_ingreso(placa)

    if not validacion["puede_ingresar"]:

        raise ValueError(
            validacion["motivo"]
        )

    vehiculo = validacion["vehiculo"]

    # =============================================
    # 3. REGISTRO TRANSACCIONAL
    # =============================================
    #
    # El repositorio vuelve a consultar la información
    # después de bloquear el vehículo.

    resultado = registrar_entrada(
        id_vehiculo=vehiculo["id_vehiculo"],
        codigo_celda=codigo_celda,
        id_operador=id_operador,
        tipo_vehiculo=vehiculo["tipo_vehiculo"]
    )

    # =============================================
    # 4. CONSTRUIR RESPUESTA
    # =============================================
    #
    # Se devuelve la información del vehículo obtenida
    # dentro de la transacción, en lugar de reutilizar
    # los datos de la consulta previa.
    #
    # Se conserva la estructura JSON de EA1 y EA2.

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