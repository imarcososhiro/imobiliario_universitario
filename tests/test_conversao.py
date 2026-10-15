import pytest

from scraper.conversao import normalizar_texto, para_inteiro, para_numero


@pytest.mark.parametrize("texto, esperado", [
    ("1.667,50", 1667.5),
    ("190,00", 190.0),
    ("37.00 m²", 37.0),
    ("1.200", 1200.0),
    ("R$ 950", 950.0),
    ("1,667.50", 1667.5),
    ("390.000,00", 390000.0),
    ("Consulte-nos", None),
    ("", None),
    (None, None),
])
def test_para_numero(texto, esperado):
    assert para_numero(texto) == esperado


def test_para_inteiro():
    assert para_inteiro("2") == 2
    assert para_inteiro("Consulte-nos") is None


def test_normalizar_texto():
    assert normalizar_texto("  C. Bonificação ") == "c. bonificacao"
    assert normalizar_texto("Total /  Mês") == "total / mes"
