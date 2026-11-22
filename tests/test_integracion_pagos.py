"""
Autos Colombia - Iteración 3.

Pruebas automatizadas de integración del módulo
de pagos y mensualidades.

Plan académico: PP-03.

Las pruebas utilizan la API real de Flask y una
base PostgreSQL aislada.

No requieren vehículos de prueba preexistentes.
No modifican la base de datos principal.
"""

from datetime import date, timedelta
from decimal import Decimal

from tests.e2e_helpers import (
    BasePruebaE2E,
    capturar_estado,
    consultar_vehiculo,
    consultar_pagos,
    generar_placa_prueba,
    verificar_respuesta,
    simular_fecha
)

from app.services.mensualidad_service import (
    fecha_actual_colombia
)


# =========================================================
# PRUEBAS DE INTEGRACION DE PAGOS
# =========================================================

class TestIntegracionPagos(BasePruebaE2E):

    def setUp(self):

        super().setUp()

        self.hoy = fecha_actual_colombia()


    # =====================================================
    # FUNCIONES AUXILIARES
    # =====================================================

    def crear_vehiculo(
        self,
        tipo="AUTOMOVIL"
    ):

        resultado = (
            self.entorno.crear_vehiculo_prueba(
                tipo_vehiculo=tipo
            )
        )

        return resultado["placa"]


    def pagar(
        self,
        placa,
        fecha=None,
        usuario="operador1"
    ):

        if fecha is None:

            fecha = self.hoy

        consulta = self.entorno.mensualidad(
            placa,
            usuario=usuario,
            fecha_pago=fecha
        )

        proyeccion = consulta["proximo_pago"]

        return self.entorno.registrar_pago(
            placa=placa,
            fecha_pago=fecha,
            corte_esperado=proyeccion["corte_esperado"],
            usuario=usuario
        )


    def verificar_cobertura(
        self,
        placa,
        fecha_inicio,
        fecha_corte,
        cantidad_pagos
    ):

        vehiculo = consultar_vehiculo(placa)

        pagos = consultar_pagos(placa)

        self.assertIsNotNone(vehiculo)

        self.assertEqual(
            vehiculo["fecha_inicio_mensualidad"],
            fecha_inicio
        )

        self.assertEqual(
            vehiculo["fecha_corte"],
            fecha_corte
        )

        self.assertEqual(
            len(pagos),
            cantidad_pagos
        )

        consulta = self.entorno.mensualidad(
            placa
        )

        self.assertEqual(
            consulta["num_pagos"],
            cantidad_pagos
        )

        self.assertEqual(
            consulta["fecha_corte"],
            fecha_corte.isoformat()
            if fecha_corte is not None
            else None
        )

        estado_esperado = (
            "ACTIVA"
            if fecha_corte is not None
            and fecha_actual_colombia() < fecha_corte
            else "INACTIVA"
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            estado_esperado
        )


    # =====================================================
    # PG-01 - CONSULTAR MENSUALIDAD VIGENTE
    # =====================================================

    def test_pg01_consultar_mensualidad_vigente(self):

        placa = self.crear_vehiculo()

        self.pagar(placa)

        antes = capturar_estado()

        consulta = self.entorno.mensualidad(
            placa
        )

        self.assertEqual(
            consulta["estado"],
            "ok"
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            consulta["tarifa"],
            250000
        )

        self.assertEqual(
            consulta["num_pagos"],
            1
        )

        self.assertEqual(
            consulta["dia_corte"],
            self.hoy.day
        )

        self.assertEqual(
            consulta["vehiculo"]["placa"],
            placa
        )

        self.assertIsNotNone(
            consulta["cliente"]["id_cliente"]
        )

        self.assertEqual(
            consulta["fecha_inicio"],
            self.hoy.isoformat()
        )

        self.assertEqual(
            consulta["proximo_pago"]["tipo"],
            "RENOVACION"
        )

        self.assertEqual(
            consulta["proximo_pago"]["corte_esperado"],
            consulta["fecha_corte"]
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-02 - VEHICULO INEXISTENTE Y SIN COBERTURA
    # =====================================================

    def test_pg02_inexistente_y_sin_pagos(self):

        placa = self.crear_vehiculo()

        inexistente = generar_placa_prueba()

        antes = capturar_estado()

        error = self.entorno.mensualidad(
            inexistente,
            esperado=404
        )

        self.assertEqual(
            error["estado"],
            "error"
        )

        consulta = self.entorno.mensualidad(
            placa
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            "INACTIVA"
        )

        self.assertEqual(
            consulta["num_pagos"],
            0
        )

        self.assertIsNone(
            consulta["fecha_inicio"]
        )

        self.assertIsNone(
            consulta["fecha_corte"]
        )

        self.assertIsNone(
            consulta["dia_corte"]
        )

        self.assertEqual(
            consulta["proximo_pago"]["tipo"],
            "PRIMER_PAGO"
        )

        self.assertIsNone(
            consulta["proximo_pago"]["corte_esperado"]
        )

        self.assertEqual(
            consultar_pagos(placa),
            []
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-03 - PRIMER PAGO DE AUTOMOVIL
    # =====================================================

    def test_pg03_primer_pago_automovil(self):

        placa = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        consulta = self.entorno.mensualidad(
            placa
        )

        proyeccion = consulta["proximo_pago"]

        resultado = self.pagar(placa)

        pago = resultado["pago"]

        mensualidad = resultado["mensualidad"]

        self.assertEqual(
            pago["tipo"],
            "PRIMER_PAGO"
        )

        self.assertEqual(
            pago["valor"],
            250000
        )

        self.assertEqual(
            pago["fecha_pago"],
            self.hoy.isoformat()
        )

        self.assertEqual(
            pago["periodo_inicio"],
            self.hoy.isoformat()
        )

        self.assertEqual(
            pago["periodo_fin"],
            proyeccion["periodo_fin"]
        )

        self.assertEqual(
            mensualidad["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            mensualidad["num_pagos"],
            1
        )

        self.assertEqual(
            pago["registrado_por"]["id_operador"],
            self.operador["id_operador"]
        )

        self.assertIsNone(
            resultado["advertencia"]
        )

        self.verificar_cobertura(
            placa,
            self.hoy,
            date.fromisoformat(pago["periodo_fin"]),
            1
        )

        persistido = consultar_pagos(placa)[0]

        self.assertEqual(
            persistido["valor"],
            Decimal("250000.00")
        )

        self.assertEqual(
            persistido["id_operador"],
            self.operador["id_operador"]
        )


    # =====================================================
    # PG-04 - PRIMER PAGO DE MOTOCICLETA
    # =====================================================

    def test_pg04_primer_pago_motocicleta(self):

        placa = self.crear_vehiculo(
            "MOTO"
        )

        resultado = self.pagar(
            placa,
            usuario="admin"
        )

        pago = resultado["pago"]

        self.assertEqual(
            pago["valor"],
            100000
        )

        self.assertEqual(
            pago["tipo"],
            "PRIMER_PAGO"
        )

        self.assertEqual(
            pago["registrado_por"]["id_operador"],
            self.admin["id_operador"]
        )

        self.assertEqual(
            resultado["mensualidad"]["estado_mensualidad"],
            "ACTIVA"
        )

        persistido = consultar_pagos(placa)[0]

        self.assertEqual(
            persistido["valor"],
            Decimal("100000.00")
        )

        self.assertEqual(
            persistido["id_operador"],
            self.admin["id_operador"]
        )

        self.verificar_cobertura(
            placa,
            self.hoy,
            date.fromisoformat(pago["periodo_fin"]),
            1
        )


    # =====================================================
    # PG-05 - DATOS DE PAGO INVALIDOS
    # =====================================================

    def test_pg05_datos_invalidos(self):

        placa = self.crear_vehiculo()

        inexistente = generar_placa_prueba()

        base = {
            "placa": placa,
            "fecha_pago": self.hoy.isoformat(),
            "corte_esperado": None
        }

        casos = (
            ("Sin placa", {
                "fecha_pago": self.hoy.isoformat(),
                "corte_esperado": None
            }),

            ("Sin fecha de pago", {
                "placa": placa,
                "corte_esperado": None
            }),

            ("Sin corte esperado", {
                "placa": placa,
                "fecha_pago": self.hoy.isoformat()
            }),

            ("Placa invalida", {
                **base,
                "placa": "ABC@123"
            }),

            ("Fecha futura", {
                **base,
                "fecha_pago": (
                    self.hoy + timedelta(days=1)
                ).isoformat()
            }),

            ("Fecha inexistente", {
                **base,
                "fecha_pago": "2026-02-30"
            }),

            ("Fecha con formato incorrecto", {
                **base,
                "fecha_pago": "21/11/2026"
            }),

            ("Fecha nula", {
                **base,
                "fecha_pago": None
            }),

            ("Corte invalido", {
                **base,
                "corte_esperado": "fecha-invalida"
            }),

            ("JSON vacio", {}),

            ("JSON no es objeto", ["pago"])
        )

        antes = capturar_estado()

        for nombre, datos in casos:

            with self.subTest(caso=nombre):

                respuesta = self.entorno.solicitud(
                    "POST",
                    "/api/pagos",
                    usuario="operador1",
                    datos=datos
                )

                verificar_respuesta(
                    respuesta,
                    422
                )

                self.assertEqual(
                    capturar_estado(),
                    antes
                )

        resultado = self.entorno.registrar_pago(
            inexistente,
            self.hoy,
            None,
            esperado=404
        )

        self.assertEqual(
            resultado["estado"],
            "error"
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        self.assertEqual(
            consultar_pagos(placa),
            []
        )


    # =====================================================
    # PG-06 - RENOVACION ANTICIPADA
    # =====================================================

    def test_pg06_renovacion_anticipada(self):

        placa = self.crear_vehiculo()

        self.pagar(placa)

        vehiculo_antes = consultar_vehiculo(
            placa
        )

        corte_anterior = vehiculo_antes["fecha_corte"]

        self.assertGreater(
            corte_anterior,
            self.hoy
        )

        consulta = self.entorno.mensualidad(
            placa
        )

        proyeccion = consulta["proximo_pago"]

        resultado = self.pagar(
            placa,
            usuario="admin"
        )

        pago = resultado["pago"]

        self.assertEqual(
            pago["tipo"],
            "RENOVACION"
        )

        self.assertEqual(
            pago["periodo_inicio"],
            corte_anterior.isoformat()
        )

        self.assertEqual(
            pago["periodo_fin"],
            proyeccion["periodo_fin"]
        )

        nuevo_corte = date.fromisoformat(
            pago["periodo_fin"]
        )

        self.assertGreater(
            nuevo_corte,
            corte_anterior
        )

        self.assertEqual(
            resultado["mensualidad"]["estado_mensualidad"],
            "ACTIVA"
        )

        self.verificar_cobertura(
            placa,
            vehiculo_antes["fecha_inicio_mensualidad"],
            nuevo_corte,
            2
        )

        self.assertEqual(
            resultado["mensualidad"]["dia_corte"],
            self.hoy.day
        )


    # =====================================================
    # PG-07 - RENOVACION TARDIA
    # =====================================================

    def test_pg07_renovacion_tardia(self):

        placa = self.crear_vehiculo()

        fecha_inicial = (
            self.hoy - timedelta(days=100)
        )

        primer_pago = self.pagar(
            placa,
            fecha=fecha_inicial
        )

        self.assertEqual(
            primer_pago["mensualidad"]["estado_mensualidad"],
            "INACTIVA"
        )

        self.assertIsNotNone(
            primer_pago["advertencia"]
        )

        anterior = consultar_vehiculo(
            placa
        )

        corte_anterior = anterior["fecha_corte"]

        self.assertLess(
            corte_anterior,
            self.hoy
        )

        resultado = self.pagar(
            placa,
            fecha=self.hoy
        )

        pago = resultado["pago"]

        self.assertEqual(
            pago["periodo_inicio"],
            corte_anterior.isoformat()
        )

        self.assertEqual(
            resultado["mensualidad"]["estado_mensualidad"],
            "INACTIVA"
        )

        self.assertIsNotNone(
            resultado["advertencia"]
        )

        self.assertIn(
            "inactiva",
            resultado["advertencia"].lower()
        )

        # Cada pago agrega un mes.
        # No se cobra automáticamente toda la deuda.

        cantidad = 2

        while (
            resultado["mensualidad"]["estado_mensualidad"]
            == "INACTIVA"
        ):

            self.assertLess(
                cantidad,
                6
            )

            corte_previo = consultar_vehiculo(
                placa
            )["fecha_corte"]

            resultado = self.pagar(
                placa,
                fecha=self.hoy
            )

            self.assertEqual(
                resultado["pago"]["periodo_inicio"],
                corte_previo.isoformat()
            )

            cantidad += 1

        self.assertEqual(
            resultado["mensualidad"]["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertIsNone(
            resultado["advertencia"]
        )

        self.verificar_cobertura(
            placa,
            fecha_inicial,
            date.fromisoformat(
                resultado["mensualidad"]["fecha_corte"]
            ),
            cantidad
        )


    # =====================================================
    # PG-08 - FECHAS ESPECIALES DEL CALENDARIO
    # =====================================================

    def test_pg08_fechas_especiales(self):

        # Se utilizan fechas históricas fijas para
        # verificar resultados conocidos e independientes
        # del algoritmo implementado en el backend.

        escenarios = (

            (
                date(2025, 1, 31),
                (
                    "2025-02-28",
                    "2025-03-31",
                    "2025-04-30",
                    "2025-05-31"
                )
            ),

            (
                date(2025, 1, 30),
                (
                    "2025-02-28",
                    "2025-03-30",
                    "2025-04-30"
                )
            ),

            (
                date(2024, 1, 31),
                (
                    "2024-02-29",
                    "2024-03-31"
                )
            ),

            (
                date(2024, 2, 29),
                tuple(
                    f"2024-{mes:02d}-29"
                    for mes in range(3, 13)
                ) + (
                    "2025-01-29",
                    "2025-02-28",
                    "2025-03-29"
                )
            ),

            (
                date(2025, 12, 31),
                (
                    "2026-01-31",
                    "2026-02-28",
                    "2026-03-31"
                )
            )
        )

        for inicio, cortes in escenarios:

            with self.subTest(
                fecha_inicio=inicio.isoformat()
            ):

                placa = self.crear_vehiculo()

                for numero, corte in enumerate(
                    cortes,
                    start=1
                ):

                    resultado = self.pagar(
                        placa,
                        fecha=inicio
                    )

                    self.assertEqual(
                        resultado["pago"]["periodo_fin"],
                        corte
                    )

                    self.assertEqual(
                        resultado["mensualidad"]["dia_corte"],
                        inicio.day
                    )

                    self.verificar_cobertura(
                        placa,
                        inicio,
                        date.fromisoformat(corte),
                        numero
                    )


    # =====================================================
    # PG-10 - HISTORIAL DE PAGOS
    # =====================================================

    def test_pg10_historial(self):

        placa = self.crear_vehiculo(
            "MOTO"
        )

        primero = self.pagar(
            placa,
            fecha=self.hoy - timedelta(days=2)
        )

        segundo = self.pagar(
            placa,
            fecha=self.hoy - timedelta(days=1),
            usuario="admin"
        )

        antes = capturar_estado()

        historial = self.entorno.historial(
            placa
        )

        self.assertEqual(
            historial["placa"],
            placa
        )

        self.assertEqual(
            historial["cantidad"],
            2
        )

        pagos = historial["pagos"]

        self.assertEqual(
            len(pagos),
            2
        )

        self.assertEqual(
            pagos[0]["id_pago"],
            segundo["pago"]["id_pago"]
        )

        self.assertEqual(
            pagos[1]["id_pago"],
            primero["pago"]["id_pago"]
        )

        self.assertEqual(
            pagos[0]["registrado_por"]["id_operador"],
            self.admin["id_operador"]
        )

        self.assertEqual(
            pagos[1]["registrado_por"]["id_operador"],
            self.operador["id_operador"]
        )

        for pago in pagos:

            self.assertEqual(
                pago["valor"],
                100000
            )

            self.assertIsNotNone(
                pago["fecha_registro"]
            )

            self.assertIsNotNone(
                pago["periodo_inicio"]
            )

            self.assertIsNotNone(
                pago["periodo_fin"]
            )

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-11 - HISTORIAL VACIO E INEXISTENTE
    # =====================================================

    def test_pg11_historial_vacio(self):

        placa = self.crear_vehiculo()

        inexistente = generar_placa_prueba()

        antes = capturar_estado()

        historial = self.entorno.historial(
            placa
        )

        self.assertEqual(
            historial["cantidad"],
            0
        )

        self.assertEqual(
            historial["pagos"],
            []
        )

        resultado = self.entorno.historial(
            inexistente,
            esperado=404
        )

        self.assertEqual(
            resultado["estado"],
            "error"
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-16 - LIMITE DE FECHA DE CORTE
    # =====================================================

    def test_pg16_limite_fecha_corte(self):

        placa = self.crear_vehiculo()

        self.pagar(placa)

        vehiculo = consultar_vehiculo(
            placa
        )

        corte = vehiculo["fecha_corte"]

        antes = capturar_estado()

        escenarios = (
            (
                corte - timedelta(days=1),
                "ACTIVA",
                True
            ),

            (
                corte,
                "INACTIVA",
                False
            ),

            (
                corte + timedelta(days=1),
                "INACTIVA",
                False
            )
        )

        for fecha, estado, permitido in escenarios:

            with self.subTest(fecha=fecha):

                with simular_fecha(fecha):

                    mensualidad = (
                        self.entorno.mensualidad(
                            placa
                        )
                    )

                    validacion = (
                        self.entorno.validar_ingreso(
                            placa
                        )
                    )

                    self.assertEqual(
                        mensualidad["estado_mensualidad"],
                        estado
                    )

                    self.assertIs(
                        validacion["puede_ingresar"],
                        permitido
                    )

                    self.assertEqual(
                        mensualidad["fecha_corte"],
                        corte.isoformat()
                    )

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-17 - AUTENTICACION Y ROLES
    # =====================================================

    def test_pg17_autenticacion_roles(self):

        placa = self.crear_vehiculo()

        solicitudes = (

            (
                "GET",
                f"/api/mensualidades/{placa}",
                None
            ),

            (
                "GET",
                f"/api/vehiculos/{placa}/pagos",
                None
            ),

            (
                "POST",
                "/api/pagos",
                {
                    "placa": placa,
                    "fecha_pago": self.hoy.isoformat(),
                    "corte_esperado": None
                }
            )
        )

        antes = capturar_estado()

        for metodo, ruta, datos in solicitudes:

            for headers in (
                {},
                {
                    "Authorization":
                        "Bearer token-invalido-e2e"
                }
            ):

                with self.subTest(
                    metodo=metodo,
                    ruta=ruta
                ):

                    respuesta = self.entorno.solicitud(
                        metodo,
                        ruta,
                        datos=datos,
                        headers=headers
                    )

                    verificar_respuesta(
                        respuesta,
                        401
                    )

                    self.assertEqual(
                        capturar_estado(),
                        antes
                    )

        # Ambos perfiles autorizados pueden registrar
        # pagos, conservando su identidad real.

        primero = self.pagar(
            placa,
            usuario="operador1"
        )

        segundo = self.pagar(
            placa,
            usuario="admin"
        )

        self.assertEqual(
            primero["pago"]["registrado_por"]["id_operador"],
            self.operador["id_operador"]
        )

        self.assertEqual(
            segundo["pago"]["registrado_por"]["id_operador"],
            self.admin["id_operador"]
        )

        for usuario in (
            "operador1",
            "admin"
        ):

            self.assertEqual(
                self.entorno.mensualidad(
                    placa,
                    usuario=usuario
                )["num_pagos"],
                2
            )

            self.assertEqual(
                self.entorno.historial(
                    placa,
                    usuario=usuario
                )["cantidad"],
                2
            )


    # =====================================================
    # PG-18 - VALOR DETERMINADO POR EL SERVIDOR
    # =====================================================

    def test_pg18_valor_servidor(self):

        tarifas = (
            ("AUTOMOVIL", 250000),
            ("CAMIONETA", 250000),
            ("MOTO", 100000)
        )

        for tipo, tarifa in tarifas:

            with self.subTest(tipo=tipo):

                placa = self.crear_vehiculo(
                    tipo
                )

                base = {
                    "placa": placa,
                    "fecha_pago": self.hoy.isoformat(),
                    "corte_esperado": None
                }

                antes = capturar_estado()

                campos_prohibidos = (
                    {"valor": 1},
                    {"valor": 0},
                    {"valor": -100},
                    {"tarifa": 1},
                    {"id_operador": 999},
                    {"id_cliente": 999},
                    {"periodo_inicio": "2020-01-01"},
                    {"periodo_fin": "2099-12-31"}
                )

                for campo in campos_prohibidos:

                    respuesta = self.entorno.solicitud(
                        "POST",
                        "/api/pagos",
                        usuario="operador1",
                        datos={
                            **base,
                            **campo
                        }
                    )

                    verificar_respuesta(
                        respuesta,
                        422
                    )

                    self.assertEqual(
                        capturar_estado(),
                        antes
                    )

                resultado = self.pagar(
                    placa
                )

                self.assertEqual(
                    resultado["pago"]["valor"],
                    tarifa
                )

                persistido = consultar_pagos(
                    placa
                )[0]

                self.assertEqual(
                    persistido["valor"],
                    Decimal(tarifa)
                )

                self.assertEqual(
                    persistido["id_operador"],
                    self.operador["id_operador"]
                )