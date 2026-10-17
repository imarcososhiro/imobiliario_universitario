"""Testes dos cartões dos imóveis (HTML montado em app/interface.py)."""
import pandas as pd

from app.interface import CSS, _cartao


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


def test_cartao_mostra_a_conta_do_preco_por_quarto():
    cartao = _cartao(imovel(), "USP")
    assert "R$ 900 <small>/quarto</small>" in cartao
    assert "R$ 1.800 por mês ÷ 2 quartos" in cartao
    kitnet = _cartao(imovel(custo_por_dormitorio=1100.0, total_mensal=1100.0, dormitorios=1.0), "USP")
    assert "1 quarto: é o total do mês" in kitnet
    # Sem nº de quartos não dá para dividir: mostra só o total
    sem_quartos = _cartao(imovel(custo_por_dormitorio=float("nan"), dormitorios=float("nan")), "USP")
    assert "R$ 1.800 <small>/mês</small>" in sem_quartos and "/quarto" not in sem_quartos


def test_cartao_com_a_distancia_ate_a_rodoviaria():
    assert "1,2 km da rodoviária · ~20 min a pé" in _cartao(imovel(), "Rodoviária")


def test_cartao_com_possivel_duplicata():
    cartao = _cartao(imovel(fonte="cardinali", duplicata_de="roca"), "USP")
    assert "Também na Roca?" in cartao and 'class="selo duplicata"' in cartao


def test_css_sem_nada_parecido_com_tag():
    # O st.html passa pelo DOMPurify, que joga fora o <style> inteiro se o texto dele tiver algo como
    # uma tag (um "<a>" num comentário, por exemplo): a página perderia todo o estilo, sem erro nenhum
    assert "<" not in CSS.strip().removeprefix("<style>").removesuffix("</style>")
