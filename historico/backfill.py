"""Reconstrói o histórico a partir das versões do CSV guardadas no git.

Uso: python -m historico.backfill --destino historico-data/snapshots

Desde nov/2025 o GitHub Actions commita o CSV da coleta quase todo dia, então
cada versão do arquivo no git é um retrato daquele dia. Este script lê todas as
versões, converte as do formato antigo (scraper com Selenium) para o formato
atual e salva um snapshot Parquet por dia.
"""
import argparse
import csv
import io
import logging
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from historico.snapshot import PASTA_PADRAO, salvar_snapshot
from scraper.cardinali import FONTE, ErroDeExtracao, normalizar_url_imovel, partes_da_url
from scraper.coleta import FUSO_BRASILIA, salvar_csv
from scraper.conversao import para_inteiro, para_numero
from scraper.modelo import Imovel

log = logging.getLogger(__name__)

# Caminhos que o CSV da coleta já teve no repositório, do mais antigo ao atual
ARQUIVOS_CSV = ("dados.csv", "dados/dados_imoveis.csv", "dados/imoveis.csv")
ARQUIVO_ATUAL = ARQUIVOS_CSV[-1]


@dataclass
class Versao:
    commit: str
    quando: datetime
    arquivo: str

    @property
    def dia(self) -> date:
        return self.quando.astimezone(FUSO_BRASILIA).date()


class NomesDoSite:
    """Nomes com acento de bairros e subtipos, aprendidos das coletas no formato atual.

    O scraper antigo tirava os nomes da URL ("Jardim-Paraiso"); o atual lê o nome
    exibido no site ("Jardim Paraíso"). Como o trecho da URL é o mesmo nos dois,
    dá para traduzir um no outro e manter os nomes iguais ao longo do histórico.
    """

    def __init__(self):
        self._bairros: dict[str, Counter] = defaultdict(Counter)
        self._subtipos: dict[str, Counter] = defaultdict(Counter)

    def aprender(self, url: str, subtipo: str, bairro: str) -> None:
        _, trecho_subtipo, trecho_bairro, _ = partes_da_url(url)
        self._subtipos[trecho_subtipo][subtipo] += 1
        self._bairros[trecho_bairro][bairro] += 1

    def bairro(self, trecho: str) -> str:
        return self._traduzir(self._bairros, trecho)

    def subtipo(self, trecho: str) -> str:
        return self._traduzir(self._subtipos, trecho)

    @staticmethod
    def _traduzir(conhecidos: dict[str, Counter], trecho: str) -> str:
        if conhecidos.get(trecho):
            return conhecidos[trecho].most_common(1)[0][0]
        return trecho.replace("-", " ")


def git(repo: Path, *argumentos: str) -> str:
    resultado = subprocess.run(["git", "-C", str(repo), *argumentos],
                               capture_output=True, text=True, encoding="utf-8", check=True)
    return resultado.stdout


def listar_versoes(repo: Path) -> list[Versao]:
    """Todas as versões dos CSVs da coleta no git (criações e alterações, não exclusões)."""
    saida = git(repo, "log", "--format=@%H %aI", "--name-only", "--diff-filter=AM", "--", *ARQUIVOS_CSV)
    versoes = []
    for bloco in saida.split("@")[1:]:
        cabecalho, *arquivos = bloco.strip().splitlines()
        commit, quando = cabecalho.split()
        versoes += [Versao(commit, datetime.fromisoformat(quando), arquivo.strip())
                    for arquivo in arquivos if arquivo.strip()]
    return versoes


def ultima_versao_por_dia(versoes: list[Versao]) -> dict[date, Versao]:
    """Se o CSV mudou mais de uma vez no mesmo dia (horário de Brasília), fica a última versão."""
    por_dia = {}
    for versao in sorted(versoes, key=lambda v: (v.quando, ARQUIVOS_CSV.index(v.arquivo))):
        por_dia[versao.dia] = versao
    return por_dia


def imovel_do_formato_antigo(linha: dict, dia: date, nomes: NomesDoSite) -> Imovel | None:
    """Converte uma linha do CSV do scraper antigo ("2.778,75", nomes vindos da URL)."""
    url = normalizar_url_imovel(linha["Link"])
    try:
        tipo, subtipo, bairro, codigo = partes_da_url(url)
    except ErroDeExtracao:
        return None

    aluguel = para_numero(linha.get("Aluguel Cheio"))
    aluguel_bonificado = para_numero(linha.get("Aluguel com Bonificação"))
    total_mensal = para_numero(linha.get("Total / Mês"))
    if aluguel is None and aluguel_bonificado is None:
        total_mensal = None  # "Consulte-nos": o total antigo era só condomínio + IPTU

    return Imovel(
        codigo=codigo,
        fonte=FONTE,
        url=url,
        tipo=tipo,
        subtipo=nomes.subtipo(subtipo),
        bairro=nomes.bairro(bairro),
        aluguel=aluguel,
        aluguel_bonificado=aluguel_bonificado,
        condominio=para_numero(linha.get("Condomínio")),
        iptu=para_numero(linha.get("IPTU")),
        total_mensal=total_mensal,
        dormitorios=para_inteiro(linha.get("Dormitórios")),
        suites=para_inteiro(linha.get("Suítes")),
        banheiros=para_inteiro(linha.get("Banheiros")),
        vagas=para_inteiro(linha.get("Garagens")),
        coletado_em=dia.isoformat(),
    )


def reconstruir(repo: Path, pasta: Path) -> list[Path]:
    """Gera um snapshot Parquet por dia a partir do histórico do git. Devolve os arquivos criados."""
    versoes = listar_versoes(repo)
    conteudo = {(v.commit, v.arquivo): git(repo, "show", f"{v.commit}:{v.arquivo}") for v in versoes}

    nomes = NomesDoSite()
    for versao in versoes:
        if versao.arquivo == ARQUIVO_ATUAL:
            for linha in csv.DictReader(io.StringIO(conteudo[versao.commit, versao.arquivo])):
                nomes.aprender(linha["url"], linha["subtipo"], linha["bairro"])

    criados = []
    with tempfile.TemporaryDirectory() as temporaria:
        for dia, versao in sorted(ultima_versao_por_dia(versoes).items()):
            texto = conteudo[versao.commit, versao.arquivo]
            caminho = Path(temporaria) / f"{dia}.csv"
            if versao.arquivo == ARQUIVO_ATUAL:
                caminho.write_text(texto, encoding="utf-8")
            else:
                por_codigo: dict[int, Imovel] = {}
                for linha in csv.DictReader(io.StringIO(texto)):
                    imovel = imovel_do_formato_antigo(linha, dia, nomes)
                    if imovel:
                        por_codigo.setdefault(imovel.codigo, imovel)
                salvar_csv(list(por_codigo.values()), caminho)
            try:
                criados.append(salvar_snapshot(caminho, pasta))
            except Exception as erro:
                log.warning("Versão de %s (%s, %s) ignorada: %s", dia, versao.commit[:7], versao.arquivo, erro)
    return criados


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Reconstrói o histórico de snapshots a partir do git.")
    parser.add_argument("--repo", type=Path, default=Path("."), help="repositório com o histórico do CSV")
    parser.add_argument("--destino", type=Path, default=PASTA_PADRAO, help="pasta dos snapshots")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)-7s %(message)s")

    criados = reconstruir(args.repo, args.destino)
    if criados:
        log.info("%d snapshots criados em %s (de %s a %s)",
                 len(criados), args.destino, criados[0].stem, criados[-1].stem)


if __name__ == "__main__":
    main()
