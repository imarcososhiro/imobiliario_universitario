"""Testes do download, com respostas simuladas (sem acessar a internet)."""
import httpx
import pytest

from scraper.download import TENTATIVAS, FalhaDeDownload, PaginaIndisponivel, baixar, criar_cliente


def cliente_com(responder):
    """Cliente httpx cujas respostas vêm da função `responder(request)`."""
    return criar_cliente(transport=httpx.MockTransport(responder))


def test_tenta_de_novo_depois_de_erro_temporario():
    respostas = iter([httpx.Response(503), httpx.Response(200, text="ok")])
    with cliente_com(lambda request: next(respostas)) as cliente:
        assert baixar(cliente, "https://exemplo.com/a") == "ok"


def test_tenta_de_novo_depois_de_erro_de_conexao():
    chamadas = []

    def responder(request):
        chamadas.append(request)
        if len(chamadas) == 1:
            raise httpx.ConnectError("conexão recusada")
        return httpx.Response(200, text="ok")

    with cliente_com(responder) as cliente:
        assert baixar(cliente, "https://exemplo.com/a") == "ok"
    assert len(chamadas) == 2


def test_desiste_depois_de_todas_as_tentativas():
    chamadas = []

    def responder(request):
        chamadas.append(request)
        return httpx.Response(500)

    with cliente_com(responder) as cliente, pytest.raises(FalhaDeDownload):
        baixar(cliente, "https://exemplo.com/a")
    assert len(chamadas) == TENTATIVAS


def test_imovel_retirado_redireciona_para_404():
    def responder(request):
        if request.url.path == "/404.php":
            return httpx.Response(200, text="não encontrado")
        return httpx.Response(302, headers={"Location": "/404.php?id=1"})

    with cliente_com(responder) as cliente, pytest.raises(PaginaIndisponivel):
        baixar(cliente, "https://exemplo.com/alugar/1")


def test_erro_definitivo_nao_tenta_de_novo():
    chamadas = []

    def responder(request):
        chamadas.append(request)
        return httpx.Response(403)

    with cliente_com(responder) as cliente, pytest.raises(httpx.HTTPStatusError):
        baixar(cliente, "https://exemplo.com/a")
    assert len(chamadas) == 1


def test_iso_8859_1_e_lido_como_windows_1252():
    corpo = "Locação – “ótimo”".encode("cp1252")
    resposta = httpx.Response(200, content=corpo, headers={"Content-Type": "text/html; charset=ISO-8859-1"})
    with cliente_com(lambda request: resposta) as cliente:
        assert baixar(cliente, "https://exemplo.com/a") == "Locação – “ótimo”"
