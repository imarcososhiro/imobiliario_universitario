from pathlib import Path

import pytest

from app.historico import VARIAVEL_URL

PASTA_FIXTURES = Path(__file__).parent / "fixtures" / "cardinali"


def ler_fixture(nome: str) -> str:
    return (PASTA_FIXTURES / f"{nome}.html").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def sem_espera_entre_tentativas(monkeypatch):
    """Nos testes, as novas tentativas de download acontecem sem esperar."""
    monkeypatch.setattr("scraper.download.ESPERA_BASE_S", 0)


@pytest.fixture(autouse=True)
def historico_sem_internet(monkeypatch, tmp_path):
    """Nenhum teste baixa o histórico do GitHub: por padrão, o dashboard procura um arquivo que não existe
    (e mostra a página sem o histórico). Os testes que precisam dele apontam para um arquivo sintético."""
    monkeypatch.setenv(VARIAVEL_URL, (tmp_path / "sem_historico.tar.gz").as_uri())
