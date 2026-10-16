"""Executa a coleta, confere se o resultado faz sentido e só então grava o CSV.

Uso: python -m scraper [--saida dados/imoveis.csv] [--falhas falhas]
"""
import argparse
import csv
import logging
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from scraper import cardinali, roca
from scraper.download import NOVAS_TENTATIVAS, PaginaIndisponivel, baixar, criar_cliente
from scraper.modelo import COLUNAS, Imovel

log = logging.getLogger("scraper")

SAIDA_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "imoveis.csv"
PASTA_FALHAS_PADRAO = Path("falhas")
FONTES = (cardinali, roca)  # cada imobiliária é um módulo em scraper/ com FONTE e o jeito de coletar
DOWNLOADS_SIMULTANEOS = 4
MAX_TAXA_FALHAS = 0.10          # mais de 10% dos anúncios com erro: o site provavelmente mudou
MIN_PROPORCAO_ANTERIOR = 0.70   # queda de mais de 30% em relação à última coleta gravada
FUSO_BRASILIA = timezone(timedelta(hours=-3))  # sem horário de verão desde 2019


@dataclass
class Falha:
    url: str
    motivo: str
    arquivo: str | None = None  # HTML salvo para investigar, quando a página chegou a ser baixada


@dataclass
class ResultadoColeta:
    imoveis: list[Imovel] = field(default_factory=list)
    falhas: list[Falha] = field(default_factory=list)
    indisponiveis: int = 0     # saíram do site entre a listagem e o download
    anunciados: int = 0        # total que o site diz ter
    novas_tentativas: int = 0  # downloads que precisaram ser repetidos


@dataclass
class Comparacao:
    """O que mudou em relação à coleta gravada anteriormente."""
    novos: int = 0
    sairam: int = 0
    mudaram_de_preco: int = 0


class ErroComPagina(Exception):
    """Erro ao ler uma página já baixada; guarda o HTML para investigar depois."""

    def __init__(self, erro: Exception, html: str):
        super().__init__(f"{type(erro).__name__}: {erro}")
        self.html = html


def salvar_html_da_falha(pasta: Path, url: str, html: str) -> str:
    """Grava o HTML de uma página que não pôde ser lida e devolve o nome do arquivo."""
    nome = re.sub(r"[^A-Za-z0-9]+", "_", urlsplit(url).path).strip("_")[-120:] or "pagina"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{nome}.html").write_text(html, encoding="utf-8")
    return f"{nome}.html"


def registrar_falhas(pasta: Path, falhas: list[Falha]) -> None:
    """Índice das falhas (URL, motivo, arquivo), junto dos HTMLs salvos."""
    pasta.mkdir(parents=True, exist_ok=True)
    with (pasta / "falhas.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["url", "motivo", "arquivo"])
        escritor.writeheader()
        escritor.writerows(asdict(falha) for falha in falhas)


def coletar(fonte, cliente, hoje: str | None = None, pasta_falhas: Path | None = None) -> ResultadoColeta:
    """Baixa e lê todos os imóveis de uma fonte. Um anúncio com erro não derruba os outros."""
    hoje = hoje or datetime.now(FUSO_BRASILIA).date().isoformat()
    tentativas_antes = NOVAS_TENTATIVAS.total
    if hasattr(fonte, "baixar_imoveis"):
        # Fontes com uma busca em JSON (como a Roca) trazem tudo em poucos pedidos, sem uma página por imóvel
        lote = fonte.baixar_imoveis(cliente, hoje)
        resultado = ResultadoColeta(imoveis=lote.imoveis, falhas=[Falha(url, motivo) for url, motivo in lote.falhas],
                                    indisponiveis=lote.indisponiveis, anunciados=lote.anunciados)
        return _finalizar(resultado, tentativas_antes)

    urls, anunciados = fonte.listar_urls(cliente)
    log.info("%d links de imóveis encontrados (%d anunciados no site)", len(urls), anunciados)
    resultado = ResultadoColeta(anunciados=anunciados)

    def processar(url: str) -> Imovel:
        html = baixar(cliente, url)
        try:
            return fonte.extrair_imovel(html, url, coletado_em=hoje)
        except Exception as erro:
            raise ErroComPagina(erro, html) from erro

    with ThreadPoolExecutor(max_workers=DOWNLOADS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar, url): url for url in urls}
        for processados, futuro in enumerate(as_completed(futuros), start=1):
            url = futuros[futuro]
            try:
                resultado.imoveis.append(futuro.result())
            except PaginaIndisponivel:
                resultado.indisponiveis += 1
            except Exception as erro:
                # Diferente de um "except: pass": o erro é registrado, entra na taxa de falhas
                # e, se a página chegou a ser baixada, o HTML fica guardado para investigar
                html = getattr(erro, "html", None)
                arquivo = salvar_html_da_falha(pasta_falhas, url, html) if html and pasta_falhas else None
                motivo = str(erro) if isinstance(erro, ErroComPagina) else f"{type(erro).__name__}: {erro}"
                resultado.falhas.append(Falha(url, motivo, arquivo))
                log.warning("Falha em %s: %s", url, motivo)
            if processados % 100 == 0:
                log.info("%d/%d imóveis processados", processados, len(urls))

    return _finalizar(resultado, tentativas_antes)


def _finalizar(resultado: ResultadoColeta, tentativas_antes: int) -> ResultadoColeta:
    # Ordem fixa por código: o diff diário do CSV no git mostra só o que mudou
    por_codigo: dict[int, Imovel] = {}
    for imovel in sorted(resultado.imoveis, key=lambda im: im.codigo):
        por_codigo.setdefault(imovel.codigo, imovel)
    resultado.imoveis = list(por_codigo.values())
    resultado.novas_tentativas = NOVAS_TENTATIVAS.total - tentativas_antes
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


def ler_anterior(caminho: Path) -> dict[str, dict[int, float | None]] | None:
    """Fonte -> {código: total mensal} da coleta gravada antes desta (None se não houver).

    Separado por fonte porque o mesmo código pode existir em imobiliárias diferentes.
    """
    if not caminho.exists():
        return None
    anterior: dict[str, dict[int, float | None]] = {}
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            total = float(linha["total_mensal"]) if linha["total_mensal"] else None
            anterior.setdefault(linha["fonte"], {})[int(linha["codigo"])] = total
    return anterior


def comparar(imoveis: list[Imovel], anterior: dict[int, float | None] | None) -> Comparacao | None:
    """O que mudou numa fonte em relação à coleta anterior dela (None se ela ainda não existia)."""
    if not anterior:
        return None
    atual = {imovel.codigo: imovel.total_mensal for imovel in imoveis}
    mudaram = sum(1 for codigo, total in atual.items()
                  if codigo in anterior and total is not None and anterior[codigo] is not None
                  and round(total, 2) != round(anterior[codigo], 2))
    return Comparacao(novos=len(atual.keys() - anterior.keys()), sairam=len(anterior.keys() - atual.keys()),
                      mudaram_de_preco=mudaram)


def salvar_csv(imoveis: list[Imovel], caminho: Path) -> None:
    """Grava num arquivo temporário e troca no fim, para nunca deixar um CSV pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    with temporario.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(asdict(imovel) for imovel in imoveis)
    os.replace(temporario, caminho)


def escrever_resumo(resultados: dict[str, ResultadoColeta], problemas: list[str], segundos: float,
                    comparacoes: dict[str, Comparacao | None]) -> None:
    """Uma tabela com uma coluna por imobiliária, no log e na página da execução do Actions."""
    def linha(rotulo, valor):
        return rotulo, [valor(fonte, resultado) for fonte, resultado in resultados.items()]

    def mudanca(campo):
        return lambda fonte, _: getattr(comparacoes[fonte], campo) if comparacoes.get(fonte) else "—"

    linhas = [
        linha("Anunciados no site", lambda _, r: r.anunciados),
        linha("Coletados", lambda _, r: len(r.imoveis)),
    ]
    if any(comparacoes.values()):
        linhas += [
            linha("Novos desde a última coleta", mudanca("novos")),
            linha("Saíram do site desde a última coleta", mudanca("sairam")),
            linha("Mudaram de preço", mudanca("mudaram_de_preco")),
        ]
    linhas += [
        linha("Saíram do site durante a coleta", lambda _, r: r.indisponiveis),
        linha("Falhas", lambda _, r: len(r.falhas)),
        linha("Novas tentativas de download", lambda _, r: r.novas_tentativas),
    ]
    for rotulo, valores in linhas:
        log.info("%s: %s", rotulo, " · ".join(f"{fonte} {valor}" for fonte, valor in zip(resultados, valores)))
    log.info("Duração: %.0f s", segundos)

    # No GitHub Actions, o resumo também aparece na página da execução
    arquivo_resumo = os.environ.get("GITHUB_STEP_SUMMARY")
    if arquivo_resumo:
        hoje = datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y")
        falhas = [falha for resultado in resultados.values() for falha in resultado.falhas]
        with open(arquivo_resumo, "a", encoding="utf-8") as resumo:
            resumo.write(f"## Coleta de imóveis · {hoje} · {segundos:.0f} s\n\n")
            resumo.write("| | " + " | ".join(resultados) + " |\n|---|" + "---:|" * len(resultados) + "\n")
            resumo.write("".join(f"| {rotulo} | " + " | ".join(map(str, valores)) + " |\n"
                                 for rotulo, valores in linhas))
            for problema in problemas:
                resumo.write(f"\n> ❌ {problema}\n")
            if falhas:
                resumo.write("\n<details><summary>Falhas (o HTML delas está no artefato "
                             "<code>paginas-com-falha</code>)</summary>\n\n")
                resumo.write("\n".join(f"- {falha.url}: {falha.motivo}" for falha in falhas))
                resumo.write("\n</details>\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta imóveis para alugar e grava em CSV.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="caminho do CSV gerado")
    parser.add_argument("--falhas", type=Path, default=PASTA_FALHAS_PADRAO,
                        help="pasta onde ficam os HTMLs das páginas que não puderam ser lidas")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # sem uma linha de log por requisição
    shutil.rmtree(args.falhas, ignore_errors=True)  # só as falhas desta execução

    inicio = time.monotonic()
    resultados: dict[str, ResultadoColeta] = {}
    # Tudo ou nada: se uma imobiliária falhar, o CSV inteiro fica como estava. Gravar só as outras
    # faria os imóveis dela "saírem" por um dia e bagunçaria o histórico de novidades
    for fonte in FONTES:
        try:
            with criar_cliente() as cliente:
                resultados[fonte.FONTE] = coletar(fonte, cliente, pasta_falhas=args.falhas)
        except Exception as erro:
            html = getattr(erro, "html", None)  # ex.: a página de listagem mudou de formato
            if html:
                arquivo = salvar_html_da_falha(args.falhas, f"{fonte.FONTE}_listagem", html)
                registrar_falhas(args.falhas, [Falha(f"{fonte.FONTE}: listagem", str(erro), arquivo)])
            log.exception("A coleta da fonte %s não pôde ser concluída", fonte.FONTE)
            return 1

    falhas = [falha for resultado in resultados.values() for falha in resultado.falhas]
    if falhas:
        registrar_falhas(args.falhas, falhas)
    anterior = ler_anterior(args.saida) or {}
    # Cada imobiliária é comparada com ela mesma: uma queda forte numa não fica escondida pelo total
    problemas = [f"{fonte}: {problema}" for fonte, resultado in resultados.items()
                 for problema in validar(resultado, len(anterior.get(fonte, {})) or None)]
    comparacoes = {fonte: comparar(resultado.imoveis, anterior.get(fonte)) for fonte, resultado in resultados.items()}
    escrever_resumo(resultados, problemas, time.monotonic() - inicio, comparacoes)
    if problemas:
        for problema in problemas:
            log.error(problema)
        log.error("O CSV NÃO foi atualizado, para não publicar dados quebrados.")
        return 1

    imoveis = [imovel for resultado in resultados.values() for imovel in resultado.imoveis]
    salvar_csv(imoveis, args.saida)
    log.info("%d imóveis gravados em %s", len(imoveis), args.saida)
    return 0
