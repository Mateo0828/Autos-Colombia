
import unittest
from datetime import date

from app.services.mensualidad_service import (
    obtener_tarifa,
    validar_fecha_pago,
    calcular_fecha_corte,
    calcular_estado_mensualidad
)


class TestMensualidadService(unittest.TestCase):

    # =====================================================
    # TARIFAS MENSUALES
    # =====================================================

    def test_pu01_tarifa_automovil(self):
        self.assertEqual(
            obtener_tarifa("AUTOMOVIL"),
            250000
        )

    def test_pu02_tarifa_camioneta(self):
        self.assertEqual(
            obtener_tarifa("CAMIONETA"),
            250000
        )

    def test_pu03_tarifa_moto(self):
        self.assertEqual(
            obtener_tarifa("MOTO"),
            100000
        )

    def test_pu04_tipo_vehiculo_invalido(self):
        with self.assertRaises(ValueError):
            obtener_tarifa("CAMION")

    # =====================================================
    # CALCULO DE FECHAS DE CORTE
    # =====================================================

    def test_pu05_corte_ordinario(self):
        inicio = date(2026, 1, 15)

        esperados = [
            date(2026, 2, 15),
            date(2026, 3, 15),
            date(2026, 4, 15),
            date(2026, 5, 15),
            date(2026, 6, 15)
        ]

        for meses, esperado in enumerate(esperados, 1):
            with self.subTest(meses=meses):
                self.assertEqual(
                    calcular_fecha_corte(inicio, meses),
                    esperado
                )

    def test_pu06_corte_dia_31(self):
        inicio = date(2026, 1, 31)

        esperados = [
            date(2026, 2, 28),
            date(2026, 3, 31),
            date(2026, 4, 30),
            date(2026, 5, 31),
            date(2026, 6, 30)
        ]

        for meses, esperado in enumerate(esperados, 1):
            with self.subTest(meses=meses):
                self.assertEqual(
                    calcular_fecha_corte(inicio, meses),
                    esperado
                )

    def test_pu07_corte_dia_30(self):
        inicio = date(2026, 1, 30)

        esperados = [
            date(2026, 2, 28),
            date(2026, 3, 30),
            date(2026, 4, 30),
            date(2026, 5, 30),
            date(2026, 6, 30)
        ]

        for meses, esperado in enumerate(esperados, 1):
            with self.subTest(meses=meses):
                self.assertEqual(
                    calcular_fecha_corte(inicio, meses),
                    esperado
                )

    def test_pu08_anio_bisiesto(self):
        inicio = date(2027, 12, 31)

        esperados = [
            date(2028, 1, 31),
            date(2028, 2, 29),
            date(2028, 3, 31),
            date(2028, 4, 30),
            date(2028, 5, 31)
        ]

        for meses, esperado in enumerate(esperados, 1):
            with self.subTest(meses=meses):
                self.assertEqual(
                    calcular_fecha_corte(inicio, meses),
                    esperado
                )

        # Primer pago realizado el 29 de febrero.
        inicio_bisiesto = date(2028, 2, 29)

        self.assertEqual(
            calcular_fecha_corte(inicio_bisiesto, 12),
            date(2029, 2, 28)
        )

        self.assertEqual(
            calcular_fecha_corte(inicio_bisiesto, 13),
            date(2029, 3, 29)
        )

    def test_pu09_cambio_de_anio(self):
        self.assertEqual(
            calcular_fecha_corte(date(2026, 12, 31), 1),
            date(2027, 1, 31)
        )

    # =====================================================
    # VIGENCIA DE MENSUALIDADES
    # =====================================================

    def test_pu10_mensualidad_vigente(self):
        self.assertEqual(
            calcular_estado_mensualidad(
                date(2026, 12, 5),
                hoy=date(2026, 11, 21)
            ),
            "ACTIVA"
        )

    def test_pu11_corte_igual_a_hoy(self):
        self.assertEqual(
            calcular_estado_mensualidad(
                date(2026, 11, 21),
                hoy=date(2026, 11, 21)
            ),
            "INACTIVA"
        )

    def test_pu12_mensualidad_vencida(self):
        self.assertEqual(
            calcular_estado_mensualidad(
                date(2026, 11, 5),
                hoy=date(2026, 11, 21)
            ),
            "INACTIVA"
        )

    def test_pu13_mensualidad_sin_pagos(self):
        self.assertEqual(
            calcular_estado_mensualidad(
                None,
                hoy=date(2026, 11, 21)
            ),
            "INACTIVA"
        )

    # =====================================================
    # VALIDACION DE FECHAS DE PAGO
    # =====================================================

    def test_pu14_fecha_pago_valida(self):
        self.assertEqual(
            validar_fecha_pago(
                "2026-11-21",
                hoy=date(2026, 11, 21)
            ),
            date(2026, 11, 21)
        )

        self.assertEqual(
            validar_fecha_pago(
                "2026-11-15",
                hoy=date(2026, 11, 21)
            ),
            date(2026, 11, 15)
        )

    def test_pu15_fecha_pago_futura(self):
        with self.assertRaises(ValueError):
            validar_fecha_pago(
                "2026-11-22",
                hoy=date(2026, 11, 21)
            )

    def test_pu16_fecha_pago_invalida(self):
        fechas_invalidas = [
            None,
            "",
            "21/11/2026",
            "2026-02-30",
            "2026-13-01",
            "20261121",
            20261121
        ]

        for valor in fechas_invalidas:
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    validar_fecha_pago(
                        valor,
                        hoy=date(2026, 11, 21)
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
