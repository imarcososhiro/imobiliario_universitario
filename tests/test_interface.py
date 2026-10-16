"""Testes dos cartões dos imóveis (HTML montado em app/interface.py)."""
import pandas as pd

from app.interface import _cartao


def imovel(**outros):
    base = {"fonte": "roca", "url": "https://roca.com.br/imovel/1", "foto_url": "https://foto/1.jpg",
            "titulo": "Apê <b>ótimo</b>", "subtipo": "Padrão", "tipo": "Apartamento", "bairro": "Centro",
            "custo_por_dormitorio": 900.0, "total_mensal": 1800.0, "total_anterior": float("nan"),
            "novo": False, "duplicata_de": float("nan"), "dormitorios": 2.0, "area_m2": 60.0, "distancia_km": 1.2}
    return pd.Series({**base, **outros})


def test_cartao_mostra_a_imobiliaria_e_escapa_o_que_vem_do_site():
    cartao = _cartao(imovel(), "USP")
    assert '<span class="imobiliaria">Roca</span>' in cartao
    assert "Apê &lt;b&gt;ótimo&lt;/b&gt;" in cartao  # o título do site não vira HTML
    assert "selo" not in cartao


def test_cartao_com_possivel_duplicata():
    cartao = _cartao(imovel(fonte="cardinali", duplicata_de="roca"), "USP")
    assert "Também na Roca?" in cartao and 'class="selo duplicata"' in cartao
