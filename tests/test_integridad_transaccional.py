"""
Autos Colombia - Iteración 3.

Pruebas automatizadas de integridad transaccional,
concurrencia de pagos y restricciones PostgreSQL.

Plan académico PP-03:

PG-09: Duplicidad y concurrencia de pagos.
PG-19: Atomicidad de las operaciones de pago.
PG-21: Restricciones de integridad PostgreSQL.

Las pruebas utilizan una base aislada y ejecutan
transacciones reales mediante Flask y psycopg.

Los fallos controlados permiten comprobar que
las operaciones incompletas no se persistan.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from psycopg.errors import (
    UniqueViolation,
    CheckViolation,
    ForeignKeyViolation
)

from tests.e2e_helpers import (
    BasePruebaE2E,
    BASE_PRUEBAS,
    verificar_base_pruebas,
    capturar_estado,
    consultar_vehiculo,
    consultar_pagos,
    verificar_respuesta
)

from app.database import get_connection

from app.services.mensualidad_service import (
    fecha_actual_colombia
)

import app.services.pago_service as pago_service


# =========================================================
# PRUEBAS DE INTEGRIDAD TRANSACCIONAL
# =========================================================

class TestIntegridadTransaccional(BasePruebaE2E):

    def setUp(self):

        super().setUp()

        self.hoy = fecha_actual_colombia()

        self.operador2 = self.entorno.autenticar(
            "operador2"
        )


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


    def proyectar(
        self,
        placa,
        usuario="operador1"
    ):

        consulta = self.entorno.mensualidad(
            placa,
            usuario=usuario,
            fecha_pago=self.hoy
        )

        return consulta["proximo_pago"]


    def construir_solicitud(
        self,
        placa,
        usuario="operador1"
    ):

        proyeccion = self.proyectar(
            placa,
            usuario=usuario
        )

        return {
            "placa": placa,
            "fecha_pago": self.hoy.isoformat(),
            "corte_esperado": (
                proyeccion["corte_esperado"]
            )
        }


    def solicitar_pago(
        self,
        datos,
        usuario="operador1"
    ):

        return self.entorno.solicitud(
            "POST",
            "/api/pagos",
            usuario=usuario,
            datos=datos
        )


    def pagar(
        self,
        placa,
        usuario="operador1"
    ):

        datos = self.construir_solicitud(
            placa,
            usuario=usuario
        )

        respuesta = self.solicitar_pago(
            datos,
            usuario=usuario
        )

        return verificar_respuesta(
            respuesta,
            201
        )


    def verificar_conflicto(
        self,
        respuesta
    ):

        cuerpo = verificar_respuesta(
            respuesta,
            409
        )

        self.assertEqual(
            cuerpo["mensaje"],
            (
                "La mensualidad ya fue actualizada; "
                "consulte de nuevo."
            )
        )

        return cuerpo


    def verificar_unico_pago_adicional(
        self,
        antes,
        placa,
        resultado,
        proyeccion
    ):
        """
        Comprueba que una operación exitosa
        haya creado exactamente un pago y modificado
        únicamente la cobertura del vehículo objetivo.
        """

        despues = capturar_estado()

        for tabla in (
            "clientes",
            "celdas",
            "estancias"
        ):

            self.assertEqual(
                despues[tabla],
                antes[tabla]
            )

        pagos_antes = {
            fila["id_pago"]: fila
            for fila in antes["pagos"]
        }

        pagos_despues = {
            fila["id_pago"]: fila
            for fila in despues["pagos"]
        }

        for identificador, fila in pagos_antes.items():

            self.assertEqual(
                pagos_despues[identificador],
                fila
            )

        id_pago = resultado["pago"]["id_pago"]

        self.assertEqual(
            set(pagos_despues) - set(pagos_antes),
            {id_pago}
        )

        pago = pagos_despues[id_pago]

        self.assertEqual(
            pago["valor"],
            Decimal(proyeccion["valor"])
        )

        self.assertEqual(
            pago["periodo_inicio"].isoformat(),
            proyeccion["periodo_inicio"]
        )

        self.assertEqual(
            pago["periodo_fin"].isoformat(),
            proyeccion["periodo_fin"]
        )

        self.assertEqual(
            pago["id_operador"],
            resultado["pago"]["registrado_por"][
                "id_operador"
            ]
        )

        vehiculos_antes = {
            fila["id_vehiculo"]: fila
            for fila in antes["vehiculos"]
        }

        vehiculos_despues = {
            fila["id_vehiculo"]: fila
            for fila in despues["vehiculos"]
        }

        self.assertEqual(
            set(vehiculos_antes),
            set(vehiculos_despues)
        )

        objetivo = consultar_vehiculo(
            placa
        )

        id_vehiculo = objetivo["id_vehiculo"]

        self.assertEqual(
            pago["id_vehiculo"],
            id_vehiculo
        )

        self.assertEqual(
            pago["id_cliente"],
            objetivo["id_cliente"]
        )

        for identificador, fila in vehiculos_antes.items():

            if identificador != id_vehiculo:

                self.assertEqual(
                    vehiculos_despues[identificador],
                    fila
                )

            else:

                esperado = dict(fila)

                if (
                    esperado[
                        "fecha_inicio_mensualidad"
                    ] is None
                ):

                    esperado[
                        "fecha_inicio_mensualidad"
                    ] = pago["periodo_inicio"]

                esperado["fecha_corte"] = (
                    pago["periodo_fin"]
                )

                self.assertEqual(
                    vehiculos_despues[identificador],
                    esperado
                )

        self.assertEqual(
            objetivo["fecha_corte"].isoformat(),
            proyeccion["periodo_fin"]
        )

        cantidad_anterior = sum(
            fila["id_vehiculo"] == id_vehiculo
            for fila in antes["pagos"]
        )

        consulta = self.entorno.mensualidad(
            placa
        )

        self.assertEqual(
            consulta["num_pagos"],
            cantidad_anterior + 1
        )

        self.assertEqual(
            consulta["fecha_corte"],
            proyeccion["periodo_fin"]
        )


    # =====================================================
    # CONCURRENCIA REAL DE PAGOS
    # =====================================================

    def ejecutar_pagos_concurrentes(
        self,
        datos
    ):
        """
        Sincroniza ambas solicitudes antes de
        adquirir el bloqueo real del vehículo.

        El repositorio original continúa ejecutando
        SELECT FOR UPDATE y las consultas posteriores.
        """

        barrera = Barrier(2)

        buscar_original = (
            pago_service.buscar_mensualidad
        )

        def buscar_sincronizado(
            *args,
            **kwargs
        ):

            if kwargs.get("bloquear", False):

                barrera.wait(timeout=15)

            return buscar_original(
                *args,
                **kwargs
            )

        with patch.object(
            pago_service,
            "buscar_mensualidad",
            side_effect=buscar_sincronizado
        ):

            with ThreadPoolExecutor(
                max_workers=2
            ) as ejecutor:

                futuros = (
                    ejecutor.submit(
                        self.solicitar_pago,
                        dict(datos),
                        "operador1"
                    ),

                    ejecutor.submit(
                        self.solicitar_pago,
                        dict(datos),
                        "operador2"
                    )
                )

                respuestas = [
                    futuro.result(timeout=30)
                    for futuro in futuros
                ]

        self.assertEqual(
            sorted(
                respuesta.status_code
                for respuesta in respuestas
            ),
            [201, 409]
        )

        exitoso = next(
            respuesta
            for respuesta in respuestas
            if respuesta.status_code == 201
        )

        conflicto = next(
            respuesta
            for respuesta in respuestas
            if respuesta.status_code == 409
        )

        resultado = verificar_respuesta(
            exitoso,
            201
        )

        self.verificar_conflicto(
            conflicto
        )

        operador_esperado = (
            self.operador["id_operador"]
            if respuestas[0].status_code == 201
            else self.operador2["id_operador"]
        )

        self.assertEqual(
            resultado["pago"]["registrado_por"][
                "id_operador"
            ],
            operador_esperado
        )

        return resultado


    # =====================================================
    # PG-09.1 - REPETICION DE SOLICITUD
    # =====================================================

    def test_pg09_01_repeticion_solicitud(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        datos = self.construir_solicitud(
            placa
        )

        proyeccion = self.proyectar(
            placa
        )

        self.assertIsNone(
            datos["corte_esperado"]
        )

        antes = capturar_estado()

        respuesta = self.solicitar_pago(
            datos
        )

        resultado = verificar_respuesta(
            respuesta,
            201
        )

        self.verificar_unico_pago_adicional(
            antes,
            placa,
            resultado,
            proyeccion
        )

        estado_confirmado = capturar_estado()

        # Simular doble clic o reenvío de la misma
        # solicitud sin consultar el nuevo corte.

        repetida = self.solicitar_pago(
            datos
        )

        self.verificar_conflicto(
            repetida
        )

        self.assertEqual(
            capturar_estado(),
            estado_confirmado
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            1
        )

        print(
            "\nPG-09.1: primer pago HTTP 201;"
            " repeticion HTTP 409;"
            " sin duplicidad."
        )


    # =====================================================
    # PG-09.2 - PRIMEROS PAGOS CONCURRENTES
    # =====================================================

    def test_pg09_02_primer_pago_concurrente(self):

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        proyeccion = self.proyectar(
            placa
        )

        datos_a = self.construir_solicitud(
            placa,
            usuario="operador1"
        )

        datos_b = self.construir_solicitud(
            placa,
            usuario="operador2"
        )

        self.assertEqual(
            datos_a,
            datos_b
        )

        self.assertIsNone(
            datos_a["corte_esperado"]
        )

        antes = capturar_estado()

        resultado = self.ejecutar_pagos_concurrentes(
            datos_a
        )

        self.assertEqual(
            resultado["pago"]["tipo"],
            "PRIMER_PAGO"
        )

        self.assertEqual(
            resultado["pago"]["valor"],
            100000
        )

        self.verificar_unico_pago_adicional(
            antes,
            placa,
            resultado,
            proyeccion
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            1
        )

        print(
            "\nPG-09.2: HTTP 201 y 409;"
            " un unico primer pago."
        )


    # =====================================================
    # PG-09.3 - RENOVACIONES CONCURRENTES
    # =====================================================

    def test_pg09_03_renovacion_concurrente(self):

        registro = self.crear_vehiculo(
            "AUTOMOVIL"
        )

        placa = registro["placa"]

        primero = self.pagar(
            placa
        )

        proyeccion = self.proyectar(
            placa
        )

        datos_a = self.construir_solicitud(
            placa,
            usuario="operador1"
        )

        datos_b = self.construir_solicitud(
            placa,
            usuario="operador2"
        )

        self.assertEqual(
            datos_a,
            datos_b
        )

        self.assertEqual(
            datos_a["corte_esperado"],
            primero["mensualidad"]["fecha_corte"]
        )

        antes = capturar_estado()

        resultado = self.ejecutar_pagos_concurrentes(
            datos_a
        )

        self.assertEqual(
            resultado["pago"]["tipo"],
            "RENOVACION"
        )

        self.assertEqual(
            resultado["pago"]["periodo_inicio"],
            primero["pago"]["periodo_fin"]
        )

        self.verificar_unico_pago_adicional(
            antes,
            placa,
            resultado,
            proyeccion
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            2
        )

        # Reenviar la proyección desactualizada.

        confirmado = capturar_estado()

        respuesta = self.solicitar_pago(
            datos_a,
            usuario="operador2"
        )

        self.verificar_conflicto(
            respuesta
        )

        self.assertEqual(
            capturar_estado(),
            confirmado
        )

        print(
            "\nPG-09.3: HTTP 201 y 409;"
            " una unica renovacion."
        )


    # =====================================================
    # PG-19.1 - FALLO DESPUES DE INSERTAR PAGO
    # =====================================================

    def test_pg19_01_rollback_despues_insertar(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        datos = self.construir_solicitud(
            placa
        )

        antes = capturar_estado()

        insertar_original = (
            pago_service.insertar_pago
        )

        evidencia = {}

        def insertar_y_fallar(
            *args,
            **kwargs
        ):
            """
            Ejecuta el INSERT real y verifica que
            la fila exista dentro de la transacción.

            Después provoca un fallo controlado
            antes de actualizar la cobertura.
            """

            pago = insertar_original(
                *args,
                **kwargs
            )

            cursor = kwargs["cursor"]

            cursor.execute(
                """
                SELECT id_pago
                FROM pago
                WHERE id_pago = %s;
                """,
                (pago["id_pago"],)
            )

            fila = cursor.fetchone()

            evidencia["id_pago"] = (
                pago["id_pago"]
            )

            evidencia["insertado"] = (
                fila is not None
            )

            raise RuntimeError(
                "Fallo E2E controlado despues del INSERT."
            )

        with patch.object(
            pago_service,
            "insertar_pago",
            side_effect=insertar_y_fallar
        ):

            respuesta = self.solicitar_pago(
                datos
            )

        verificar_respuesta(
            respuesta,
            500
        )

        self.assertTrue(
            evidencia.get("insertado")
        )

        self.assertIsNotNone(
            evidencia.get("id_pago")
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        self.assertEqual(
            consultar_pagos(placa),
            []
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

        # Una vez retirado el fallo simulado,
        # la misma solicitud debe funcionar.

        resultado = verificar_respuesta(
            self.solicitar_pago(datos),
            201
        )

        self.assertEqual(
            resultado["mensualidad"]["num_pagos"],
            1
        )

        print(
            "\nPG-19.1: INSERT real revertido;"
            " HTTP 500;"
            " reintento exitoso."
        )


    # =====================================================
    # PG-19.2 - FALLO DESPUES DE ACTUALIZAR COBERTURA
    # =====================================================

    def test_pg19_02_rollback_despues_actualizar(self):

        registro = self.crear_vehiculo(
            "MOTO"
        )

        placa = registro["placa"]

        self.pagar(
            placa
        )

        datos = self.construir_solicitud(
            placa
        )

        antes = capturar_estado()

        vehiculo_original = consultar_vehiculo(
            placa
        )

        actualizar_original = (
            pago_service.actualizar_cobertura
        )

        evidencia = {}

        def actualizar_y_fallar(
            *args,
            **kwargs
        ):
            """
            Ejecuta el UPDATE real después del INSERT
            del pago de renovación.

            Verifica que ambas escrituras sean visibles
            dentro de la transacción y provoca un fallo.
            """

            cobertura = actualizar_original(
                *args,
                **kwargs
            )

            cursor = kwargs["cursor"]

            id_vehiculo = kwargs["id_vehiculo"]

            cursor.execute(
                """
                SELECT fecha_corte
                FROM vehiculo
                WHERE id_vehiculo = %s;
                """,
                (id_vehiculo,)
            )

            fila = cursor.fetchone()

            evidencia["nuevo_corte"] = (
                fila["fecha_corte"]
            )

            evidencia["corte_actualizado"] = (
                fila["fecha_corte"]
                == cobertura["fecha_corte"]
            )

            cursor.execute(
                """
                SELECT COUNT(*) AS cantidad
                FROM pago
                WHERE id_vehiculo = %s;
                """,
                (id_vehiculo,)
            )

            evidencia["cantidad_pagos"] = (
                cursor.fetchone()["cantidad"]
            )

            raise RuntimeError(
                "Fallo E2E controlado despues del UPDATE."
            )

        with patch.object(
            pago_service,
            "actualizar_cobertura",
            side_effect=actualizar_y_fallar
        ):

            respuesta = self.solicitar_pago(
                datos,
                usuario="admin"
            )

        verificar_respuesta(
            respuesta,
            500
        )

        self.assertTrue(
            evidencia.get("corte_actualizado")
        )

        self.assertGreater(
            evidencia["nuevo_corte"],
            vehiculo_original["fecha_corte"]
        )

        self.assertEqual(
            evidencia["cantidad_pagos"],
            2
        )

        # Ambas escrituras deben revertirse.

        self.assertEqual(
            capturar_estado(),
            antes
        )

        self.assertEqual(
            consultar_vehiculo(placa),
            vehiculo_original
        )

        self.assertEqual(
            len(consultar_pagos(placa)),
            1
        )

        # Reintentar la renovación normalmente.

        resultado = verificar_respuesta(
            self.solicitar_pago(
                datos,
                usuario="admin"
            ),
            201
        )

        self.assertEqual(
            resultado["mensualidad"]["num_pagos"],
            2
        )

        self.assertEqual(
            resultado["pago"]["periodo_inicio"],
            vehiculo_original[
                "fecha_corte"
            ].isoformat()
        )

        print(
            "\nPG-19.2: INSERT y UPDATE reales revertidos;"
            " HTTP 500;"
            " reintento exitoso."
        )


    # =====================================================
    # COMPROBACION DIRECTA DE RESTRICCIONES SQL
    # =====================================================

    def verificar_restriccion(
        self,
        sentencia,
        parametros,
        excepcion_esperada,
        restriccion_esperada
    ):
        """
        Ejecuta una operación SQL inválida y comprueba
        que PostgreSQL la rechace por la restricción
        específica esperada.

        Todas las operaciones son revertidas,
        incluso si la prueba falla.
        """

        verificar_base_pruebas()

        conexion = get_connection()

        try:

            with conexion.cursor() as cursor:

                cursor.execute(
                    "SELECT current_database();"
                )

                self.assertEqual(
                    cursor.fetchone()[0],
                    BASE_PRUEBAS
                )

                with self.assertRaises(
                    excepcion_esperada
                ) as contexto:

                    cursor.execute(
                        sentencia,
                        parametros
                    )

                self.assertEqual(
                    contexto.exception.diag.constraint_name,
                    restriccion_esperada
                )

        finally:

            try:

                conexion.rollback()

            finally:

                conexion.close()


    # =====================================================
    # PG-21.1 - RESTRICCION UNIQUE
    # =====================================================

    def test_pg21_01_restriccion_unique(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        resultado = self.pagar(
            placa
        )

        id_pago = resultado["pago"]["id_pago"]

        antes = capturar_estado()

        self.verificar_restriccion(
            """
            INSERT INTO pago (
                id_vehiculo,
                id_cliente,
                id_operador,
                valor,
                fecha_pago,
                periodo_inicio,
                periodo_fin
            )
            SELECT
                id_vehiculo,
                id_cliente,
                id_operador,
                valor,
                fecha_pago,
                periodo_inicio,
                periodo_fin
            FROM pago
            WHERE id_pago = %s;
            """,
            (id_pago,),
            UniqueViolation,
            "uq_pago_vehiculo_periodo"
        )

        self.assertEqual(
            capturar_estado(),
            antes
        )

        print(
            "\nPG-21.1: restriccion UNIQUE verificada."
        )


    # =====================================================
    # PG-21.2 - RESTRICCIONES CHECK
    # =====================================================

    def test_pg21_02_restricciones_check(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        resultado = self.pagar(
            placa
        )

        id_pago = resultado["pago"]["id_pago"]

        antes = capturar_estado()

        casos = (

            (
                "Valor cero",

                """
                UPDATE pago
                SET valor = 0
                WHERE id_pago = %s;
                """,

                "chk_valor_pago"
            ),

            (
                "Valor negativo",

                """
                UPDATE pago
                SET valor = -100
                WHERE id_pago = %s;
                """,

                "chk_valor_pago"
            ),

            (
                "Periodo igual",

                """
                UPDATE pago
                SET periodo_fin = periodo_inicio
                WHERE id_pago = %s;
                """,

                "chk_periodo_pago"
            ),

            (
                "Periodo invertido",

                """
                UPDATE pago
                SET periodo_fin = periodo_inicio - 1
                WHERE id_pago = %s;
                """,

                "chk_periodo_pago"
            )
        )

        for nombre, sql, restriccion in casos:

            with self.subTest(
                caso=nombre
            ):

                self.verificar_restriccion(
                    sql,
                    (id_pago,),
                    CheckViolation,
                    restriccion
                )

                self.assertEqual(
                    capturar_estado(),
                    antes
                )

        print(
            "\nPG-21.2: cuatro restricciones CHECK"
            " verificadas."
        )


    # =====================================================
    # PG-21.3 - INTEGRIDAD REFERENCIAL
    # =====================================================

    def test_pg21_03_integridad_referencial(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        resultado = self.pagar(
            placa
        )

        id_pago = resultado["pago"]["id_pago"]

        antes = capturar_estado()

        casos = (

            (
                "id_vehiculo",
                "fk_pago_vehiculo"
            ),

            (
                "id_cliente",
                "fk_pago_cliente"
            ),

            (
                "id_operador",
                "fk_pago_operador"
            )
        )

        for columna, restriccion in casos:

            with self.subTest(
                columna=columna
            ):

                self.verificar_restriccion(
                    f"""
                    UPDATE pago
                    SET {columna} = -1
                    WHERE id_pago = %s;
                    """,
                    (id_pago,),
                    ForeignKeyViolation,
                    restriccion
                )

                self.assertEqual(
                    capturar_estado(),
                    antes
                )

        print(
            "\nPG-21.3: tres claves foraneas"
            " verificadas."
        )


    # =====================================================
    # PG-21.4 - CONSISTENCIA DE FECHAS
    # =====================================================

    def test_pg21_04_consistencia_fechas(self):

        registro = self.crear_vehiculo()

        placa = registro["placa"]

        self.pagar(
            placa
        )

        id_vehiculo = registro["id_vehiculo"]

        antes = capturar_estado()

        casos = (

            (
                "Fecha de corte nula",

                """
                UPDATE vehiculo
                SET fecha_corte = NULL
                WHERE id_vehiculo = %s;
                """
            ),

            (
                "Fecha de inicio nula",

                """
                UPDATE vehiculo
                SET fecha_inicio_mensualidad = NULL
                WHERE id_vehiculo = %s;
                """
            ),

            (
                "Corte anterior al inicio",

                """
                UPDATE vehiculo
                SET fecha_corte =
                    fecha_inicio_mensualidad - 1
                WHERE id_vehiculo = %s;
                """
            )
        )

        for nombre, sql in casos:

            with self.subTest(
                caso=nombre
            ):

                self.verificar_restriccion(
                    sql,
                    (id_vehiculo,),
                    CheckViolation,
                    "chk_fechas_mensualidad"
                )

                self.assertEqual(
                    capturar_estado(),
                    antes
                )

        print(
            "\nPG-21.4: consistencia de fechas"
            " verificada."
        )