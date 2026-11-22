"""
Autos Colombia - Iteración 3.

Pruebas complementarias de concurrencia e integridad
del registro de entradas.

Verifican la correspondencia entre DS-01 y el
contrato HTTP implementado.

Casos:
- CO-01: Concurrencia por vehículo.
- CO-02: Concurrencia por celda.
- CO-03: Rechazo ordinario por estancia activa.
- CO-04: Rechazo ordinario por celda ocupada.
- CO-05: Cambio concurrente del estado de una celda.
- CO-06: Revalidación final de vigencia e integridad.

Las transacciones se ejecutan realmente en PostgreSQL.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from tests.e2e_helpers import (
    BasePruebaE2E,
    capturar_estado,
    consultar_vehiculo,
    consultar_pagos,
    consultar_celda,
    consultar_estancia,
    consultar_estancias_activas,
    seleccionar_celda,
    verificar_respuesta
)

from app.services.mensualidad_service import (
    fecha_actual_colombia
)

import app.services.entrada_service as entrada_service

import app.repositories.estancia_repository as estancia_repository


# =========================================================
# PRUEBAS COMPLEMENTARIAS DE ENTRADAS
# =========================================================

class TestConcurrenciaEntradas(BasePruebaE2E):

    def setUp(self):

        super().setUp()

        self.hoy = fecha_actual_colombia()

        self.operador2 = self.entorno.autenticar(
            "operador2"
        )


    # =====================================================
    # FUNCIONES AUXILIARES
    # =====================================================

    def crear_vehiculo_vigente(
        self,
        tipo="MOTO"
    ):
        """
        Crea un vehículo independiente y registra
        su primer pago mediante la API real.
        """

        registro = self.entorno.crear_vehiculo_prueba(
            tipo_vehiculo=tipo
        )

        placa = registro["placa"]

        pago = self.entorno.registrar_pago(
            placa=placa,
            fecha_pago=self.hoy,
            corte_esperado=None
        )

        self.assertEqual(
            pago["mensualidad"]["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertTrue(
            self.entorno.validar_ingreso(placa)[
                "puede_ingresar"
            ]
        )

        return placa


    def solicitar_entrada(
        self,
        placa,
        codigo_celda,
        usuario
    ):
        """
        Ejecuta la solicitud sin asumir previamente
        cuál será el código HTTP recibido.
        """

        return self.entorno.solicitud(
            "POST",
            "/api/entradas",
            usuario=usuario,
            datos={
                "placa": placa,
                "codigo_celda": codigo_celda
            }
        )


    def ejecutar_entradas_concurrentes(
        self,
        solicitud_a,
        solicitud_b
    ):
        """
        Sincroniza ambas solicitudes inmediatamente
        después de superar las validaciones previas.

        La función original del repositorio conserva
        sus transacciones y bloqueos reales.
        """

        barrera = Barrier(2)

        registrar_original = (
            entrada_service.registrar_entrada
        )

        def registrar_sincronizado(
            *args,
            **kwargs
        ):

            barrera.wait(timeout=15)

            return registrar_original(
                *args,
                **kwargs
            )

        with patch.object(
            entrada_service,
            "registrar_entrada",
            side_effect=registrar_sincronizado
        ):

            with ThreadPoolExecutor(
                max_workers=2
            ) as ejecutor:

                futuro_a = ejecutor.submit(
                    self.solicitar_entrada,
                    *solicitud_a
                )

                futuro_b = ejecutor.submit(
                    self.solicitar_entrada,
                    *solicitud_b
                )

                respuesta_a = futuro_a.result(
                    timeout=30
                )

                respuesta_b = futuro_b.result(
                    timeout=30
                )

        respuestas = (
            respuesta_a,
            respuesta_b
        )

        self.assertEqual(
            sorted(
                respuesta.status_code
                for respuesta in respuestas
            ),
            [201, 409]
        )

        exitosa = next(
            respuesta
            for respuesta in respuestas
            if respuesta.status_code == 201
        )

        conflicto = next(
            respuesta
            for respuesta in respuestas
            if respuesta.status_code == 409
        )

        cuerpo_exitoso = verificar_respuesta(
            exitosa,
            201
        )

        cuerpo_conflicto = verificar_respuesta(
            conflicto,
            409
        )

        return (
            cuerpo_exitoso,
            cuerpo_conflicto
        )


    def verificar_integridad_final(
        self,
        antes,
        ids_nuevos
    ):
        """
        Comprueba que solamente se hayan creado
        las estancias esperadas.

        Los clientes, vehículos, pagos y celdas
        deben conservar su estado anterior.
        """

        despues = capturar_estado()

        for tabla in (
            "clientes",
            "vehiculos",
            "pagos",
            "celdas"
        ):

            self.assertEqual(
                despues[tabla],
                antes[tabla],
                f"Se modificó inesperadamente: {tabla}"
            )

        anteriores = {
            estancia["id_estancia"]: estancia
            for estancia in antes["estancias"]
        }

        actuales = {
            estancia["id_estancia"]: estancia
            for estancia in despues["estancias"]
        }

        for identificador, estancia in anteriores.items():

            self.assertEqual(
                actuales[identificador],
                estancia
            )

        nuevos = (
            set(actuales)
            - set(anteriores)
        )

        self.assertEqual(
            nuevos,
            set(ids_nuevos)
        )

        for identificador in nuevos:

            self.assertEqual(
                actuales[identificador]["estado"],
                "FINALIZADA"
            )

            self.assertIsNotNone(
                actuales[identificador][
                    "fecha_hora_salida"
                ]
            )

            self.assertIsNotNone(
                actuales[identificador][
                    "id_operador_salida"
                ]
            )

        self.assertEqual(
            consultar_estancias_activas(),
            []
        )


    # =====================================================
    # CO-01 - MISMO VEHICULO, DIFERENTES CELDAS
    # =====================================================

    def test_co01_concurrencia_mismo_vehiculo(self):

        placa = self.crear_vehiculo_vigente()

        celda_a = seleccionar_celda(
            "MOTO"
        )

        celda_b = seleccionar_celda(
            "MOTO",
            excluir=(celda_a,)
        )

        antes = capturar_estado()

        exitoso, conflicto = (
            self.ejecutar_entradas_concurrentes(
                (
                    placa,
                    celda_a,
                    "operador1"
                ),
                (
                    placa,
                    celda_b,
                    "operador2"
                )
            )
        )

        self.assertIn(
            "estancia activa",
            conflicto["mensaje"].lower()
        )

        estancia = exitoso["estancia"]

        id_estancia = estancia["id_estancia"]

        celda_ganadora = estancia["celda"]["codigo"]

        celda_perdedora = (
            celda_b
            if celda_ganadora == celda_a
            else celda_a
        )

        self.assertEqual(
            exitoso["vehiculo"]["placa"],
            placa
        )

        activas = consultar_estancias_activas(
            placa
        )

        self.assertEqual(
            len(activas),
            1
        )

        self.assertEqual(
            activas[0]["id_estancia"],
            id_estancia
        )

        self.assertEqual(
            consultar_celda(celda_ganadora)["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            consultar_celda(celda_perdedora)["estado"],
            "DISPONIBLE"
        )

        operador_esperado = (
            self.operador["id_operador"]
            if celda_ganadora == celda_a
            else self.operador2["id_operador"]
        )

        self.assertEqual(
            consultar_estancia(id_estancia)[
                "id_operador_entrada"
            ],
            operador_esperado
        )

        self.entorno.registrar_salida(
            placa,
            usuario="admin"
        )

        self.verificar_integridad_final(
            antes,
            [id_estancia]
        )

        print(
            "\nCO-01:",
            "HTTP 201 y 409;",
            "una estancia;",
            "integridad conservada."
        )


    # =====================================================
    # CO-02 - DIFERENTES VEHICULOS, MISMA CELDA
    # =====================================================

    def test_co02_concurrencia_misma_celda(self):

        placa_a = self.crear_vehiculo_vigente()

        placa_b = self.crear_vehiculo_vigente()

        celda = seleccionar_celda(
            "MOTO"
        )

        antes = capturar_estado()

        exitoso, conflicto = (
            self.ejecutar_entradas_concurrentes(
                (
                    placa_a,
                    celda,
                    "operador1"
                ),
                (
                    placa_b,
                    celda,
                    "operador2"
                )
            )
        )

        self.assertIn(
            "ocupada",
            conflicto["mensaje"].lower()
        )

        placa_ganadora = exitoso["vehiculo"]["placa"]

        placa_perdedora = (
            placa_b
            if placa_ganadora == placa_a
            else placa_a
        )

        id_estancia = exitoso[
            "estancia"
        ]["id_estancia"]

        self.assertIn(
            placa_ganadora,
            (placa_a, placa_b)
        )

        self.assertEqual(
            len(
                consultar_estancias_activas(
                    placa_ganadora
                )
            ),
            1
        )

        self.assertEqual(
            consultar_estancias_activas(
                placa_perdedora
            ),
            []
        )

        self.assertEqual(
            consultar_celda(celda)["estado"],
            "OCUPADA"
        )

        operador_esperado = (
            self.operador["id_operador"]
            if placa_ganadora == placa_a
            else self.operador2["id_operador"]
        )

        self.assertEqual(
            consultar_estancia(id_estancia)[
                "id_operador_entrada"
            ],
            operador_esperado
        )

        self.entorno.registrar_salida(
            placa_ganadora,
            usuario="admin"
        )

        self.verificar_integridad_final(
            antes,
            [id_estancia]
        )

        print(
            "\nCO-02:",
            "HTTP 201 y 409;",
            "una celda asignada;",
            "integridad conservada."
        )


    # =====================================================
    # CO-03 - RECHAZO ORDINARIO POR ESTANCIA ACTIVA
    # =====================================================

    def test_co03_estancia_previamente_activa(self):

        placa = self.crear_vehiculo_vigente()

        celda_a = seleccionar_celda(
            "MOTO"
        )

        celda_b = seleccionar_celda(
            "MOTO",
            excluir=(celda_a,)
        )

        original = capturar_estado()

        entrada = self.entorno.registrar_entrada(
            placa,
            celda_a
        )

        id_estancia = entrada[
            "estancia"
        ]["id_estancia"]

        antes_rechazo = capturar_estado()

        rechazo = self.entorno.registrar_entrada(
            placa,
            celda_b,
            usuario="operador2",
            esperado=400
        )

        self.assertIn(
            "estancia activa",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            capturar_estado(),
            antes_rechazo
        )

        self.assertEqual(
            consultar_celda(celda_a)["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            consultar_celda(celda_b)["estado"],
            "DISPONIBLE"
        )

        self.entorno.registrar_salida(
            placa
        )

        self.verificar_integridad_final(
            original,
            [id_estancia]
        )

        print(
            "\nCO-03:",
            "HTTP 400;",
            "rechazo ordinario correcto."
        )


    # =====================================================
    # CO-04 - RECHAZO ORDINARIO POR CELDA OCUPADA
    # =====================================================

    def test_co04_celda_previamente_ocupada(self):

        placa_a = self.crear_vehiculo_vigente()

        placa_b = self.crear_vehiculo_vigente()

        celda = seleccionar_celda(
            "MOTO"
        )

        original = capturar_estado()

        entrada = self.entorno.registrar_entrada(
            placa_a,
            celda
        )

        id_estancia = entrada[
            "estancia"
        ]["id_estancia"]

        antes_rechazo = capturar_estado()

        rechazo = self.entorno.registrar_entrada(
            placa_b,
            celda,
            usuario="operador2",
            esperado=400
        )

        self.assertIn(
            "ocupada",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            capturar_estado(),
            antes_rechazo
        )

        self.assertEqual(
            consultar_estancias_activas(
                placa_b
            ),
            []
        )

        self.entorno.registrar_salida(
            placa_a
        )

        self.verificar_integridad_final(
            original,
            [id_estancia]
        )

        print(
            "\nCO-04:",
            "HTTP 400;",
            "celda previamente ocupada."
        )


    # =====================================================
    # CO-05 - CAMBIO DE ESTADO DESPUES DE VALIDAR
    # =====================================================

    def test_co05_celda_deshabilitada_concurrentemente(self):

        placa = self.crear_vehiculo_vigente()

        celda = seleccionar_celda(
            "MOTO"
        )

        antes = capturar_estado()

        registrar_original = (
            entrada_service.registrar_entrada
        )

        def restaurar_celda():
            """
            Restaura únicamente la celda seleccionada
            si esta quedó fuera de servicio.
            """

            estado = consultar_celda(
                celda
            )["estado"]

            if estado == "FUERA_DE_SERVICIO":

                respuesta = self.entorno.solicitud(
                    "PATCH",
                    f"/api/celdas/{celda}/habilitar",
                    usuario="admin"
                )

                verificar_respuesta(
                    respuesta,
                    200
                )

        # Garantizar restauración aun si falla
        # alguna comprobación posterior.

        self.addCleanup(
            restaurar_celda
        )

        def deshabilitar_antes_de_registrar(
            *args,
            **kwargs
        ):
            """
            Ejecuta una modificación real de la celda
            después de superar la validación previa,
            pero antes de iniciar la transacción.
            """

            respuesta = self.entorno.solicitud(
                "PATCH",
                f"/api/celdas/{celda}/deshabilitar",
                usuario="admin"
            )

            verificar_respuesta(
                respuesta,
                200
            )

            return registrar_original(
                *args,
                **kwargs
            )

        with patch.object(
            entrada_service,
            "registrar_entrada",
            side_effect=deshabilitar_antes_de_registrar
        ):

            rechazo = self.entorno.registrar_entrada(
                placa,
                celda,
                esperado=409
            )

        self.assertIn(
            "fuera de servicio",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            consultar_estancias_activas(placa),
            []
        )

        self.assertEqual(
            consultar_celda(celda)["estado"],
            "FUERA_DE_SERVICIO"
        )

        # Ahora la celda ya está fuera de servicio
        # antes de realizar una nueva solicitud.
        # El rechazo debe ser ordinario: HTTP 400.

        estado_deshabilitado = capturar_estado()

        rechazo_ordinario = self.entorno.registrar_entrada(
            placa,
            celda,
            esperado=400
        )

        self.assertIn(
            "fuera de servicio",
            rechazo_ordinario["mensaje"].lower()
        )

        self.assertEqual(
            capturar_estado(),
            estado_deshabilitado
        )

        restaurar_celda()

        self.verificar_integridad_final(
            antes,
            []
        )

        print(
            "\nCO-05:",
            "HTTP 409 al cambiar la condición;",
            "HTTP 400 cuando ya estaba deshabilitada."
        )


    # =====================================================
    # CO-06 - COMPROBACION FINAL DE VIGENCIA
    # =====================================================

    def test_co06_vencimiento_antes_de_persistir(self):
        """
        Simula un cambio de vigencia entre las dos
        comprobaciones realizadas por el repositorio.

        Las consultas y la transacción continúan
        ejecutándose realmente contra PostgreSQL.
        """

        placa = self.crear_vehiculo_vigente()

        celda = seleccionar_celda(
            "MOTO"
        )

        vehiculo_original = consultar_vehiculo(
            placa
        )

        pagos_originales = consultar_pagos(
            placa
        )

        antes = capturar_estado()

        self.assertTrue(
            self.entorno.validar_ingreso(placa)[
                "puede_ingresar"
            ]
        )

        with patch.object(
            estancia_repository,
            "calcular_estado_mensualidad",
            side_effect=[
                "ACTIVA",
                "INACTIVA"
            ]
        ) as simulacion:

            rechazo = self.entorno.registrar_entrada(
                placa,
                celda,
                esperado=400
            )

        self.assertEqual(
            simulacion.call_count,
            2
        )

        # Ambas comprobaciones deben utilizar la fecha
        # de corte real obtenida de PostgreSQL.

        for llamada in simulacion.call_args_list:

            self.assertEqual(
                llamada.args[0],
                vehiculo_original["fecha_corte"]
            )

        self.assertIn(
            "vencida",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            consultar_vehiculo(placa),
            vehiculo_original
        )

        self.assertEqual(
            consultar_pagos(placa),
            pagos_originales
        )

        self.assertEqual(
            consultar_estancias_activas(placa),
            []
        )

        self.assertEqual(
            consultar_celda(celda)["estado"],
            "DISPONIBLE"
        )

        self.verificar_integridad_final(
            antes,
            []
        )

        print(
            "\nCO-06:",
            "HTTP 400;",
            "vigencia revalidada;",
            "ninguna escritura persistida."
        )