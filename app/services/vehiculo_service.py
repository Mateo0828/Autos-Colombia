from app.repositories.vehiculo_repository import (
    actualizar_vehiculo,
    buscar_por_placa,
    TipoVehiculoConEstanciaActivaError
)

from app.services.validacion_service import (
    validar_placa
)


# =========================================================
# EXCEPCIONES DEL SERVICIO
# =========================================================

class VehiculoNoEncontradoError(Exception):
    pass


# =========================================================
# CONSULTAR VEHICULO
# =========================================================

def consultar_vehiculo(placa):
    """
    Normaliza la placa y consulta la información
    del vehículo.
    """

    placa = validar_placa(placa)

    return buscar_por_placa(placa)


# =========================================================
# MODIFICAR VEHICULO
# =========================================================

def modificar_vehiculo(
    placa,
    marca=None,
    color=None,
    tipo_vehiculo=None
):
    """
    Gestiona la modificación administrativa del vehículo.

    Atributos permitidos:
    - Marca.
    - Color.
    - Tipo de vehículo.

    Iteración 3:
    La mensualidad no puede modificarse manualmente.

    La validación de estancia activa y la actualización
    se realizan dentro de una única transacción en el
    repositorio.

    Los atributos omitidos conservan su valor actual,
    incluso cuando existen modificaciones simultáneas.

    Referencias:
    RF-I3-15, RN-34 y RN-38.
    """

    # =============================================
    # 1. VALIDAR PLACA
    # =============================================

    placa = validar_placa(placa)

    # =============================================
    # 2. VALIDAR MARCA
    # =============================================

    if marca is not None:

        marca = str(marca).strip()

        if not marca:

            raise ValueError(
                "La marca del vehículo es obligatoria."
            )

        if len(marca) > 50:

            raise ValueError(
                "La marca no puede superar los "
                "50 caracteres."
            )

    # =============================================
    # 3. VALIDAR COLOR
    # =============================================

    if color is not None:

        color = str(color).strip()

        if not color:

            raise ValueError(
                "El color del vehículo es obligatorio."
            )

        if len(color) > 30:

            raise ValueError(
                "El color no puede superar los "
                "30 caracteres."
            )

    # =============================================
    # 4. VALIDAR TIPO DE VEHICULO
    # =============================================

    if tipo_vehiculo is not None:

        tipo_vehiculo = (
            str(tipo_vehiculo).strip().upper()
        )

        if tipo_vehiculo not in (
            "MOTO",
            "AUTOMOVIL",
            "CAMIONETA"
        ):

            raise ValueError(
                "El tipo de vehículo debe ser MOTO, "
                "AUTOMOVIL o CAMIONETA."
            )

    # =============================================
    # 5. ACTUALIZACION TRANSACCIONAL
    # =============================================
    #
    # No se realiza una consulta previa independiente
    # de la estancia activa.
    #
    # Esa comprobación se ejecuta bajo el bloqueo
    # del vehículo dentro del repositorio.

    resultado = actualizar_vehiculo(
        placa=placa,
        marca=marca,
        color=color,
        tipo_vehiculo=tipo_vehiculo
    )

    if resultado is None:

        raise VehiculoNoEncontradoError(
            "El vehículo solicitado no existe."
        )

    return resultado