
import unittest
from datetime import date

from app.services.mensualidad_service import proyectar_pago


class TestProyeccionPago(unittest.TestCase):

    # =====================================================
    # PRIMER PAGO
    # =====================================================

    def test_pu17_primer_pago_automovil(self):

        resultado = proyectar_pago(
            tipo_vehiculo="AUTOMOVIL",
            fecha_pago=date(2026, 11, 21),
            fecha_inicio_mensualidad=None,
            fecha_corte=None,
            num_pagos=0,
            hoy=date(2026, 11, 21)
        )

        self.assertEqual(resultado, {
            "tipo": "PRIMER_PAGO",
            "valor": 250000,
            "fecha_pago": date(2026, 11, 21),
            "fecha_inicio": date(2026, 11, 21),
            "dia_corte": 21,
            "periodo_inicio": date(2026, 11, 21),
            "periodo_fin": date(2026, 12, 21),
            "corte_esperado": None,
            "estado_resultante": "ACTIVA",
            "num_pagos_resultante": 1,
            "advertencia": None
        })


    def test_pu18_primer_pago_motocicleta(self):

        resultado = proyectar_pago(
            tipo_vehiculo="MOTO",
            fecha_pago=date(2026, 11, 21),
            fecha_inicio_mensualidad=None,
            fecha_corte=None,
            num_pagos=0,
            hoy=date(2026, 11, 21)
        )

        self.assertEqual(
            resultado["tipo"], "PRIMER_PAGO"
        )

        self.assertEqual(
            resultado["valor"], 100000
        )

        self.assertEqual(
            resultado["periodo_fin"],
            date(2026, 12, 21)
        )

        self.assertEqual(
            resultado["estado_resultante"], "ACTIVA"
        )


    # =====================================================
    # RENOVACIONES
    # =====================================================

    def test_pu19_renovacion_anticipada(self):

        resultado = proyectar_pago(
            tipo_vehiculo="AUTOMOVIL",
            fecha_pago=date(2026, 2, 3),
            fecha_inicio_mensualidad=date(2026, 1, 10),
            fecha_corte=date(2026, 2, 10),
            num_pagos=1,
            hoy=date(2026, 2, 3)
        )

        self.assertEqual(resultado, {
            "tipo": "RENOVACION",
            "valor": 250000,
            "fecha_pago": date(2026, 2, 3),
            "fecha_inicio": date(2026, 1, 10),
            "dia_corte": 10,
            "periodo_inicio": date(2026, 2, 10),
            "periodo_fin": date(2026, 3, 10),
            "corte_esperado": date(2026, 2, 10),
            "estado_resultante": "ACTIVA",
            "num_pagos_resultante": 2,
            "advertencia": None
        })


    def test_pu20_renovacion_tardia(self):

        resultado = proyectar_pago(
            tipo_vehiculo="CAMIONETA",
            fecha_pago=date(2026, 2, 15),
            fecha_inicio_mensualidad=date(2026, 1, 10),
            fecha_corte=date(2026, 2, 10),
            num_pagos=1,
            hoy=date(2026, 2, 15)
        )

        self.assertEqual(
            resultado["valor"], 250000
        )

        self.assertEqual(
            resultado["periodo_inicio"],
            date(2026, 2, 10)
        )

        self.assertEqual(
            resultado["periodo_fin"],
            date(2026, 3, 10)
        )

        self.assertEqual(
            resultado["dia_corte"], 10
        )

        self.assertEqual(
            resultado["estado_resultante"], "ACTIVA"
        )

        self.assertIsNone(resultado["advertencia"])


    def test_pu21_renovacion_dia_del_corte(self):

        resultado = proyectar_pago(
            tipo_vehiculo="AUTOMOVIL",
            fecha_pago=date(2026, 11, 21),
            fecha_inicio_mensualidad=date(2026, 10, 21),
            fecha_corte=date(2026, 11, 21),
            num_pagos=1,
            hoy=date(2026, 11, 21)
        )

        self.assertEqual(
            resultado["periodo_inicio"],
            date(2026, 11, 21)
        )

        self.assertEqual(
            resultado["periodo_fin"],
            date(2026, 12, 21)
        )

        self.assertEqual(
            resultado["estado_resultante"], "ACTIVA"
        )


    # =====================================================
    # MESES CORTOS Y ANIOS BISIESTOS
    # =====================================================

    def test_pu22_renovaciones_dia_31(self):

        inicio = date(2026, 1, 31)

        corte = date(2026, 2, 28)

        cortes_esperados = [
            date(2026, 3, 31),
            date(2026, 4, 30),
            date(2026, 5, 31),
            date(2026, 6, 30)
        ]

        for num_pagos, esperado in enumerate(
            cortes_esperados, 1
        ):

            with self.subTest(num_pagos=num_pagos):

                resultado = proyectar_pago(
                    tipo_vehiculo="AUTOMOVIL",
                    fecha_pago=corte,
                    fecha_inicio_mensualidad=inicio,
                    fecha_corte=corte,
                    num_pagos=num_pagos,
                    hoy=corte
                )

                self.assertEqual(
                    resultado["periodo_inicio"],
                    corte
                )

                self.assertEqual(
                    resultado["periodo_fin"],
                    esperado
                )

                self.assertEqual(
                    resultado["fecha_inicio"],
                    inicio
                )

                self.assertEqual(
                    resultado["dia_corte"], 31
                )

                self.assertEqual(
                    resultado["num_pagos_resultante"],
                    num_pagos + 1
                )

                corte = resultado["periodo_fin"]


    def test_pu23_renovacion_anio_bisiesto(self):

        resultado = proyectar_pago(
            tipo_vehiculo="AUTOMOVIL",
            fecha_pago=date(2028, 1, 25),
            fecha_inicio_mensualidad=date(2027, 12, 31),
            fecha_corte=date(2028, 1, 31),
            num_pagos=1,
            hoy=date(2028, 1, 25)
        )

        self.assertEqual(
            resultado["periodo_fin"],
            date(2028, 2, 29)
        )

        self.assertEqual(
            resultado["dia_corte"], 31
        )

        self.assertEqual(
            resultado["estado_resultante"], "ACTIVA"
        )


    # =====================================================
    # CONSISTENCIA DE COBERTURA
    # =====================================================

    def test_pu24_cobertura_resultante_vencida(self):

        resultado = proyectar_pago(
            tipo_vehiculo="AUTOMOVIL",
            fecha_pago=date(2026, 11, 21),
            fecha_inicio_mensualidad=date(2026, 8, 5),
            fecha_corte=date(2026, 9, 5),
            num_pagos=1,
            hoy=date(2026, 11, 21)
        )

        self.assertEqual(
            resultado["periodo_inicio"],
            date(2026, 9, 5)
        )

        self.assertEqual(
            resultado["periodo_fin"],
            date(2026, 10, 5)
        )

        self.assertEqual(
            resultado["estado_resultante"], "INACTIVA"
        )

        self.assertIsNotNone(
            resultado["advertencia"]
        )

        self.assertEqual(
            resultado["num_pagos_resultante"], 2
        )


    # =====================================================
    # VALIDACIONES Y OPERACIONES INVALIDAS
    # =====================================================

    def test_pu25_fecha_pago_futura(self):

        with self.assertRaises(ValueError):

            proyectar_pago(
                tipo_vehiculo="AUTOMOVIL",
                fecha_pago=date(2026, 11, 22),
                fecha_inicio_mensualidad=None,
                fecha_corte=None,
                num_pagos=0,
                hoy=date(2026, 11, 21)
            )


    def test_pu26_pago_anterior_al_inicio(self):

        with self.assertRaises(ValueError):

            proyectar_pago(
                tipo_vehiculo="AUTOMOVIL",
                fecha_pago=date(2026, 10, 1),
                fecha_inicio_mensualidad=date(2026, 10, 10),
                fecha_corte=date(2026, 11, 10),
                num_pagos=1,
                hoy=date(2026, 11, 21)
            )


    def test_pu27_fechas_inconsistentes(self):

        escenarios = [
            {
                "fecha_inicio_mensualidad": date(2026, 10, 21),
                "fecha_corte": None,
                "num_pagos": 1
            },
            {
                "fecha_inicio_mensualidad": None,
                "fecha_corte": date(2026, 11, 21),
                "num_pagos": 1
            },
            {
                "fecha_inicio_mensualidad": date(2026, 10, 21),
                "fecha_corte": date(2026, 11, 21),
                "num_pagos": 0
            }
        ]

        for escenario in escenarios:

            with self.subTest(escenario=escenario):

                with self.assertRaises(RuntimeError):

                    proyectar_pago(
                        tipo_vehiculo="AUTOMOVIL",
                        fecha_pago=date(2026, 11, 21),
                        hoy=date(2026, 11, 21),
                        **escenario
                    )


    def test_pu28_cobertura_incompatible(self):

        with self.assertRaises(RuntimeError):

            proyectar_pago(
                tipo_vehiculo="AUTOMOVIL",
                fecha_pago=date(2026, 11, 21),
                fecha_inicio_mensualidad=date(2026, 9, 21),
                fecha_corte=date(2026, 11, 21),
                num_pagos=1,
                hoy=date(2026, 11, 21)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
