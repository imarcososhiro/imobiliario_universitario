from pathlib import Path

import pytest

PASTA_FIXTURES = Path(__file__).parent / "fixtures" / "cardinali"


def ler_fixture(nome: str) -> str:
    return (PASTA_FIXTURES / f"{nome}.html").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def sem_espera_entre_tentativas(monkeypatch):
    """Nos testes, as novas tentativas de download acontecem sem esperar."""
    monkeypatch.setattr("scraper.download.ESPERA_BASE_S", 0)
