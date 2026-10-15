from datetime import date

from app import formatacao as fmt


def test_reais():
    assert fmt.reais(1234.5) == "R$ 1.234"
    assert fmt.reais(1234.5, casas=2) == "R$ 1.234,50"
    assert fmt.reais(950) == "R$ 950"
    assert fmt.reais(float("nan")) == fmt.SEM_DADO
    assert fmt.reais(None) == fmt.SEM_DADO


def test_numero_km_e_area():
    assert fmt.numero(1234567) == "1.234.567"
    assert fmt.km(2.345) == "2,3 km"
    assert fmt.metros_quadrados(37.0) == "37 m²"


def test_data():
    assert fmt.data(date(2026, 10, 15)) == "15/10/2026"
