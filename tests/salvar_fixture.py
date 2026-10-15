"""Baixa uma página do site e salva uma versão enxuta em tests/fixtures/ para os testes.

Uso: python -m tests.salvar_fixture <url> <nome>

Útil quando o site muda: salve a página que quebrou, escreva um teste com ela
e ajuste o parser até o teste passar.
"""
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment

from scraper.download import baixar, criar_cliente

PASTA = Path(__file__).parent / "fixtures" / "cardinali"


def enxugar(html: str) -> str:
    """Tira o que o parser não usa (CSS, SVG, scripts) para a fixture ficar pequena."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["style", "svg", "noscript", "iframe", "link"]):
        tag.decompose()
    for script in soup.find_all("script"):
        if script.get("type") != "application/ld+json":
            script.decompose()
    for comentario in soup.find_all(string=lambda texto: isinstance(texto, Comment)):
        comentario.extract()
    return str(soup)


def main() -> None:
    url, nome = sys.argv[1], sys.argv[2]
    with criar_cliente() as cliente:
        html = baixar(cliente, url)
    destino = PASTA / f"{nome}.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(enxugar(html), encoding="utf-8")
    print(f"{destino} ({destino.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
