"""
Autos Colombia - Iteración 3.

Pruebas automatizadas de integración entre el
módulo de pagos y las operaciones del parqueadero
implementadas durante EA1 y EA2.

Plan académico: PP-03.

Casos cubiertos:
- PG-12: Entrada con mensualidad vigente.
- PG-13: Entrada con mensualidad vencida.
- PG-14: Entrada después del primer pago.
- PG-15: Salida con mensualidad vencida.
- PG-20: Protección de la mensualidad.

Las pruebas utilizan Flask Test Client y una
base PostgreSQL aislada.
"""

from datetime import timedelta

from tests.e2e_helpers import (
    BasePruebaE2E,
    capturar_estado,
    consultar_vehiculo,
    consultar_pagos,
    consultar_celda,
    consultar_estancia,
    consultar_estancias_activas,
    seleccionar_celda,
    verificar_respuesta,
    simular_fecha
)

from app.services.mensualidad_service import (
    fecha_actual_colombia
)


# =========================================================
# INTEGRACION DE OPERACIONES EA1, EA2 Y EA3
# =========================================================

class TestIntegracionOperaciones(BasePruebaE2E):

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

        return self.entorno.crear_vehiculo_prueba(
            tipo_vehiculo=tipo
        )


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


    def consultar_vehiculo_api(
        self,
        placa,
        usuario="operador1"
    ):

        respuesta = self.entorno.solicitud(
            "GET",
            f"/api/vehiculos/{placa}",
            usuario=usuario
        )

        cuerpo = verificar_respuesta(
            respuesta,
            200
        )

        return cuerpo["vehiculo"]


    def modificar_vehiculo(
        self,
        placa,
        datos,
        usuario="admin",
        esperado=200
    ):

        respuesta = self.entorno.solicitud(
            "PUT",
            f"/api/vehiculos/{placa}",
            usuario=usuario,
            datos=datos
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    def verificar_salida(
        self,
        placa,
        codigo_celda,
        id_estancia,
        usuario="operador1"
    ):

        resultado = self.entorno.registrar_salida(
            placa,
            usuario=usuario
        )

        estancia = resultado["estancia"]

        self.assertEqual(
            estancia["id_estancia"],
            id_estancia
        )

        self.assertEqual(
            estancia["estado"],
            "FINALIZADA"
        )

        self.assertIsNotNone(
            estancia["fecha_hora_salida"]
        )

        self.assertEqual(
            estancia["celda"]["codigo"],
            codigo_celda
        )

        self.assertEqual(
            estancia["celda"]["estado"],
            "DISPONIBLE"
        )

        persistida = consultar_estancia(
            id_estancia
        )

        self.assertEqual(
            persistida["estado"],
            "FINALIZADA"
        )

        self.assertIsNotNone(
            persistida["fecha_hora_salida"]
        )

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "DISPONIBLE"
        )

        self.assertEqual(
            consultar_estancias_activas(placa),
            []
        )

        return resultado


    # =====================================================
    # PG-12 - ENTRADA CON MENSUALIDAD VIGENTE
    # =====================================================

    def test_pg12_entrada_mensualidad_vigente(self):

        registro = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        placa = registro["placa"]

        self.pagar(placa)

        mensualidad = self.entorno.mensualidad(
            placa
        )

        self.assertEqual(
            mensualidad["estado_mensualidad"],
            "ACTIVA"
        )

        codigo_celda = seleccionar_celda(
            "AUTOMOVIL"
        )

        celda_anterior = consultar_celda(
            codigo_celda
        )

        vehiculo_anterior = consultar_vehiculo(
            placa
        )

        pagos_anteriores = consultar_pagos(
            placa
        )

        self.assertEqual(
            celda_anterior["estado"],
            "DISPONIBLE"
        )

        validacion = self.entorno.validar_ingreso(
            placa
        )

        self.assertIs(
            validacion["puede_ingresar"],
            True
        )

        self.assertEqual(
            validacion["codigo_motivo"],
            "INGRESO_PERMITIDO"
        )

        resultado = self.entorno.registrar_entrada(
            placa,
            codigo_celda
        )

        estancia = resultado["estancia"]

        id_estancia = estancia["id_estancia"]

        self.assertEqual(
            resultado["vehiculo"]["placa"],
            placa
        )

        self.assertEqual(
            estancia["estado"],
            "ACTIVA"
        )

        self.assertEqual(
            estancia["celda"]["codigo"],
            codigo_celda
        )

        self.assertEqual(
            estancia["celda"]["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            estancia["operador"]["id_operador"],
            self.operador["id_operador"]
        )

        persistida = consultar_estancia(
            id_estancia
        )

        self.assertEqual(
            persistida["id_vehiculo"],
            registro["id_vehiculo"]
        )

        self.assertEqual(
            persistida["id_celda"],
            celda_anterior["id_celda"]
        )

        self.assertEqual(
            persistida["id_operador_entrada"],
            self.operador["id_operador"]
        )

        self.assertEqual(
            persistida["estado"],
            "ACTIVA"
        )

        self.assertIsNone(
            persistida["fecha_hora_salida"]
        )

        self.assertIsNone(
            persistida["id_operador_salida"]
        )

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            len(consultar_estancias_activas(placa)),
            1
        )

        # Comprobar la consulta de vehículos dentro.

        respuesta = self.entorno.solicitud(
            "GET",
            "/api/estancias/activas",
            usuario="operador1"
        )

        activos = verificar_respuesta(
            respuesta,
            200
        )

        self.assertTrue(
            any(
                fila["id_estancia"] == id_estancia
                for fila in activos["vehiculos"]
            )
        )

        # La entrada no modifica cobertura ni pagos.

        self.assertEqual(
            consultar_vehiculo(placa),
            vehiculo_anterior
        )

        self.assertEqual(
            consultar_pagos(placa),
            pagos_anteriores
        )

        # Finalizar la estancia y liberar la celda.

        self.verificar_salida(
            placa,
            codigo_celda,
            id_estancia
        )

        self.assertEqual(
            consultar_celda(codigo_celda),
            celda_anterior
        )


    # =====================================================
    # PG-13 - ENTRADA CON MENSUALIDAD VENCIDA
    # =====================================================

    def test_pg13_entrada_mensualidad_vencida(self):

        registro = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        placa = registro["placa"]

        fecha_historica = (
            self.hoy - timedelta(days=90)
        )

        resultado_pago = self.pagar(
            placa,
            fecha=fecha_historica
        )

        self.assertEqual(
            resultado_pago["mensualidad"]["estado_mensualidad"],
            "INACTIVA"
        )

        self.assertIsNotNone(
            resultado_pago["advertencia"]
        )

        codigo_celda = seleccionar_celda(
            "AUTOMOVIL"
        )

        antes = capturar_estado()

        validacion = self.entorno.validar_ingreso(
            placa
        )

        self.assertIs(
            validacion["puede_ingresar"],
            False
        )

        self.assertEqual(
            validacion["codigo_motivo"],
            "MENSUALIDAD_VENCIDA"
        )

        self.assertTrue(
            validacion["validaciones"]["vehiculo_registrado"]
        )

        self.assertFalse(
            validacion["validaciones"]["mensualidad_activa"]
        )

        rechazo = self.entorno.registrar_entrada(
            placa,
            codigo_celda,
            esperado=400
        )

        self.assertEqual(
            rechazo["estado"],
            "error"
        )

        self.assertIn(
            "vencida",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            consultar_estancias_activas(placa),
            []
        )

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "DISPONIBLE"
        )

        # Ninguna tabla debe modificarse.

        self.assertEqual(
            capturar_estado(),
            antes
        )


    # =====================================================
    # PG-14 - PRIMER PAGO HABILITA EL INGRESO
    # =====================================================

    def test_pg14_ingreso_despues_primer_pago(self):

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        codigo_celda = seleccionar_celda(
            "MOTO"
        )

        vehiculo = consultar_vehiculo(
            placa
        )

        self.assertIsNone(
            vehiculo["fecha_inicio_mensualidad"]
        )

        self.assertIsNone(
            vehiculo["fecha_corte"]
        )

        self.assertEqual(
            consultar_pagos(placa),
            []
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

        antes = capturar_estado()

        # -------------------------------------------------
        # 1. Rechazar entrada sin primer pago.
        # -------------------------------------------------

        validacion = self.entorno.validar_ingreso(
            placa
        )

        self.assertIs(
            validacion["puede_ingresar"],
            False
        )

        self.assertEqual(
            validacion["codigo_motivo"],
            "SIN_PRIMER_PAGO"
        )

        rechazo = self.entorno.registrar_entrada(
            placa,
            codigo_celda,
            esperado=400
        )

        self.assertIn(
            "primer pago",
            rechazo["mensaje"].lower()
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # 2. Registrar primer pago.
        # -------------------------------------------------

        resultado_pago = self.pagar(
            placa
        )

        self.assertEqual(
            resultado_pago["pago"]["tipo"],
            "PRIMER_PAGO"
        )

        self.assertEqual(
            resultado_pago["pago"]["valor"],
            100000
        )

        self.assertEqual(
            resultado_pago["mensualidad"]["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            1
        )

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "DISPONIBLE"
        )

        # -------------------------------------------------
        # 3. Comprobar habilitación del ingreso.
        # -------------------------------------------------

        consulta = self.consultar_vehiculo_api(
            placa
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            "ACTIVA"
        )

        validacion = self.entorno.validar_ingreso(
            placa
        )

        self.assertIs(
            validacion["puede_ingresar"],
            True
        )

        self.assertEqual(
            validacion["codigo_motivo"],
            "INGRESO_PERMITIDO"
        )

        # -------------------------------------------------
        # 4. Registrar entrada.
        # -------------------------------------------------

        resultado = self.entorno.registrar_entrada(
            placa,
            codigo_celda
        )

        id_estancia = resultado[
            "estancia"
        ]["id_estancia"]

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            len(consultar_estancias_activas(placa)),
            1
        )

        # -------------------------------------------------
        # 5. Registrar salida.
        # -------------------------------------------------

        self.verificar_salida(
            placa,
            codigo_celda,
            id_estancia
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            1
        )

        self.assertEqual(
            self.entorno.mensualidad(placa)[
                "estado_mensualidad"
            ],
            "ACTIVA"
        )


    # =====================================================
    # PG-15 - SALIDA CON MENSUALIDAD VENCIDA
    # =====================================================

    def test_pg15_salida_mensualidad_vencida(self):

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        self.pagar(placa)

        codigo_celda = seleccionar_celda(
            "MOTO"
        )

        entrada = self.entorno.registrar_entrada(
            placa,
            codigo_celda
        )

        id_estancia = entrada[
            "estancia"
        ]["id_estancia"]

        vehiculo_anterior = consultar_vehiculo(
            placa
        )

        pagos_anteriores = consultar_pagos(
            placa
        )

        fecha_corte = vehiculo_anterior[
            "fecha_corte"
        ]

        self.assertGreater(
            fecha_corte,
            self.hoy
        )

        self.assertEqual(
            consultar_celda(codigo_celda)["estado"],
            "OCUPADA"
        )

        # Simular que la mensualidad vence mientras
        # el vehículo permanece dentro del parqueadero.

        with simular_fecha(
            fecha_corte + timedelta(days=1)
        ):

            mensualidad = self.entorno.mensualidad(
                placa
            )

            self.assertEqual(
                mensualidad["estado_mensualidad"],
                "INACTIVA"
            )

            validacion = self.entorno.validar_ingreso(
                placa
            )

            self.assertIs(
                validacion["puede_ingresar"],
                False
            )

            self.assertEqual(
                validacion["codigo_motivo"],
                "MENSUALIDAD_VENCIDA"
            )

            self.assertEqual(
                consultar_estancia(id_estancia)["estado"],
                "ACTIVA"
            )

            # La salida debe permitirse incluso cuando
            # la mensualidad se encuentra vencida.

            salida = self.verificar_salida(
                placa,
                codigo_celda,
                id_estancia,
                usuario="admin"
            )

            self.assertEqual(
                salida["estancia"]["operador_salida"][
                    "id_operador"
                ],
                self.admin["id_operador"]
            )

            self.assertEqual(
                consultar_estancia(id_estancia)[
                    "id_operador_entrada"
                ],
                self.operador["id_operador"]
            )

            self.assertEqual(
                consultar_estancia(id_estancia)[
                    "id_operador_salida"
                ],
                self.admin["id_operador"]
            )

            self.assertEqual(
                self.entorno.mensualidad(placa)[
                    "estado_mensualidad"
                ],
                "INACTIVA"
            )

            # El vehículo no puede volver a ingresar
            # mientras la mensualidad esté vencida.

            antes_reingreso = capturar_estado()

            self.entorno.registrar_entrada(
                placa,
                codigo_celda,
                esperado=400
            )

            self.assertEqual(
                capturar_estado(),
                antes_reingreso
            )

        # La simulación no modifica las fechas
        # persistidas ni los pagos registrados.

        self.assertEqual(
            consultar_vehiculo(placa),
            vehiculo_anterior
        )

        self.assertEqual(
            consultar_pagos(placa),
            pagos_anteriores
        )

        self.assertEqual(
            consultar_estancias_activas(placa),
            []
        )


    # =====================================================
    # PG-20 - PROTECCION DE LA MENSUALIDAD
    # =====================================================

    def test_pg20_proteccion_mensualidad(self):

        registro_inactivo = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        registro_activo = self.crear_vehiculo(
            "MOTO"
        )

        placa_inactiva = registro_inactivo["placa"]

        placa_activa = registro_activo["placa"]

        self.pagar(placa_activa)

        antes = capturar_estado()

        # -------------------------------------------------
        # 1. Impedir activación manual.
        # -------------------------------------------------

        self.modificar_vehiculo(
            placa_inactiva,
            {
                "estado_mensualidad": "ACTIVA"
            },
            esperado=422
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # 2. Impedir desactivación manual.
        # -------------------------------------------------

        self.modificar_vehiculo(
            placa_activa,
            {
                "estado_mensualidad": "INACTIVA"
            },
            esperado=422
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # 3. Impedir modificación de cobertura.
        # -------------------------------------------------

        campos_protegidos = (

            {
                "fecha_inicio_mensualidad":
                    "2020-01-01"
            },

            {
                "fecha_inicio":
                    "2020-01-01"
            },

            {
                "fecha_corte":
                    "2099-12-31"
            },

            {
                "dia_corte": 31
            },

            {
                "num_pagos": 999
            },

            {
                "mensualidad": "ACTIVA"
            },

            {
                "corte_esperado":
                    "2099-12-31"
            },

            {
                "tarifa": 1
            },

            {
                "fecha_corte": None
            },

            {
                "marca": "Marca no autorizada",
                "estado_mensualidad": "INACTIVA"
            }
        )

        for datos in campos_protegidos:

            with self.subTest(
                campos=tuple(datos)
            ):

                self.modificar_vehiculo(
                    placa_activa,
                    datos,
                    esperado=422
                )

                self.assertEqual(
                    capturar_estado(),
                    antes
                )

        # -------------------------------------------------
        # 4. Conservar permisos de EA2.
        # -------------------------------------------------

        self.modificar_vehiculo(
            placa_activa,
            {
                "color": "Blanco"
            },
            usuario="operador1",
            esperado=403
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # 5. Permitir edición administrativa válida.
        # -------------------------------------------------

        vehiculo_anterior = consultar_vehiculo(
            placa_activa
        )

        pagos_anteriores = consultar_pagos(
            placa_activa
        )

        resultado = self.modificar_vehiculo(
            placa_activa,
            {
                "marca": "Marca E2E Actualizada",
                "color": "Blanco"
            }
        )

        vehiculo_api = resultado["vehiculo"]

        self.assertEqual(
            vehiculo_api["marca"],
            "Marca E2E Actualizada"
        )

        self.assertEqual(
            vehiculo_api["color"],
            "Blanco"
        )

        self.assertEqual(
            vehiculo_api["estado_mensualidad"],
            "ACTIVA"
        )

        vehiculo_esperado = {
            **vehiculo_anterior,
            "marca": "Marca E2E Actualizada",
            "color": "Blanco"
        }

        self.assertEqual(
            consultar_vehiculo(placa_activa),
            vehiculo_esperado
        )

        self.assertEqual(
            consultar_pagos(placa_activa),
            pagos_anteriores
        )

        # -------------------------------------------------
        # 6. Verificar consistencia de las consultas.
        # -------------------------------------------------

        mensualidad = self.entorno.mensualidad(
            placa_activa
        )

        consulta = self.consultar_vehiculo_api(
            placa_activa
        )

        self.assertEqual(
            mensualidad["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            mensualidad["fecha_corte"],
            consulta["fecha_corte"]
        )

        respuesta = self.entorno.solicitud(
            "GET",
            f"/api/clientes/{registro_activo['id_cliente']}",
            usuario="admin"
        )

        cliente = verificar_respuesta(
            respuesta,
            200
        )["cliente"]

        vehiculos = [
            vehiculo
            for vehiculo in cliente["vehiculos"]
            if vehiculo["placa"] == placa_activa
        ]

        self.assertEqual(
            len(vehiculos),
            1
        )

        self.assertEqual(
            vehiculos[0]["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            vehiculos[0]["fecha_corte"],
            mensualidad["fecha_corte"]
        )

        # El vehículo sin pagos debe continuar inactivo.

        self.assertEqual(
            self.entorno.mensualidad(placa_inactiva)[
                "estado_mensualidad"
            ],
            "INACTIVA"
        )

        self.assertEqual(
            consultar_pagos(placa_inactiva),
            []
        )

        # Solo se autorizó modificar marca y color
        # de uno de los vehículos independientes.

        final = capturar_estado()

        for tabla in (
            "clientes",
            "pagos",
            "estancias",
            "celdas"
        ):

            self.assertEqual(
                final[tabla],
                antes[tabla]
            )

        vehiculos_esperados = [
            vehiculo_esperado
            if fila["placa"] == placa_activa
            else fila
            for fila in antes["vehiculos"]
        ]

        self.assertEqual(
            final["vehiculos"],
            vehiculos_esperados
        )