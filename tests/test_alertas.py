"""Testes do alerta de coleta quebrada, contra um GitHub falso que roda na própria máquina."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import pytest

from scraper import alertas

REPOSITORIO = "dono/repo"


class GitHubFalso:
    """Servidor HTTP local que imita a API de issues do GitHub e anota cada pedido recebido."""

    def __init__(self):
        self.issues = {}   # número -> issue
        self.pedidos = []  # (método, caminho, corpo)
        github = self

        class Atendente(BaseHTTPRequestHandler):
            def _responder(self, dados, status=200):
                corpo = json.dumps(dados).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def _anotar(self):
                tamanho = int(self.headers.get("Content-Length", 0))
                corpo = json.loads(self.rfile.read(tamanho)) if tamanho else None
                caminho = urlsplit(self.path).path.removeprefix(f"/repos/{REPOSITORIO}")
                github.pedidos.append((self.command, caminho, corpo))
                assert self.headers["Authorization"] == "Bearer token-falso"
                return caminho, corpo

            def do_GET(self):
                self._anotar()
                self._responder([issue for issue in github.issues.values() if issue["state"] == "open"])

            def do_POST(self):
                caminho, corpo = self._anotar()
                if caminho == "/issues":
                    numero = max(github.issues, default=0) + 1
                    github.issues[numero] = {"number": numero, "state": "open", **corpo}
                    self._responder(github.issues[numero], status=201)
                else:  # /issues/<número>/comments
                    self._responder({"id": len(github.pedidos)}, status=201)

            def do_PATCH(self):
                caminho, corpo = self._anotar()
                issue = github.issues[int(caminho.rsplit("/", 1)[1])]
                issue.update(corpo)
                self._responder(issue)

            def log_message(self, *_):  # sem uma linha no terminal a cada pedido
                pass

        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Atendente)
        self.url = f"http://127.0.0.1:{self.servidor.server_port}"

    def abrir_issue(self, numero, **outros):
        self.issues[numero] = {"number": numero, "state": "open", "title": alertas.TITULO, **outros}


@pytest.fixture
def github():
    falso = GitHubFalso()
    linha = threading.Thread(target=falso.servidor.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    linha.start()
    yield falso
    falso.servidor.shutdown()


def ambiente(github, **outros):
    return {"GITHUB_TOKEN": "token-falso", "GITHUB_REPOSITORY": REPOSITORIO, "GITHUB_API_URL": github.url,
            "GITHUB_SERVER_URL": "https://github.com", "GITHUB_RUN_ID": "42", **outros}


PASSOS_COM_FALHA_NO_SCRAPER = json.dumps({
    "dependencias": {"outcome": "success", "conclusion": "success", "outputs": {}},
    "scraper": {"outcome": "failure", "conclusion": "failure", "outputs": {}},
})


def test_falha_abre_uma_issue(github, tmp_path, capsys):
    log = tmp_path / "coleta.log"
    log.write_text("\n".join(f"linha {numero}" for numero in range(1, 101)), encoding="utf-8")

    assert alertas.main(["falhou", "--log", str(log)], ambiente(github, PASSOS=PASSOS_COM_FALHA_NO_SCRAPER)) == 0

    assert [(metodo, caminho) for metodo, caminho, _ in github.pedidos] == [("GET", "/issues"), ("POST", "/issues")]
    issue = github.issues[1]
    assert (issue["title"], issue["labels"]) == (alertas.TITULO, [alertas.ROTULO])
    assert "https://github.com/dono/repo/actions/runs/42" in issue["body"]
    assert "**Rodar o scraper**" in issue["body"]
    assert "linha 100" in issue["body"] and "linha 41" in issue["body"]  # as últimas 60 linhas do log
    assert "linha 40\n" not in issue["body"]
    assert capsys.readouterr().out.strip() == "aberta a issue #1"


def test_falha_comenta_na_issue_que_ja_esta_aberta(github, capsys):
    github.abrir_issue(7)
    alertas.main(["falhou"], ambiente(github))  # sem log e sem PASSOS: falhou na preparação
    metodo, caminho, corpo = github.pedidos[-1]
    assert (metodo, caminho) == ("POST", "/issues/7/comments")
    assert "uma etapa de preparação" in corpo["body"]
    assert list(github.issues) == [7]  # nenhuma issue nova
    assert capsys.readouterr().out.strip() == "comentado na issue #7"


def test_coleta_resolvida_fecha_o_aviso(github, capsys):
    github.abrir_issue(7)
    alertas.main(["resolvida"], ambiente(github))
    assert [(metodo, caminho) for metodo, caminho, _ in github.pedidos] == [
        ("GET", "/issues"), ("POST", "/issues/7/comments"), ("PATCH", "/issues/7")]
    assert github.issues[7]["state"] == "closed"
    assert capsys.readouterr().out.strip() == "fechadas: #7"


def test_coleta_resolvida_sem_aviso_aberto(github, capsys):
    alertas.main(["resolvida"], ambiente(github))
    assert [metodo for metodo, _, _ in github.pedidos] == ["GET"]
    assert capsys.readouterr().out.strip() == "nenhum aviso aberto"


def test_pull_request_com_o_rotulo_nao_conta_como_aviso(github):
    github.abrir_issue(3, pull_request={"url": "..."})  # a API de issues também lista PRs
    alertas.main(["resolvida"], ambiente(github))
    assert github.issues[3]["state"] == "open"


def test_sem_token_nao_faz_nada(github, capsys):
    assert alertas.main(["falhou"], {"GITHUB_REPOSITORY": REPOSITORIO}) == 2
    assert github.pedidos == []
    assert "GITHUB_TOKEN" in capsys.readouterr().err


def test_etapas_que_falharam():
    assert alertas.etapas_que_falharam(PASSOS_COM_FALHA_NO_SCRAPER) == ["Rodar o scraper"]
    assert alertas.etapas_que_falharam('{"outra": {"outcome": "failure"}}') == ["outra"]  # id sem nome conhecido
    assert alertas.etapas_que_falharam("não é JSON") == []
    assert alertas.etapas_que_falharam(None) == []

