"""Executa a coleta, confere se o resultado faz sentido e só então grava o CSV.

Uso: python -m scraper [--saida dados/imoveis.csv]
"""
import argparse
import csv
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scraper import cardinali
from scraper.download import PaginaIndisponivel, baixar, criar_cliente
from scraper.modelo import COLUNAS, Imovel

log = logging.getLogger("scraper")

SAIDA_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "imoveis.csv"
DOWNLOADS_SIMULTANEOS = 4
MAX_TAXA_FALHAS = 0.10          # mais de 10% dos anúncios com erro: o site provavelmente mudou
MIN_PROPORCAO_ANTERIOR = 0.70   # queda de mais de 30% em relação à última coleta gravada
FUSO_BRASILIA = timezone(timedelta(hours=-3))  # sem horário de verão desde 2019


@dataclass
class Falha:
    url: str
    motivo: str


@dataclass
class ResultadoColeta:
    imoveis: list[Imovel] = field(default_factory=list)
    falhas: list[Falha] = field(default_factory=list)
    indisponiveis: int = 0  # saíram do site entre a listagem e o download
    anunciados: int = 0     # total que o site diz ter


def coletar(fonte, cliente, hoje: str | None = None) -> ResultadoColeta:
    """Baixa e lê todos os imóveis de uma fonte. Um anúncio com erro não derruba os outros."""
    hoje = hoje or datetime.now(FUSO_BRASILIA).date().isoformat()
    urls, anunciados = fonte.listar_urls(cliente)
    log.info("%d links de imóveis encontrados (%d anunciados no site)", len(urls), anunciados)
    resultado = ResultadoColeta(anunciados=anunciados)

    def processar(url: str) -> Imovel:
        return fonte.extrair_imovel(baixar(cliente, url), url, coletado_em=hoje)

    with ThreadPoolExecutor(max_workers=DOWNLOADS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar, url): url for url in urls}
        for processados, futuro in enumerate(as_completed(futuros), start=1):
            url = futuros[futuro]
            try:
                resultado.imoveis.append(futuro.result())
            except PaginaIndisponivel:
                resultado.indisponiveis += 1
            except Exception as erro:
                # Diferente de um "except: pass": o erro é registrado e entra na taxa de falhas
                resultado.falhas.append(Falha(url, f"{type(erro).__name__}: {erro}"))
                log.warning("Falha em %s: %s", url, erro)
            if processados % 100 == 0:
                log.info("%d/%d imóveis processados", processados, len(urls))

    # Ordem fixa por código: o diff diário do CSV no git mostra só o que mudou
    por_codigo: dict[int, Imovel] = {}
    for imovel in sorted(resultado.imoveis, key=lambda im: im.codigo):
        por_codigo.setdefault(imovel.codigo, imovel)
    resultado.imoveis = list(por_codigo.values())
    return resultado


def validar(resultado: ResultadoColeta, quantidade_anterior: int | None) -> list[str]:
    """Lista os problemas que impedem gravar o resultado (lista vazia = tudo certo)."""
    problemas = []
    coletados = len(resultado.imoveis)
    tentados = coletados + len(resultado.falhas)
    if coletados == 0:
        problemas.append("nenhum imóvel coletado")
    elif len(resultado.falhas) / tentados > MAX_TAXA_FALHAS:
        problemas.append(f"{len(resultado.falhas)} de {tentados} anúncios falharam "
                         f"(limite: {MAX_TAXA_FALHAS:.0%})")
    if quantidade_anterior and coletados < quantidade_anterior * MIN_PROPORCAO_ANTERIOR:
        problemas.append(f"só {coletados} imóveis contra {quantidade_anterior} na coleta anterior "
                         f"(queda maior que {1 - MIN_PROPORCAO_ANTERIOR:.0%})")
    return problemas


def contar_linhas(caminho: Path) -> int | None:
    if not caminho.exists():
        return None
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return sum(1 for _ in csv.DictReader(arquivo))


def salvar_csv(imoveis: list[Imovel], caminho: Path) -> None:
    """Grava num arquivo temporário e troca no fim, para nunca deixar um CSV pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    with temporario.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(asdict(imovel) for imovel in imoveis)
    os.replace(temporario, caminho)


def escrever_resumo(resultado: ResultadoColeta, problemas: list[str], segundos: float) -> None:
    linhas = [
        f"Anunciados no site: {resultado.anunciados}",
        f"Coletados: {len(resultado.imoveis)}",
        f"Saíram do site durante a coleta: {resultado.indisponiveis}",
        f"Falhas: {len(resultado.falhas)}",
        f"Duração: {segundos:.0f} s",
    ]
    for linha in linhas:
        log.info(linha)

    # No GitHub Actions, o resumo também aparece na página da execução
    arquivo_resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if arquivo_resumo:
        with open(arquivo_resumo, "a", encoding="utf-8") as resumo:
            resumo.write("## Coleta de imóveis\n\n" + "\n".join(f"- {linha}" for linha in linhas) + "\n")
            for problema in problemas:
                resumo.write(f"\n> ❌ {problema}\n")
            if resultado.falhas:
                resumo.write("\n<details><summary>Falhas</summary>\n\n")
                resumo.write("\n".join(f"- {falha.url}: {falha.motivo}" for falha in resultado.falhas))
                resumo.write("\n</details>\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta imóveis para alugar e grava em CSV.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="caminho do CSV gerado")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # sem uma linha de log por requisição

    inicio = time.monotonic()
    try:
        with criar_cliente() as cliente:
            resultado = coletar(cardinali, cliente)
    except Exception:
        log.exception("A coleta não pôde ser concluída")
        return 1

    problemas = validar(resultado, contar_linhas(args.saida))
    escrever_resumo(resultado, problemas, time.monotonic() - inicio)
    if problemas:
        for problema in problemas:
            log.error(problema)
        log.error("O CSV NÃO foi atualizado, para não publicar dados quebrados.")
        return 1

    salvar_csv(resultado.imoveis, args.saida)
    log.info("%d imóveis gravados em %s", len(resultado.imoveis), args.saida)
    return 0
