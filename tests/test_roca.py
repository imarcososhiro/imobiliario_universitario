"""Testes da Roca contra um site falso que serve o sitemap e a busca salvos em tests/fixtures/roca.

As respostas da busca são reais, sem o endereço, as coordenadas e as observações dos imóveis.
"""
import json
from pathlib import Path
from urllib.parse import unquote

import httpx
import pytest

from scraper import roca
from scraper.download import criar_cliente

PASTA = Path(__file__).parent / "fixtures" / "roca"
SITEMAP = (PASTA / "sitemap.xml").read_text(encoding="utf-8")
DOCS = {doc["idtProperty"]: doc for doc in json.loads((PASTA / "busca.json").read_text(encoding="utf-8"))
        ["response"]["docs"]}


def responder_roca(pedidos=None, sitemap=SITEMAP, busca=None):
    """O sitemap e a busca da Roca. A busca devolve só os códigos pedidos que estão nas fixtures."""
    def responder(request):
        caminho = unquote(request.url.raw_path.decode())
        if pedidos is not None:
            pedidos.append(caminho)
        if caminho == "/sitemaps/propertys.xml":
            return httpx.Response(200, text=sitemap)
        if caminho.startswith("/api/solr/search/"):
            if busca is not None:
                return httpx.Response(200, text=busca)
            consulta = json.loads(caminho.removeprefix("/api/solr/search/"))
            docs = [DOCS[codigo] for codigo in consulta["idtsPropertys"] if codigo in DOCS]
            return httpx.Response(200, json={"response": {"numFound": len(docs), "docs": docs}})
        return httpx.Response(404)
    return responder


def site_falso(**opcoes):
    return httpx.MockTransport(responder_roca(**opcoes))


def coletar(**opcoes):
    with criar_cliente(transport=site_falso(**opcoes)) as cliente:
        return roca.baixar_imoveis(cliente, "2026-10-16")


def test_sitemap_so_traz_casas_e_apartamentos_para_alugar_em_sao_carlos():
    imoveis = roca.listar_imoveis(SITEMAP)
    # Ficam de fora: um apartamento em Ribeirão Preto, um só à venda e um comercial
    assert sorted(imoveis) == sorted(DOCS)
    assert imoveis[61376] == ("https://roca.com.br/imovel/venda-e-locacao/apartamentos/sao-carlos/"
                              "jardim-paraiso-residencial-madre-st-bernard/61376")


def test_converte_um_apartamento():
    imovel = roca.imovel_da_busca(DOCS[61376], "https://roca.com.br/imovel/venda-e-locacao/apartamentos/x/y/61376",
                                  coletado_em="2026-10-16")
    assert (imovel.fonte, imovel.codigo, imovel.tipo, imovel.subtipo) == ("roca", 61376, "Apartamento", "Padrão")
    assert (imovel.bairro, imovel.situacao, imovel.finalidade) == ("Jardim Paraíso", "DISPONÍVEL", "Residencial")
    assert (imovel.aluguel, imovel.condominio, imovel.iptu) == (2223.0, 220.0, 80.0)
    assert imovel.total_mensal == 2523.0  # aluguel + condomínio + IPTU, como na Cardinali
    assert (imovel.dormitorios, imovel.banheiros, imovel.vagas, imovel.area_util_m2) == (1, 1, 1, 40.0)
    assert imovel.foto_url.startswith("https://") and imovel.coletado_em == "2026-10-16"


def test_reservado_comercial_e_bairro_em_maiusculas():
    def converter(codigo):
        return roca.imovel_da_busca(DOCS[codigo], roca.listar_imoveis(SITEMAP)[codigo])
    assert converter(65346).situacao == "RESERVADO"
    assert (converter(56678).tipo, converter(56678).finalidade) == ("Casa", "Comercial")  # casa para negócio
    assert converter(25287).bairro == "Centro"  # o site escreve "CENTRO"


APARTAMENTO = DOCS[61376]  # mostra o aluguel no site


@pytest.mark.parametrize("doc", [
    {**APARTAMENTO, "dtaPrevisionOutput": "2026-10-29T00:00:00Z"},  # ainda alugado: "Disponível em breve"
    {campo: valor for campo, valor in APARTAMENTO.items() if campo != "portalLocation"},  # escondido à mão
    {**APARTAMENTO, "flgHideValLocationSite": 1},  # a marcação da página, se a busca passar a trazê-la
], ids=["previsao_de_saida", "sem_portais", "marcacao_da_pagina"])
def test_aluguel_sob_consulta_fica_sem_aluguel_e_sem_total(doc):
    imovel = roca.imovel_da_busca(doc, "https://roca.com.br/imovel/locacao/apartamentos/x/y/61376")
    # Como o "Consulte-nos" da Cardinali: sem aluguel não há total, e o dashboard deixa o imóvel de fora
    assert (imovel.aluguel, imovel.total_mensal) == (None, None)
    assert (imovel.condominio, imovel.iptu) == (220.0, 80.0)  # esses o site continua mostrando


def test_imovel_real_disponivel_em_breve_fica_sem_aluguel():
    # A busca traz o aluguel (R$ 927,09), mas a página mostra "Disponível em breve" e "Valor sob consulta"
    assert DOCS[25287]["valLocation"] == 927.09 and DOCS[25287]["dtaPrevisionOutput"]
    assert roca.imovel_da_busca(DOCS[25287], roca.listar_imoveis(SITEMAP)[25287]).aluguel is None


def test_coleta_em_lotes(monkeypatch):
    monkeypatch.setattr(roca, "POR_PEDIDO", 4)
    pedidos = []
    resultado = coletar(pedidos=pedidos)
    assert pedidos[0] == "/sitemaps/propertys.xml"
    assert len(pedidos) == 3  # o sitemap e 2 lotes (6 imóveis, 4 por pedido)
    assert resultado.anunciados == 6
    assert resultado.nao_alugam_para_estudantes == 1  # o site marca esse imóvel assim: fica de fora
    assert sorted(imovel.codigo for imovel in resultado.imoveis) == sorted(set(DOCS) - {69667})
    assert (resultado.falhas, resultado.indisponiveis) == ([], 0)


def test_imovel_que_a_busca_nao_devolve_conta_como_indisponivel():
    linha = "<url><loc>https://roca.com.br/imovel/locacao/casas/sao-carlos/centro/999999</loc></url>"
    resultado = coletar(sitemap=SITEMAP.replace("</urlset>", linha + "</urlset>"))
    assert (resultado.anunciados, resultado.indisponiveis) == (7, 1)


def test_imovel_com_dado_estranho_vira_falha_sem_derrubar_os_outros(monkeypatch):
    estranho = {**DOCS[65246], "prop_char_5": "dois"}
    monkeypatch.setitem(DOCS, 65246, estranho)
    resultado = coletar()
    [(url, motivo)] = resultado.falhas
    assert url.endswith("/65246") and motivo.startswith("ValueError")
    assert len(resultado.imoveis) == 4


def test_busca_fora_do_formato_interrompe_e_guarda_a_resposta():
    with pytest.raises(roca.ErroDeExtracao) as erro:
        coletar(busca="<html>manutenção</html>")
    assert erro.value.html == "<html>manutenção</html>"


def test_busca_sem_portais_em_nenhum_imovel_interrompe(monkeypatch):
    # Se a busca deixar de trazer o campo, todos os imóveis ficariam "sob consulta" e a Roca sumiria
    # do dashboard em silêncio: a coleta falha (e abre a issue) em vez disso
    for codigo, doc in list(DOCS.items()):
        monkeypatch.setitem(DOCS, codigo, {campo: valor for campo, valor in doc.items() if campo != "portalLocation"})
    with pytest.raises(roca.ErroDeExtracao, match="portalLocation"):
        coletar()


def test_sitemap_sem_imoveis_interrompe():
    with pytest.raises(roca.ErroDeExtracao, match="sitemap"):
        coletar(sitemap='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>')


def test_fixtures_nao_guardam_endereco():
    for doc in DOCS.values():
        assert not {"fullAddress", "namStreet", "numNumber", "latitude", "longitude"} & set(doc)
