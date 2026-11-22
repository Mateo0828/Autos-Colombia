"""
Autos Colombia - Iteración 3.

Pruebas de regresión de las funcionalidades
implementadas durante EA1 y EA2.

Plan académico PP-03:
PG-22 - Regresión de iteraciones anteriores.

Casos complementarios:
RG-01: Autenticación y control de acceso.
RG-02: Registro y asociación cliente-vehículos.
RG-03: Administración de clientes y vehículos.
RG-04: Administración de celdas.
RG-05: Operaciones del parqueadero.
RG-06: Integración completa EA1, EA2 y EA3.

Utiliza Flask Test Client y PostgreSQL aislado.
"""

from tests.e2e_helpers import (
    BasePruebaE2E,
    capturar_estado,
    consultar_uno,
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


# =========================================================
# PG-22 - REGRESION DE ITERACIONES ANTERIORES
# =========================================================

class TestRegresionIteraciones(BasePruebaE2E):

    def setUp(self):

        super().setUp()

        self.hoy = fecha_actual_colombia()


    # =====================================================
    # FUNCIONES AUXILIARES
    # =====================================================

    def solicitar(
        self,
        metodo,
        ruta,
        usuario="operador1",
        datos=None,
        esperado=200
    ):

        respuesta = self.entorno.solicitud(
            metodo,
            ruta,
            usuario=usuario,
            datos=datos
        )

        return verificar_respuesta(
            respuesta,
            esperado
        )


    def crear_vehiculo(
        self,
        tipo="AUTOMOVIL",
        documento=None
    ):

        return self.entorno.crear_vehiculo_prueba(
            tipo_vehiculo=tipo,
            documento=documento
        )


    def pagar(
        self,
        placa,
        usuario="operador1"
    ):

        consulta = self.entorno.mensualidad(
            placa,
            usuario=usuario,
            fecha_pago=self.hoy
        )

        return self.entorno.registrar_pago(
            placa=placa,
            fecha_pago=self.hoy,
            corte_esperado=consulta[
                "proximo_pago"
            ]["corte_esperado"],
            usuario=usuario
        )


    def consultar_cliente_db(
        self,
        id_cliente
    ):

        return consultar_uno(
            """
            SELECT *
            FROM cliente
            WHERE id_cliente = %s;
            """,
            (id_cliente,)
        )


    def consultar_celdas_disponibles(
        self,
        tipo
    ):

        resultado = self.solicitar(
            "GET",
            "/api/celdas/disponibles"
            f"?tipo_vehiculo={tipo}"
        )

        return {
            celda["codigo"]
            for celda in resultado["celdas"]
        }


    def verificar_parqueadero_libre(self):

        self.assertEqual(
            consultar_estancias_activas(),
            []
        )

        estado = self.solicitar(
            "GET",
            "/api/parqueadero/estado"
        )

        self.assertEqual(
            estado["vehiculos_dentro"],
            0
        )


    # =====================================================
    # RG-01 - AUTENTICACION Y CONTROL DE ACCESO
    # =====================================================

    def test_pg22_rg01_autenticacion_permisos(self):

        antes = capturar_estado()

        # -------------------------------------------------
        # Consultar la identidad de ambos perfiles.
        # -------------------------------------------------

        operador = self.solicitar(
            "GET",
            "/api/auth/me",
            usuario="operador1"
        )

        administrador = self.solicitar(
            "GET",
            "/api/auth/me",
            usuario="admin"
        )

        self.assertEqual(
            operador["usuario"]["rol"],
            "OPERADOR"
        )

        self.assertEqual(
            administrador["usuario"]["rol"],
            "ADMINISTRADOR"
        )

        # -------------------------------------------------
        # El administrador puede consultar usuarios.
        # -------------------------------------------------

        self.solicitar(
            "GET",
            "/api/usuarios",
            usuario="admin"
        )

        # -------------------------------------------------
        # El operador no puede administrar usuarios.
        # -------------------------------------------------

        self.solicitar(
            "GET",
            "/api/usuarios",
            usuario="operador1",
            esperado=403
        )

        # -------------------------------------------------
        # Consultas protegidas sin autenticación.
        # -------------------------------------------------

        rutas = (
            "/api/auth/me",
            "/api/estancias/activas",
            "/api/parqueadero/estado",
            "/api/celdas"
        )

        for ruta in rutas:

            with self.subTest(ruta=ruta):

                self.solicitar(
                    "GET",
                    ruta,
                    usuario=None,
                    esperado=401
                )

        # -------------------------------------------------
        # Cerrar sesión y verificar revocación del token.
        # -------------------------------------------------

        token_anterior = self.entorno.sesiones[
            "operador1"
        ]["token"]

        self.entorno.cerrar_sesion(
            "operador1"
        )

        respuesta = self.entorno.solicitud(
            "GET",
            "/api/auth/me",
            headers={
                "Authorization":
                    "Bearer " + token_anterior
            }
        )

        verificar_respuesta(
            respuesta,
            401
        )

        # Restaurar la sesión para operaciones posteriores.

        usuario = self.entorno.autenticar(
            "operador1"
        )

        self.assertEqual(
            usuario["id_operador"],
            self.operador["id_operador"]
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        print(
            "\nRG-01: autenticacion, permisos "
            "y revocacion correctos."
        )


    # =====================================================
    # RG-02 - REGISTRO CLIENTE Y VEHICULOS
    # =====================================================

    def test_pg22_rg02_registro_clientes_vehiculos(self):

        primero = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        segundo = self.crear_vehiculo(
            "MOTO",
            documento=primero["documento"]
        )

        self.assertEqual(
            primero["id_cliente"],
            segundo["id_cliente"]
        )

        self.assertNotEqual(
            primero["id_vehiculo"],
            segundo["id_vehiculo"]
        )

        self.assertNotEqual(
            primero["placa"],
            segundo["placa"]
        )

        cliente = self.solicitar(
            "GET",
            f"/api/clientes/{primero['id_cliente']}",
            usuario="admin"
        )["cliente"]

        placas = {
            vehiculo["placa"]
            for vehiculo in cliente["vehiculos"]
        }

        self.assertEqual(
            placas,
            {
                primero["placa"],
                segundo["placa"]
            }
        )

        # Ambos vehículos comienzan sin mensualidades.

        for registro in (
            primero,
            segundo
        ):

            placa = registro["placa"]

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
                consulta["fecha_corte"]
            )

            self.assertEqual(
                consultar_pagos(placa),
                []
            )

        # Pagar solamente el automóvil.

        self.pagar(
            primero["placa"]
        )

        self.assertEqual(
            self.entorno.mensualidad(
                primero["placa"]
            )["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            self.entorno.mensualidad(
                segundo["placa"]
            )["estado_mensualidad"],
            "INACTIVA"
        )

        self.assertEqual(
            consultar_pagos(
                segundo["placa"]
            ),
            []
        )

        # Intentar registrar nuevamente una placa.

        antes = capturar_estado()

        self.solicitar(
            "POST",
            "/api/registros",
            datos={
                "documento": primero["documento"],
                "nombre": "Cliente Prueba E2E",
                "placa": primero["placa"],
                "marca": "Marca duplicada",
                "color": "Rojo",
                "tipo_vehiculo": "AUTOMOVIL"
            },
            esperado=409
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        print(
            "\nRG-02: cliente con multiples vehiculos; "
            "mensualidades independientes."
        )


    # =====================================================
    # RG-03 - ADMINISTRACION DE CLIENTES Y VEHICULOS
    # =====================================================

    def test_pg22_rg03_administracion(self):

        registro = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        placa = registro["placa"]

        id_cliente = registro["id_cliente"]

        self.pagar(placa)

        pagos_originales = consultar_pagos(
            placa
        )

        vehiculo_original = consultar_vehiculo(
            placa
        )

        cliente_original = self.consultar_cliente_db(
            id_cliente
        )

        antes = capturar_estado()

        # -------------------------------------------------
        # El operador no puede modificar clientes.
        # -------------------------------------------------

        self.solicitar(
            "PUT",
            f"/api/clientes/{id_cliente}",
            datos={
                "nombre": "Nombre no autorizado"
            },
            esperado=403
        )

        # -------------------------------------------------
        # El operador no puede modificar vehículos.
        # -------------------------------------------------

        self.solicitar(
            "PUT",
            f"/api/vehiculos/{placa}",
            datos={
                "color": "Rojo"
            },
            esperado=403
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # El administrador modifica datos permitidos.
        # -------------------------------------------------

        nuevo_nombre = "Cliente E2E Actualizado"

        self.solicitar(
            "PUT",
            f"/api/clientes/{id_cliente}",
            usuario="admin",
            datos={
                "nombre": nuevo_nombre
            }
        )

        self.solicitar(
            "PUT",
            f"/api/vehiculos/{placa}",
            usuario="admin",
            datos={
                "marca": "Marca E2E Modificada",
                "color": "Blanco",
                "tipo_vehiculo": "CAMIONETA"
            }
        )

        self.assertEqual(
            self.consultar_cliente_db(
                id_cliente
            ),
            {
                **cliente_original,
                "nombre": nuevo_nombre
            }
        )

        self.assertEqual(
            consultar_vehiculo(placa),
            {
                **vehiculo_original,
                "marca": "Marca E2E Modificada",
                "color": "Blanco",
                "tipo_vehiculo": "CAMIONETA"
            }
        )

        self.assertEqual(
            consultar_pagos(placa),
            pagos_originales
        )

        # -------------------------------------------------
        # La placa continúa siendo inmutable.
        # -------------------------------------------------

        antes_rechazo = capturar_estado()

        self.solicitar(
            "PUT",
            f"/api/vehiculos/{placa}",
            usuario="admin",
            datos={
                "placa": "NUEVAPLACA"
            },
            esperado=422
        )

        self.assertEqual(
            capturar_estado(),
            antes_rechazo
        )

        consulta = self.solicitar(
            "GET",
            f"/api/vehiculos/{placa}"
        )["vehiculo"]

        self.assertEqual(
            consulta["tipo_vehiculo"],
            "CAMIONETA"
        )

        self.assertEqual(
            consulta["estado_mensualidad"],
            "ACTIVA"
        )

        self.assertEqual(
            consulta["fecha_corte"],
            vehiculo_original[
                "fecha_corte"
            ].isoformat()
        )

        print(
            "\nRG-03: administracion conservada; "
            "cobertura e historial protegidos."
        )


    # =====================================================
    # RG-04 - ADMINISTRACION DE CELDAS
    # =====================================================

    def test_pg22_rg04_administracion_celdas(self):

        codigo = seleccionar_celda(
            "MOTO"
        )

        antes = capturar_estado()

        def restaurar_celda():

            celda = consultar_celda(
                codigo
            )

            if celda["estado"] == "FUERA_DE_SERVICIO":

                self.solicitar(
                    "PATCH",
                    f"/api/celdas/{codigo}/habilitar",
                    usuario="admin"
                )

        self.addCleanup(
            restaurar_celda
        )

        # -------------------------------------------------
        # Consultar celdas según el perfil.
        # -------------------------------------------------

        self.solicitar(
            "GET",
            "/api/celdas",
            usuario="admin"
        )

        self.solicitar(
            "GET",
            "/api/celdas",
            usuario="operador1",
            esperado=403
        )

        disponibles = (
            self.consultar_celdas_disponibles(
                "MOTO"
            )
        )

        self.assertIn(
            codigo,
            disponibles
        )

        # -------------------------------------------------
        # El operador no puede deshabilitar celdas.
        # -------------------------------------------------

        self.solicitar(
            "PATCH",
            f"/api/celdas/{codigo}/deshabilitar",
            usuario="operador1",
            esperado=403
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # El administrador puede deshabilitar.
        # -------------------------------------------------

        self.solicitar(
            "PATCH",
            f"/api/celdas/{codigo}/deshabilitar",
            usuario="admin"
        )

        self.assertEqual(
            consultar_celda(codigo)["estado"],
            "FUERA_DE_SERVICIO"
        )

        self.assertNotIn(
            codigo,
            self.consultar_celdas_disponibles(
                "MOTO"
            )
        )

        # -------------------------------------------------
        # Restaurar disponibilidad.
        # -------------------------------------------------

        restaurar_celda()

        self.assertIn(
            codigo,
            self.consultar_celdas_disponibles(
                "MOTO"
            )
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        print(
            "\nRG-04: administracion, permisos "
            "y disponibilidad de celdas correctos."
        )


    # =====================================================
    # RG-05 - OPERACIONES DEL PARQUEADERO
    # =====================================================

    def test_pg22_rg05_operaciones_parqueadero(self):

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        self.pagar(placa)

        celda_a = seleccionar_celda(
            "MOTO"
        )

        celda_b = seleccionar_celda(
            "MOTO",
            excluir=(celda_a,)
        )

        celda_incompatible = seleccionar_celda(
            "AUTOMOVIL"
        )

        antes = capturar_estado()

        # -------------------------------------------------
        # Rechazar celda incompatible.
        # -------------------------------------------------

        self.entorno.registrar_entrada(
            placa,
            celda_incompatible,
            esperado=400
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # -------------------------------------------------
        # Registrar entrada válida.
        # -------------------------------------------------

        entrada = self.entorno.registrar_entrada(
            placa,
            celda_a
        )

        id_estancia = entrada[
            "estancia"
        ]["id_estancia"]

        self.assertEqual(
            consultar_celda(celda_a)["estado"],
            "OCUPADA"
        )

        self.assertNotIn(
            celda_a,
            self.consultar_celdas_disponibles(
                "MOTO"
            )
        )

        # -------------------------------------------------
        # Consultar estado del parqueadero.
        # -------------------------------------------------

        estado = self.solicitar(
            "GET",
            "/api/parqueadero/estado"
        )

        self.assertEqual(
            estado["vehiculos_dentro"],
            1
        )

        # -------------------------------------------------
        # Impedir deshabilitar una celda ocupada.
        # -------------------------------------------------

        self.solicitar(
            "PATCH",
            f"/api/celdas/{celda_a}/deshabilitar",
            usuario="admin",
            esperado=409
        )

        # -------------------------------------------------
        # Impedir modificación incompatible del vehículo.
        # -------------------------------------------------

        self.solicitar(
            "PUT",
            f"/api/vehiculos/{placa}",
            usuario="admin",
            datos={
                "tipo_vehiculo": "AUTOMOVIL"
            },
            esperado=409
        )

        # -------------------------------------------------
        # Proteger la reasignación mediante autenticación.
        # -------------------------------------------------

        antes_reasignacion = capturar_estado()

        self.solicitar(
            "PUT",
            f"/api/estancias/{placa}/reasignar-celda",
            usuario=None,
            datos={
                "nueva_celda": celda_b
            },
            esperado=401
        )

        self.assertEqual(
            capturar_estado(),
            antes_reasignacion
        )

        # -------------------------------------------------
        # Reasignar a una celda compatible disponible.
        # -------------------------------------------------

        self.solicitar(
            "PUT",
            f"/api/estancias/{placa}/reasignar-celda",
            datos={
                "nueva_celda": celda_b
            }
        )

        estancia = consultar_estancia(
            id_estancia
        )

        self.assertEqual(
            estancia["estado"],
            "ACTIVA"
        )

        self.assertEqual(
            estancia["id_celda"],
            consultar_celda(celda_b)["id_celda"]
        )

        self.assertEqual(
            consultar_celda(celda_a)["estado"],
            "DISPONIBLE"
        )

        self.assertEqual(
            consultar_celda(celda_b)["estado"],
            "OCUPADA"
        )

        self.assertEqual(
            len(consultar_estancias_activas(placa)),
            1
        )

        # -------------------------------------------------
        # Consultar vehículos dentro.
        # -------------------------------------------------

        activos = self.solicitar(
            "GET",
            "/api/estancias/activas"
        )

        self.assertEqual(
            activos["cantidad"],
            1
        )

        self.assertTrue(
            any(
                fila["id_estancia"] == id_estancia
                for fila in activos["vehiculos"]
            )
        )

        # -------------------------------------------------
        # Registrar salida.
        # -------------------------------------------------

        salida = self.entorno.registrar_salida(
            placa
        )

        self.assertEqual(
            salida["estancia"]["id_estancia"],
            id_estancia
        )

        self.assertEqual(
            consultar_estancia(id_estancia)["estado"],
            "FINALIZADA"
        )

        self.assertEqual(
            consultar_celda(celda_b)["estado"],
            "DISPONIBLE"
        )

        # Impedir registrar una segunda salida.

        antes_segunda_salida = capturar_estado()

        self.entorno.registrar_salida(
            placa,
            esperado=400
        )

        self.assertEqual(
            capturar_estado(),
            antes_segunda_salida
        )

        self.verificar_parqueadero_libre()

        # -------------------------------------------------
        # Verificar integridad global.
        # -------------------------------------------------

        final = capturar_estado()

        for tabla in (
            "clientes",
            "vehiculos",
            "pagos",
            "celdas"
        ):

            self.assertEqual(
                final[tabla],
                antes[tabla]
            )

        anteriores = {
            fila["id_estancia"]: fila
            for fila in antes["estancias"]
        }

        actuales = {
            fila["id_estancia"]: fila
            for fila in final["estancias"]
        }

        self.assertEqual(
            set(actuales) - set(anteriores),
            {id_estancia}
        )

        for identificador, fila in anteriores.items():

            self.assertEqual(
                actuales[identificador],
                fila
            )

        print(
            "\nRG-05: entrada, reasignacion, consultas "
            "y salida correctas."
        )


    # =====================================================
    # RG-06 - INTEGRACION COMPLETA DE ITERACIONES
    # =====================================================

    def test_pg22_rg06_flujo_integrado(self):

        # EA2: registro de un nuevo vehículo.

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        celda = seleccionar_celda(
            "MOTO"
        )

        self.assertEqual(
            self.entorno.mensualidad(placa)[
                "estado_mensualidad"
            ],
            "INACTIVA"
        )

        # EA1 + EA3: entrada inicialmente rechazada.

        antes = capturar_estado()

        self.entorno.registrar_entrada(
            placa,
            celda,
            esperado=400
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        # EA3: primer pago.

        primer_pago = self.pagar(
            placa
        )

        self.assertEqual(
            primer_pago["pago"]["tipo"],
            "PRIMER_PAGO"
        )

        self.assertEqual(
            primer_pago["mensualidad"][
                "estado_mensualidad"
            ],
            "ACTIVA"
        )

        # EA1: registrar entrada.

        entrada = self.entorno.registrar_entrada(
            placa,
            celda
        )

        id_estancia = entrada[
            "estancia"
        ]["id_estancia"]

        # EA1: registrar salida.

        self.entorno.registrar_salida(
            placa,
            usuario="admin"
        )

        self.assertEqual(
            consultar_estancia(id_estancia)["estado"],
            "FINALIZADA"
        )

        estancia_original = consultar_estancia(
            id_estancia
        )

        # EA3: renovar mensualidad.

        renovacion = self.pagar(
            placa,
            usuario="admin"
        )

        self.assertEqual(
            renovacion["pago"]["tipo"],
            "RENOVACION"
        )

        self.assertEqual(
            renovacion["pago"]["periodo_inicio"],
            primer_pago["pago"]["periodo_fin"]
        )

        self.assertEqual(
            renovacion["mensualidad"]["num_pagos"],
            2
        )

        historial = self.entorno.historial(
            placa
        )

        self.assertEqual(
            historial["cantidad"],
            2
        )

        self.assertEqual(
            historial["pagos"][0]["id_pago"],
            renovacion["pago"]["id_pago"]
        )

        self.assertEqual(
            historial["pagos"][1]["id_pago"],
            primer_pago["pago"]["id_pago"]
        )

        self.assertEqual(
            consultar_estancia(id_estancia),
            estancia_original
        )

        self.assertEqual(
            consultar_celda(celda)["estado"],
            "DISPONIBLE"
        )

        # EA2: cerrar sesión.

        self.entorno.cerrar_sesion(
            "operador1"
        )

        self.solicitar(
            "GET",
            "/api/parqueadero/estado",
            usuario=None,
            esperado=401
        )

        self.entorno.autenticar(
            "operador1"
        )

        self.verificar_parqueadero_libre()

        print(
            "\nRG-06: flujo integrado EA1 + EA2 + EA3 "
            "completado correctamente."
        )