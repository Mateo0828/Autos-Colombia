"""
Autos Colombia - Iteración 3.

Infraestructura reutilizable para las pruebas de
integración y regresión del backend.

Utiliza:
- unittest
- Flask Test Client
- PostgreSQL
- psycopg
- unittest.mock

Las pruebas de integración requieren activación
explícita y una base de datos aislada.
"""

import os
import unittest

from contextlib import contextmanager, ExitStack
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from uuid import uuid4

from dotenv import dotenv_values
from psycopg.rows import dict_row


# =========================================================
# CONFIGURACION GENERAL
# =========================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

BASE_PRUEBAS = "autos_colombia_ea3_pruebas"

E2E_HABILITADAS = (
    os.getenv("RUN_E2E") == "1"
)

USUARIOS_PRUEBA = {
    "admin": "E2E_ADMIN_PASSWORD",
    "operador1": "E2E_OPERADOR1_PASSWORD",
    "operador2": "E2E_OPERADOR2_PASSWORD"
}

TABLAS_CONTROL = {
    "clientes": ("cliente", "id_cliente"),
    "vehiculos": ("vehiculo", "id_vehiculo"),
    "pagos": ("pago", "id_pago"),
    "celdas": ("celda", "id_celda"),
    "estancias": ("estancia", "id_estancia")
}


# =========================================================
# PROTECCION DEL ENTORNO DE PRUEBAS
# =========================================================

def verificar_base_pruebas():
    """
    Comprueba que las pruebas de integración estén
    habilitadas expresamente y que la conexión real
    corresponda exclusivamente a la base autorizada.

    No modifica variables de entorno ni archivos.
    """

    if not E2E_HABILITADAS:

        raise RuntimeError(
            "Las pruebas E2E no están habilitadas. "
            "Configure RUN_E2E=1."
        )

    if os.getenv("DB_NAME") != BASE_PRUEBAS:

        raise RuntimeError(
            "DB_NAME debe corresponder exclusivamente "
            "a autos_colombia_ea3_pruebas."
        )

    # Importación diferida para mantener independientes
    # las pruebas unitarias de PostgreSQL.

    from app.database import get_connection

    with get_connection() as conexion:

        with conexion.cursor() as cursor:

            cursor.execute(
                "SELECT current_database();"
            )

            base_real = cursor.fetchone()[0]

            if base_real != BASE_PRUEBAS:

                raise RuntimeError(
                    "La conexión no corresponde a "
                    "la base de pruebas autorizada."
                )

    return base_real


# =========================================================
# CREDENCIALES EXTERNAS
# =========================================================

def obtener_credencial(usuario):
    """
    Obtiene las credenciales desde variables de
    entorno o desde el archivo .env local.

    No almacena contraseñas en el código fuente.
    """

    variable = USUARIOS_PRUEBA.get(usuario)

    if variable is None:

        raise ValueError(
            f"Usuario de pruebas no reconocido: {usuario}"
        )

    configuracion = dotenv_values(
        RAIZ_PROYECTO / ".env"
    )

    password = (
        os.getenv(variable)
        or configuracion.get(variable)
    )

    if not password:

        raise RuntimeError(
            f"Falta configurar la variable {variable}."
        )

    return password


# =========================================================
# CONSULTAS DIRECTAS A POSTGRESQL
# =========================================================

def consultar(sql, parametros=()):
    """
    Ejecuta una consulta de verificación en una
    transacción de solo lectura.

    Comprueba el nombre real de la base antes
    de ejecutar la consulta solicitada.
    """

    if not E2E_HABILITADAS:

        raise RuntimeError(
            "Las pruebas E2E no están habilitadas."
        )

    if os.getenv("DB_NAME") != BASE_PRUEBAS:

        raise RuntimeError(
            "Base de datos no autorizada."
        )

    from app.database import get_connection

    with get_connection() as conexion:

        conexion.read_only = True

        with conexion.cursor(
            row_factory=dict_row
        ) as cursor:

            cursor.execute(
                "SELECT current_database() AS base;"
            )

            if cursor.fetchone()["base"] != BASE_PRUEBAS:

                raise RuntimeError(
                    "Base de datos no autorizada."
                )

            cursor.execute(sql, parametros)

            return cursor.fetchall()


def consultar_uno(sql, parametros=()):
    """
    Devuelve un único registro o None.

    Rechaza consultas que obtengan más de
    un registro cuando se espera solamente uno.
    """

    filas = consultar(sql, parametros)

    if len(filas) > 1:

        raise AssertionError(
            "La consulta devolvió más de un registro."
        )

    return filas[0] if filas else None


def capturar_estado():
    """
    Obtiene una copia lógica de las tablas
    principales para comparar su integridad.

    No incluye sesiones de autenticación,
    ya que las pruebas pueden crearlas y revocarlas.
    """

    return {
        nombre: consultar(
            f"SELECT * FROM {tabla} ORDER BY {pk};"
        )
        for nombre, (tabla, pk)
        in TABLAS_CONTROL.items()
    }


def consultar_vehiculo(placa):

    return consultar_uno(
        """
        SELECT *
        FROM vehiculo
        WHERE UPPER(placa) = UPPER(%s);
        """,
        (placa,)
    )


def consultar_pagos(placa):

    return consultar(
        """
        SELECT p.*
        FROM pago p
        INNER JOIN vehiculo v
            ON p.id_vehiculo = v.id_vehiculo
        WHERE UPPER(v.placa) = UPPER(%s)
        ORDER BY p.id_pago;
        """,
        (placa,)
    )


def consultar_celda(codigo):

    return consultar_uno(
        """
        SELECT *
        FROM celda
        WHERE UPPER(codigo) = UPPER(%s);
        """,
        (codigo,)
    )


def consultar_estancia(id_estancia):

    return consultar_uno(
        """
        SELECT *
        FROM estancia
        WHERE id_estancia = %s;
        """,
        (id_estancia,)
    )


def consultar_estancias_activas(placa=None):

    if placa is None:

        return consultar(
            """
            SELECT *
            FROM estancia
            WHERE estado = 'ACTIVA'
            ORDER BY id_estancia;
            """
        )

    return consultar(
        """
        SELECT e.*
        FROM estancia e
        INNER JOIN vehiculo v
            ON e.id_vehiculo = v.id_vehiculo
        WHERE e.estado = 'ACTIVA'
          AND UPPER(v.placa) = UPPER(%s)
        ORDER BY e.id_estancia;
        """,
        (placa,)
    )


def seleccionar_celda(
    tipo_vehiculo,
    excluir=()
):
    """
    Selecciona una celda disponible y compatible,
    sin depender de identificadores fijos.
    """

    tipo_celda = (
        "MOTO"
        if tipo_vehiculo == "MOTO"
        else "CARRO"
    )

    filas = consultar(
        """
        SELECT codigo
        FROM celda
        WHERE tipo_celda = %s
          AND estado = 'DISPONIBLE'
        ORDER BY codigo;
        """,
        (tipo_celda,)
    )

    for fila in filas:

        codigo = fila["codigo"]

        if codigo not in excluir:

            return codigo

    raise AssertionError(
        "No existe una celda disponible y compatible."
    )


# =========================================================
# VALIDACION DE RESPUESTAS HTTP
# =========================================================

def verificar_respuesta(
    respuesta,
    codigo_esperado
):
    """
    Verifica el código HTTP y la estructura JSON.

    No imprime respuestas de autenticación ni
    información sensible.
    """

    if respuesta.status_code != codigo_esperado:

        raise AssertionError(
            f"HTTP esperado: {codigo_esperado}. "
            f"HTTP recibido: {respuesta.status_code}."
        )

    cuerpo = respuesta.get_json(silent=True)

    if not isinstance(cuerpo, dict):

        raise AssertionError(
            "La respuesta no contiene un objeto JSON."
        )

    if codigo_esperado >= 400:

        if cuerpo.get("estado") != "error":

            raise AssertionError(
                "La respuesta de error es inconsistente."
            )

    return cuerpo


# =========================================================
# GENERACION DE DATOS DE PRUEBA
# =========================================================

def generar_placa_prueba():
    """
    Genera una placa alfanumérica independiente.

    Evita colisiones con los vehículos existentes
    y respeta el límite de diez caracteres.
    """

    for _ in range(100):

        placa = (
            "T" + uuid4().hex[:9].upper()
        )

        if consultar_vehiculo(placa) is None:

            return placa

    raise RuntimeError(
        "No fue posible generar una placa de prueba."
    )


def generar_documento_prueba():
    """
    Genera un documento alfanumérico de prueba
    de máximo veinte caracteres.
    """

    for _ in range(100):

        documento = (
            "TEST" + uuid4().hex[:16].upper()
        )

        cliente = consultar_uno(
            """
            SELECT id_cliente
            FROM cliente
            WHERE documento = %s;
            """,
            (documento,)
        )

        if cliente is None:

            return documento

    raise RuntimeError(
        "No fue posible generar un documento de prueba."
    )


# =========================================================
# SIMULACION COORDINADA DE FECHAS
# =========================================================

@contextmanager
def simular_fecha(fecha):
    """
    Simula la fecha de referencia de las reglas
    de mensualidad.

    No modifica el reloj del sistema ni los
    registros de PostgreSQL.

    No debe utilizarse simultáneamente con otras
    pruebas que dependan de la fecha real.
    """

    verificar_base_pruebas()

    import app.services.mensualidad_service as ms
    import app.services.pago_service as ps

    import app.repositories.cliente_repository as cr
    import app.repositories.vehiculo_repository as vr
    import app.repositories.estancia_repository as er

    modulos = (
        ms,
        ps,
        cr,
        vr,
        er
    )

    with ExitStack() as stack:

        for modulo in modulos:

            if hasattr(
                modulo,
                "fecha_actual_colombia"
            ):

                stack.enter_context(
                    patch.object(
                        modulo,
                        "fecha_actual_colombia",
                        return_value=fecha
                    )
                )

        if ms.fecha_actual_colombia() != fecha:

            raise AssertionError(
                "La simulación de fecha no fue aplicada."
            )

        if ps.fecha_actual_colombia() != fecha:

            raise AssertionError(
                "La fecha del servicio de pagos "
                "no fue simulada correctamente."
            )

        yield


# =========================================================
# ENTORNO REUTILIZABLE DE INTEGRACION
# =========================================================

class EntornoE2E:
    """
    Administra solicitudes HTTP, autenticación,
    datos de prueba y limpieza de las estancias
    generadas durante una ejecución.
    """

    def __init__(self):

        verificar_base_pruebas()

        from app import create_app

        self.app = create_app()

        self.sesiones = {}

        self.vehiculos_prueba = set()

        self.estancias_prueba = set()

        self.tiempos = []


    # -----------------------------------------------------
    # SOLICITUDES HTTP
    # -----------------------------------------------------

    def solicitud(
        self,
        metodo,
        ruta,
        usuario=None,
        datos=None,
        headers=None
    ):
        """
        Ejecuta una solicitud contra Flask Test Client.

        Crea un cliente independiente para cada
        operación, facilitando también las pruebas
        concurrentes.
        """

        verificar_base_pruebas()

        encabezados = dict(headers or {})

        if usuario is not None:

            sesion = self.sesiones.get(usuario)

            if sesion is None:

                raise RuntimeError(
                    f"No existe sesión para {usuario}."
                )

            encabezados["Authorization"] = (
                "Bearer " + sesion["token"]
            )

        argumentos = {
            "headers": encabezados
        }

        if datos is not None:

            argumentos["json"] = datos

        with self.app.test_client() as cliente:

            inicio = perf_counter()

            respuesta = cliente.open(
                ruta,
                method=metodo,
                **argumentos
            )

            duracion = perf_counter() - inicio

        self.tiempos.append({
            "metodo": metodo,
            "ruta": ruta,
            "http": respuesta.status_code,
            "segundos": duracion
        })

        return respuesta


    # -----------------------------------------------------
    # AUTENTICACION
    # -----------------------------------------------------

    def autenticar(self, usuario):

        if usuario in self.sesiones:

            return dict(
                self.sesiones[usuario]["usuario"]
            )

        password = obtener_credencial(usuario)

        respuesta = self.solicitud(
            "POST",
            "/api/auth/login",
            datos={
                "usuario": usuario,
                "password": password
            }
        )

        cuerpo = verificar_respuesta(
            respuesta,
            200
        )

        self.sesiones[usuario] = {
            "token": cuerpo["token"],
            "usuario": cuerpo["usuario"]
        }

        return dict(cuerpo["usuario"])


    def cerrar_sesion(self, usuario):

        if usuario not in self.sesiones:

            return

        respuesta = self.solicitud(
            "POST",
            "/api/auth/logout",
            usuario=usuario
        )

        verificar_respuesta(
            respuesta,
            200
        )

        del self.sesiones[usuario]


    # -----------------------------------------------------
    # REGISTRO DE VEHICULOS
    # -----------------------------------------------------

    def crear_vehiculo_prueba(
        self,
        tipo_vehiculo="AUTOMOVIL",
        usuario="operador1",
        documento=None,
        nombre="Cliente Prueba E2E"
    ):
        """
        Crea un vehículo mediante la API real.

        Cada vehículo tiene una placa independiente
        y debe comenzar sin cobertura registrada.
        """

        placa = generar_placa_prueba()

        if documento is None:

            documento = generar_documento_prueba()

        # Registrar la placa antes de ejecutar la
        # solicitud para facilitar la limpieza ante
        # una comprobación posterior fallida.

        self.vehiculos_prueba.add(placa)

        respuesta = self.solicitud(
            "POST",
            "/api/registros",
            usuario=usuario,
            datos={
                "documento": documento,
                "nombre": nombre,
                "placa": placa,
                "marca": "Marca E2E",
                "color": "Gris",
                "tipo_vehiculo": tipo_vehiculo
            }
        )

        cuerpo = verificar_respuesta(
            respuesta,
            201
        )

        vehiculo = consultar_vehiculo(placa)

        if vehiculo is None:

            raise AssertionError(
                "El vehículo no fue persistido."
            )

        if vehiculo["fecha_corte"] is not None:

            raise AssertionError(
                "El vehículo nuevo tiene cobertura."
            )

        if (
            vehiculo["fecha_inicio_mensualidad"]
            is not None
        ):

            raise AssertionError(
                "El vehículo nuevo tiene fecha inicial."
            )

        if consultar_pagos(placa):

            raise AssertionError(
                "El vehículo nuevo contiene pagos."
            )

        return {
            "placa": placa,
            "documento": documento,
            "id_vehiculo": vehiculo["id_vehiculo"],
            "id_cliente": vehiculo["id_cliente"],
            "respuesta": cuerpo
        }


    # -----------------------------------------------------
    # CONSULTA Y PROYECCION DE MENSUALIDADES
    # -----------------------------------------------------

    def mensualidad(
        self,
        placa,
        usuario="operador1",
        fecha_pago=None,
        esperado=200
    ):

        ruta = f"/api/mensualidades/{placa}"

        if fecha_pago is not None:

            from urllib.parse import urlencode

            ruta += "?" + urlencode({
                "fecha_pago": str(fecha_pago)
            })

        respuesta = self.solicitud(
            "GET",
            ruta,
            usuario=usuario
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    # -----------------------------------------------------
    # REGISTRO DE PAGOS
    # -----------------------------------------------------

    def registrar_pago(
        self,
        placa,
        fecha_pago,
        corte_esperado,
        usuario="operador1",
        esperado=201
    ):

        respuesta = self.solicitud(
            "POST",
            "/api/pagos",
            usuario=usuario,
            datos={
                "placa": placa,

                "fecha_pago": str(fecha_pago),

                "corte_esperado": (
                    str(corte_esperado)
                    if corte_esperado is not None
                    else None
                )
            }
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    def historial(
        self,
        placa,
        usuario="operador1",
        esperado=200
    ):

        respuesta = self.solicitud(
            "GET",
            f"/api/vehiculos/{placa}/pagos",
            usuario=usuario
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    # -----------------------------------------------------
    # VALIDACION DE INGRESO
    # -----------------------------------------------------

    def validar_ingreso(
        self,
        placa,
        usuario="operador1",
        esperado=200
    ):

        respuesta = self.solicitud(
            "GET",
            f"/api/vehiculos/{placa}/validar-ingreso",
            usuario=usuario
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    # -----------------------------------------------------
    # REGISTRO DE ENTRADAS
    # -----------------------------------------------------

    def registrar_entrada(
        self,
        placa,
        codigo_celda,
        usuario="operador1",
        esperado=201
    ):

        # Las operaciones de escritura gestionadas
        # por esta función solamente pueden utilizar
        # vehículos creados por el entorno de pruebas.

        if placa not in self.vehiculos_prueba:

            raise RuntimeError(
                "La placa no pertenece a este "
                "entorno de pruebas."
            )

        respuesta = self.solicitud(
            "POST",
            "/api/entradas",
            usuario=usuario,
            datos={
                "placa": placa,
                "codigo_celda": codigo_celda
            }
        )

        if respuesta.status_code == 201:

            cuerpo = respuesta.get_json()

            self.estancias_prueba.add(
                cuerpo["estancia"]["id_estancia"]
            )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    # -----------------------------------------------------
    # REGISTRO DE SALIDAS
    # -----------------------------------------------------

    def registrar_salida(
        self,
        placa,
        usuario="operador1",
        esperado=200
    ):

        if placa not in self.vehiculos_prueba:

            raise RuntimeError(
                "La placa no pertenece a este "
                "entorno de pruebas."
            )

        respuesta = self.solicitud(
            "POST",
            "/api/salidas",
            usuario=usuario,
            datos={
                "placa": placa
            }
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    # -----------------------------------------------------
    # LIMPIEZA DE SEGURIDAD
    # -----------------------------------------------------

    def limpiar(self):
        """
        Finaliza únicamente estancias de vehículos
        generados por esta instancia.

        Cierra las sesiones de prueba.

        Conserva clientes, vehículos, pagos e historial
        producidos durante la ejecución.
        """

        errores = []

        try:

            usuario = None

            for candidato in (
                "operador1",
                "admin",
                "operador2"
            ):

                if candidato in self.sesiones:

                    usuario = candidato

                    break

            for placa in sorted(
                self.vehiculos_prueba
            ):

                try:

                    activas = (
                        consultar_estancias_activas(
                            placa
                        )
                    )

                    if not activas:

                        continue

                    if usuario is None:

                        raise RuntimeError(
                            "No hay una sesión disponible "
                            "para finalizar la estancia."
                        )

                    self.registrar_salida(
                        placa,
                        usuario=usuario
                    )

                    if consultar_estancias_activas(
                        placa
                    ):

                        raise AssertionError(
                            "La estancia no fue finalizada."
                        )

                except Exception as error:

                    errores.append(
                        f"Limpieza {placa}: {error}"
                    )

        finally:

            for usuario in list(self.sesiones):

                try:

                    self.cerrar_sesion(usuario)

                except Exception as error:

                    errores.append(
                        f"Sesión {usuario}: {error}"
                    )

        if errores:

            raise AssertionError(
                "Errores de limpieza: "
                + " | ".join(errores)
            )


# =========================================================
# CLASE BASE PARA PRUEBAS UNITTTEST
# =========================================================

@unittest.skipUnless(
    E2E_HABILITADAS,
    "Pruebas E2E deshabilitadas. "
    "Configure RUN_E2E=1."
)
class BasePruebaE2E(unittest.TestCase):
    """
    Clase base que utilizarán los módulos de
    integración de pagos, operaciones y concurrencia.

    Cada caso dispone de un entorno independiente.
    """

    def setUp(self):

        self.entorno = EntornoE2E()

        # Garantizar limpieza incluso cuando una
        # prueba o una autenticación produzca un error.

        self.addCleanup(
            self.entorno.limpiar
        )

        self.operador = self.entorno.autenticar(
            "operador1"
        )

        self.admin = self.entorno.autenticar(
            "admin"
        )