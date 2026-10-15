"""Testes do parser da Cardinali com páginas reais salvas em tests/fixtures/.

Se o site mudar e a coleta começar a falhar, salve a página nova com
`python -m tests.salvar_fixture <url> <nome>` e veja aqui qual campo quebrou.
"""
import pytest

from scraper import cardinali
from scraper.cardinali import ErroDeExtracao, extrair_imovel, extrair_listagem
from tests.conftest import ler_fixture

SITE = cardinali.SITE


def extrair(nome_fixture, caminho):
    return extrair_imovel(ler_fixture(nome_fixture), f"{SITE}/alugar/Sao-Carlos/{caminho}", "2026-10-15")


def test_primeira_pagina_da_listagem():
    urls, tem_proxima, total = extrair_listagem(ler_fixture("listagem_primeira_pagina"))
    assert len(urls) == 27
    assert tem_proxima
    assert total == 692
    assert urls[0] == f"{SITE}/alugar/Sao-Carlos/Apartamento/Padrao/Vila-Jacobucci/241186"


def test_ultima_pagina_da_listagem():
    urls, tem_proxima, total = extrair_listagem(ler_fixture("listagem_ultima_pagina"))
    assert not tem_proxima
    assert total == 331
    assert len(urls) == 7
    # Códigos curtos também são imóveis
    assert f"{SITE}/alugar/Sao-Carlos/Casa/Padrao/Jardim-Nova-Santa-Paula/754" in urls
    # Links /comprar/ da listagem de aluguel viram /alugar/
    assert f"{SITE}/alugar/Sao-Carlos/Casa/Padrao/Centro/2269" in urls
    assert all("/comprar/" not in url for url in urls)


def test_normalizar_url_imovel():
    assert (cardinali.normalizar_url_imovel("/comprar/Sao-Carlos/Casa/Padrao/Centro/2269")
            == f"{SITE}/alugar/Sao-Carlos/Casa/Padrao/Centro/2269")


def test_imovel_com_bonificacao():
    imovel = extrair("imovel_bonificacao", "Apartamento/Padrao/Jardim-Lutfalla/241116")
    assert imovel.codigo == 241116
    assert imovel.fonte == "cardinali"
    assert (imovel.tipo, imovel.subtipo, imovel.bairro) == ("Apartamento", "Padrão", "Jardim Lutfalla")
    assert imovel.titulo == "Apartamento com 01 quarto ao lado da Usp."
    assert imovel.situacao == "DISPONÍVEL"
    assert imovel.aluguel == 1667.5
    assert imovel.aluguel_bonificado == 1334.0
    assert imovel.aluguel_anterior is None
    assert (imovel.condominio, imovel.iptu, imovel.total_mensal) == (190.0, 30.0, 1554.0)
    assert (imovel.dormitorios, imovel.banheiros, imovel.suites, imovel.vagas) == (1, 1, None, None)
    assert (imovel.area_util_m2, imovel.area_total_m2) == (37.0, 37.0)
    assert imovel.foto_url.startswith("https://")
    assert imovel.coletado_em == "2026-10-15"


def test_imovel_com_todas_as_caracteristicas():
    imovel = extrair("imovel_completo", "Apartamento/Padrao/Centro/241165")
    assert (imovel.dormitorios, imovel.suites, imovel.banheiros, imovel.vagas) == (2, 1, 2, 1)
    assert imovel.total_mensal == 3536.94


def test_aluguel_consulte_nos_fica_sem_total():
    # O site mostra "Total / Mês 160,00", que é só o IPTU: não é o custo real
    imovel = extrair("imovel_consulte", "Casa/Padrao/Vila-Monteiro-Gleba-I/203503")
    assert imovel.aluguel is None
    assert imovel.iptu == 160.0
    assert imovel.total_mensal is None
    assert imovel.bairro == "Vila Monteiro (Gleba I)"
    assert (imovel.area_util_m2, imovel.area_construida_m2, imovel.area_total_m2) == (95.0, 95.0, 150.0)


def test_imovel_em_promocao():
    imovel = extrair("imovel_promocao", "Casa/Padrao/Centro/240217")
    assert imovel.aluguel == 4900.0            # "POR: Aluguel"
    assert imovel.aluguel_anterior == 5556.0   # "DE: Aluguel"
    assert imovel.aluguel_bonificado is None
    assert imovel.total_mensal == 4900.0
    assert imovel.finalidade == "Comercial"


def test_imovel_a_venda_e_para_alugar_nao_usa_o_total_da_venda():
    imovel = extrair("imovel_venda_e_aluguel", "Apartamento/Padrao/Parque-Santa-Monica/240579")
    assert imovel.aluguel == 1900.0
    assert imovel.total_mensal == 2443.9  # e não o "Total" de R$ 390.000 da venda


def test_kitnet_sem_dormitorio_informado():
    imovel = extrair("imovel_kitnet", "Apartamento/Kitchnet-sem-Condominio/Jardim-Paraiso/204308")
    assert imovel.dormitorios is None
    assert imovel.subtipo == "Kitchnet sem Condomínio"
    assert imovel.bairro == "Jardim Paraíso"
    assert imovel.condominio is None


def test_pagina_sem_quadro_de_valores():
    html = ler_fixture("imovel_bonificacao").replace('id="valores_imovel"', 'id="outro"')
    with pytest.raises(ErroDeExtracao, match="valores"):
        extrair_imovel(html, f"{SITE}/alugar/Sao-Carlos/Apartamento/Padrao/Jardim-Lutfalla/241116")


def test_codigo_da_pagina_diferente_do_da_url():
    with pytest.raises(ErroDeExtracao, match="código"):
        extrair("imovel_bonificacao", "Apartamento/Padrao/Jardim-Lutfalla/999999")


def test_url_fora_do_padrao():
    with pytest.raises(ErroDeExtracao, match="URL"):
        extrair_imovel(ler_fixture("imovel_bonificacao"), f"{SITE}/imovel/241116")
