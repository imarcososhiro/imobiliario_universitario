"""Testes da coleta completa contra um "site falso" que serve as fixtures salvas."""
import csv

import httpx
import pytest

from scraper import cardinali, coleta
from scraper.coleta import Falha, ResultadoColeta, coletar, validar
from scraper.download import criar_cliente
from scraper.modelo import COLUNAS, Imovel
from tests.conftest import ler_fixture

LUTFALLA = "/alugar/Sao-Carlos/Apartamento/Padrao/Jardim-Lutfalla/241116"
CENTRO = "/alugar/Sao-Carlos/Apartamento/Padrao/Centro/241165"
SANTA_MONICA = "/Sao-Carlos/Apartamento/Padrao/Parque-Santa-Monica/240579"
VILA_MONTEIRO = "/alugar/Sao-Carlos/Casa/Padrao/Vila-Monteiro-Gleba-I/203503"
RETIRADO = "/alugar/Sao-Carlos/Apartamento/Padrao/Centro/999"


def listagem(total, *links):
    cards = "".join(f'<div class="card-imo"><a href="{link}">ver</a></div>' for link in links)
    return (f"<h1>{total} imóveis em São Carlos, SP para locação</h1>{cards}"
            '<ul class="pagination"><li><a href="JavaScript:void(0);">»</a></li></ul>')


def site_falso(**substituicoes):
    paginas = {
        "/alugar/Sao-Carlos/Apartamento?pag=1": listagem(4, LUTFALLA, CENTRO, "/comprar" + SANTA_MONICA, RETIRADO),
        "/alugar/Sao-Carlos/Casa?pag=1": listagem(1, VILA_MONTEIRO),
        LUTFALLA: ler_fixture("imovel_bonificacao"),
        CENTRO: ler_fixture("imovel_completo"),
        "/alugar" + SANTA_MONICA: ler_fixture("imovel_venda_e_aluguel"),
        VILA_MONTEIRO: ler_fixture("imovel_consulte"),
    }
    paginas.update(substituicoes)

    def responder(request):
        caminho = request.url.raw_path.decode()
        if caminho in paginas:
            return httpx.Response(200, text=paginas[caminho])
        if caminho.startswith("/404"):
            return httpx.Response(200, text="não encontrado")
        return httpx.Response(302, headers={"Location": "/404.php"})

    return httpx.MockTransport(responder)


@pytest.fixture
def usar_site_falso(monkeypatch):
    def configurar(**substituicoes):
        transporte = site_falso(**substituicoes)
        monkeypatch.setattr(coleta, "criar_cliente", lambda: criar_cliente(transport=transporte))
    return configurar


def test_coleta_ponta_a_ponta():
    with criar_cliente(transport=site_falso()) as cliente:
        resultado = coletar(cardinali, cliente, hoje="2026-10-15")
    assert [imovel.codigo for imovel in resultado.imoveis] == [203503, 240579, 241116, 241165]
    assert resultado.anunciados == 5
    assert resultado.indisponiveis == 1
    assert resultado.falhas == []
    assert all(imovel.url.startswith(f"{cardinali.SITE}/alugar/") for imovel in resultado.imoveis)


def test_falha_em_um_anuncio_nao_derruba_a_coleta():
    with criar_cliente(transport=site_falso(**{CENTRO: "<html>layout novo</html>"})) as cliente:
        resultado = coletar(cardinali, cliente)
    assert len(resultado.imoveis) == 3
    assert len(resultado.falhas) == 1
    assert resultado.falhas[0].url.endswith(CENTRO)


def imoveis_falsos(quantidade):
    return [Imovel(codigo=i, fonte="teste", url="", tipo="", subtipo="", bairro="") for i in range(quantidade)]


def test_validar_aceita_coleta_normal():
    assert validar(ResultadoColeta(imoveis=imoveis_falsos(95)), quantidade_anterior=100) == []


def test_validar_recusa_coleta_vazia():
    assert validar(ResultadoColeta(), quantidade_anterior=None) == ["nenhum imóvel coletado"]


def test_validar_recusa_muitas_falhas():
    resultado = ResultadoColeta(imoveis=imoveis_falsos(80), falhas=[Falha("u", "erro")] * 20)
    assert "20 de 100 anúncios falharam" in validar(resultado, None)[0]


def test_validar_recusa_queda_brusca():
    assert "queda" in validar(ResultadoColeta(imoveis=imoveis_falsos(60)), quantidade_anterior=100)[0]


def test_main_grava_o_csv(tmp_path, usar_site_falso):
    usar_site_falso()
    saida = tmp_path / "imoveis.csv"
    assert coleta.main(["--saida", str(saida)]) == 0

    with saida.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        linhas = list(leitor)
    assert leitor.fieldnames == COLUNAS
    assert [linha["codigo"] for linha in linhas] == ["203503", "240579", "241116", "241165"]
    assert linhas[0]["total_mensal"] == ""  # aluguel "Consulte-nos"
    assert linhas[2]["total_mensal"] == "1554.0"


def test_main_nao_sobrescreve_quando_a_coleta_encolhe(tmp_path, usar_site_falso):
    usar_site_falso()
    saida = tmp_path / "imoveis.csv"
    coleta.salvar_csv(imoveis_falsos(20), saida)
    conteudo_anterior = saida.read_text(encoding="utf-8")

    assert coleta.main(["--saida", str(saida)]) == 1
    assert saida.read_text(encoding="utf-8") == conteudo_anterior


def test_main_falha_se_a_listagem_mudar(tmp_path, usar_site_falso):
    usar_site_falso(**{"/alugar/Sao-Carlos/Apartamento?pag=1": "<html>layout novo</html>"})
    saida = tmp_path / "imoveis.csv"
    assert coleta.main(["--saida", str(saida)]) == 1
    assert not saida.exists()


def test_main_escreve_resumo_no_github_actions(tmp_path, usar_site_falso, monkeypatch):
    usar_site_falso()
    resumo = tmp_path / "resumo.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumo))
    coleta.main(["--saida", str(tmp_path / "imoveis.csv")])
    assert "Coletados: 4" in resumo.read_text(encoding="utf-8")
