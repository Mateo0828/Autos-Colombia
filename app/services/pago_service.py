
from datetime import date

from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation

from app.database import get_connection

from app.repositories.pago_repository import (
    buscar_mensualidad,
    insertar_pago,
    actualizar_cobertura,
    consultar_historial_pagos
)

from app.services.mensualidad_service import (
    fecha_actual_colombia,
    obtener_tarifa,
    validar_fecha_pago,
    calcular_estado_mensualidad,
    proyectar_pago
)

from app.services.validacion_service import validar_placa


# =========================================================
# EXCEPCIONES DE LA GESTION DE PAGOS
# =========================================================

class VehiculoNoEncontradoError(Exception):
    pass


class ConflictoPagoError(Exception):
    pass


MENSAJE_CONFLICTO = (
    "La mensualidad ya fue actualizada; consulte de nuevo."
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def _validar_placa(placa):

    if not isinstance(placa, str):
        raise ValueError("La placa es obligatoria.")

    return validar_placa(placa)


def _fecha_iso(fecha):

    if fecha is None:
        return None

    return fecha.isoformat()


def _validar_corte_esperado(valor):

    # El primer pago no posee un corte anterior.
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise ValueError(
            "El corte esperado debe ser una fecha o null."
        )

    try:

        fecha = date.fromisoformat(valor)

        if fecha.isoformat() != valor:
            raise ValueError

        return fecha

    except ValueError:

        raise ValueError(
            "El corte esperado debe tener el formato YYYY-MM-DD."
        )


def _validar_datos_pago(datos):

    if not isinstance(datos, dict):
        raise ValueError(
            "Los datos del pago deben enviarse en formato JSON."
        )

    campos_permitidos = {
        "placa",
        "fecha_pago",
        "corte_esperado"
    }

    campos_recibidos = set(datos)

    campos_adicionales = (
        campos_recibidos - campos_permitidos
    )

    if campos_adicionales:

        raise ValueError(
            "Campos no autorizados: "
            + ", ".join(sorted(campos_adicionales))
            + "."
        )

    campos_faltantes = (
        campos_permitidos - campos_recibidos
    )

    if campos_faltantes:

        raise ValueError(
            "Campos obligatorios faltantes: "
            + ", ".join(sorted(campos_faltantes))
            + "."
        )


def _verificar_vehiculo(vehiculo):

    if vehiculo is None:

        raise VehiculoNoEncontradoError(
            "El vehículo no se encuentra registrado."
        )


# =========================================================
# CONSTRUIR RESPUESTAS
# Formato acordado para la integracion con el frontend.
# =========================================================

def _formatear_mensualidad(
    fecha_inicio,
    fecha_corte,
    num_pagos,
    hoy
):

    return {
        "estado_mensualidad": calcular_estado_mensualidad(
            fecha_corte,
            hoy
        ),

        "fecha_inicio": _fecha_iso(fecha_inicio),

        "dia_corte": (
            fecha_inicio.day
            if fecha_inicio is not None
            else None
        ),

        "fecha_corte": _fecha_iso(fecha_corte),

        "num_pagos": num_pagos
    }


def _formatear_proyeccion(proyeccion):

    return {
        "tipo": proyeccion["tipo"],

        "fecha_pago": _fecha_iso(
            proyeccion["fecha_pago"]
        ),

        "valor": proyeccion["valor"],

        "periodo_inicio": _fecha_iso(
            proyeccion["periodo_inicio"]
        ),

        "periodo_fin": _fecha_iso(
            proyeccion["periodo_fin"]
        ),

        "corte_esperado": _fecha_iso(
            proyeccion["corte_esperado"]
        ),

        "estado_resultante": (
            proyeccion["estado_resultante"]
        ),

        "advertencia": proyeccion["advertencia"]
    }


def _formatear_pago(pago, responsable):

    return {
        "id_pago": pago["id_pago"],

        "valor": int(pago["valor"]),

        "fecha_pago": _fecha_iso(
            pago["fecha_pago"]
        ),

        "fecha_registro": _fecha_iso(
            pago["fecha_registro"]
        ),

        "periodo_inicio": _fecha_iso(
            pago["periodo_inicio"]
        ),

        "periodo_fin": _fecha_iso(
            pago["periodo_fin"]
        ),

        "registrado_por": {
            "id_operador": responsable["id_operador"],
            "usuario": responsable["usuario"],
            "nombre": responsable["nombre"]
        }
    }


# =========================================================
# CONSULTAR MENSUALIDAD
# UC-I3-01 / HU-I3-01
# =========================================================

def consultar_mensualidad(placa, fecha_pago=None):

    placa = _validar_placa(placa)

    hoy = fecha_actual_colombia()

    if fecha_pago is None:

        fecha_pago = hoy

    else:

        fecha_pago = validar_fecha_pago(
            fecha_pago,
            hoy
        )

    with get_connection() as conexion:

        with conexion.cursor(row_factory=dict_row) as cursor:

            vehiculo = buscar_mensualidad(
                cursor,
                placa
            )

    _verificar_vehiculo(vehiculo)

    proyeccion = proyectar_pago(
        tipo_vehiculo=vehiculo["tipo_vehiculo"],
        fecha_pago=fecha_pago,
        fecha_inicio_mensualidad=(
            vehiculo["fecha_inicio_mensualidad"]
        ),
        fecha_corte=vehiculo["fecha_corte"],
        num_pagos=vehiculo["num_pagos"],
        hoy=hoy
    )

    mensualidad = _formatear_mensualidad(
        fecha_inicio=vehiculo["fecha_inicio_mensualidad"],
        fecha_corte=vehiculo["fecha_corte"],
        num_pagos=vehiculo["num_pagos"],
        hoy=hoy
    )

    return {
        "vehiculo": {
            "id_vehiculo": vehiculo["id_vehiculo"],
            "placa": vehiculo["placa"],
            "marca": vehiculo["marca"],
            "color": vehiculo["color"],
            "tipo_vehiculo": vehiculo["tipo_vehiculo"]
        },

        "cliente": {
            "id_cliente": vehiculo["id_cliente"],
            "documento": vehiculo["documento_cliente"],
            "nombre": vehiculo["nombre_cliente"]
        },

        "tarifa": obtener_tarifa(
            vehiculo["tipo_vehiculo"]
        ),

        **mensualidad,

        "proximo_pago": _formatear_proyeccion(
            proyeccion
        )
    }


# =========================================================
# REGISTRAR PRIMER PAGO O RENOVACION
# UC-I3-02 / UC-I3-03
# HU-I3-02 / HU-I3-03
# =========================================================

def registrar_pago(datos, usuario_actual):

    _validar_datos_pago(datos)

    placa = _validar_placa(datos["placa"])

    hoy = fecha_actual_colombia()

    fecha_pago = validar_fecha_pago(
        datos["fecha_pago"],
        hoy
    )

    corte_esperado = _validar_corte_esperado(
        datos["corte_esperado"]
    )

    # El usuario proviene de la sesion autenticada.
    # Nunca se recibe su identificador desde el body.

    id_operador = usuario_actual["id_operador"]

    try:

        with get_connection() as conexion:

            with conexion.cursor(
                row_factory=dict_row
            ) as cursor:

                # -----------------------------------------
                # 1. BLOQUEAR Y CONSULTAR VEHICULO
                # -----------------------------------------

                vehiculo = buscar_mensualidad(
                    cursor,
                    placa,
                    bloquear=True
                )

                _verificar_vehiculo(vehiculo)

                # -----------------------------------------
                # 2. CONTROL DE CONCURRENCIA
                # -----------------------------------------

                if corte_esperado != vehiculo["fecha_corte"]:

                    raise ConflictoPagoError(
                        MENSAJE_CONFLICTO
                    )

                # -----------------------------------------
                # 3. CALCULAR TARIFA Y PERIODO
                # -----------------------------------------

                proyeccion = proyectar_pago(
                    tipo_vehiculo=vehiculo["tipo_vehiculo"],
                    fecha_pago=fecha_pago,
                    fecha_inicio_mensualidad=(
                        vehiculo["fecha_inicio_mensualidad"]
                    ),
                    fecha_corte=vehiculo["fecha_corte"],
                    num_pagos=vehiculo["num_pagos"],
                    hoy=hoy
                )

                # -----------------------------------------
                # 4. INSERTAR EL PAGO
                # -----------------------------------------

                pago = insertar_pago(
                    cursor=cursor,

                    id_vehiculo=vehiculo["id_vehiculo"],

                    id_cliente=vehiculo["id_cliente"],

                    id_operador=id_operador,

                    valor=proyeccion["valor"],

                    fecha_pago=fecha_pago,

                    periodo_inicio=(
                        proyeccion["periodo_inicio"]
                    ),

                    periodo_fin=(
                        proyeccion["periodo_fin"]
                    )
                )

                # -----------------------------------------
                # 5. ACTUALIZAR COBERTURA
                # -----------------------------------------

                cobertura = actualizar_cobertura(
                    cursor=cursor,

                    id_vehiculo=vehiculo["id_vehiculo"],

                    fecha_inicio_mensualidad=(
                        proyeccion["fecha_inicio"]
                    ),

                    fecha_corte=(
                        proyeccion["periodo_fin"]
                    )
                )

                # -----------------------------------------
                # 6. CONSTRUIR RESPUESTA
                # -----------------------------------------

                pago_respuesta = _formatear_pago(
                    pago,
                    usuario_actual
                )

                pago_respuesta.update({
                    "placa": vehiculo["placa"],
                    "id_cliente": vehiculo["id_cliente"],
                    "tipo": proyeccion["tipo"]
                })

                mensualidad = _formatear_mensualidad(
                    fecha_inicio=(
                        cobertura["fecha_inicio_mensualidad"]
                    ),
                    fecha_corte=cobertura["fecha_corte"],
                    num_pagos=(
                        proyeccion["num_pagos_resultante"]
                    ),
                    hoy=hoy
                )

                resultado = {
                    "mensaje": "Pago registrado correctamente.",

                    "pago": pago_respuesta,

                    "mensualidad": mensualidad,

                    "advertencia": proyeccion["advertencia"]
                }

            # El gestor de contexto de psycopg confirma
            # la transaccion al finalizar correctamente.
            #
            # Ante una excepcion, revierte los cambios.

        return resultado

    except UniqueViolation as error:

        if (
            error.diag.constraint_name
            == "uq_pago_vehiculo_periodo"
        ):

            raise ConflictoPagoError(
                MENSAJE_CONFLICTO
            ) from error

        raise


# =========================================================
# CONSULTAR HISTORIAL DE PAGOS
# UC-I3-04 / HU-I3-04
# =========================================================

def consultar_historial(placa):

    placa = _validar_placa(placa)

    with get_connection() as conexion:

        with conexion.cursor(row_factory=dict_row) as cursor:

            vehiculo = buscar_mensualidad(
                cursor,
                placa
            )

            _verificar_vehiculo(vehiculo)

            pagos = consultar_historial_pagos(
                cursor,
                vehiculo["id_vehiculo"]
            )

    historial = []

    for pago in pagos:

        responsable = {
            "id_operador": pago["id_operador"],
            "usuario": pago["usuario_operador"],
            "nombre": pago["nombre_operador"]
        }

        historial.append(
            _formatear_pago(
                pago,
                responsable
            )
        )

    return {
        "placa": vehiculo["placa"],
        "cantidad": len(historial),
        "pagos": historial
    }
