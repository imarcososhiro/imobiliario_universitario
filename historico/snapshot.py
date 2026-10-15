"""Guarda a coleta do dia como um arquivo Parquet no histórico.

Uso: python -m historico.snapshot dados/imoveis.csv --destino historico-data/snapshots

Cada dia vira um arquivo snapshots/AAAA/AAAA-MM-DD.parquet que não é reescrito
depois: assim o git guarda cada dia uma vez só e o histórico cresce devagar.
"""
import argparse
from dataclasses import fields
from pathlib import Path
from types import NoneType
from typing import get_args

import duckdb

from scraper.modelo import COLUNAS, Imovel

PASTA_PADRAO = Path("historico-data") / "snapshots"
TIPOS_SQL = {int: "BIGINT", float: "DOUBLE", str: "VARCHAR"}


def esquema() -> dict[str, str]:
    """Tipo SQL de cada coluna, derivado de scraper/modelo.py.

    Fixar os tipos evita que uma coluna toda vazia num dia vire texto e deixe
    os arquivos de dias diferentes incompatíveis entre si.
    """
    tipos = {}
    for campo in fields(Imovel):
        tipo_python = next(t for t in get_args(campo.type) or (campo.type,) if t is not NoneType)
        tipos[campo.name] = TIPOS_SQL[tipo_python]
    tipos["coletado_em"] = "DATE"
    return tipos


def caminho_snapshot(pasta: Path, data) -> Path:
    return pasta / str(data.year) / f"{data.isoformat()}.parquet"


def salvar_snapshot(caminho_csv: Path, pasta: Path) -> Path:
    """Converte o CSV de uma coleta em Parquet e devolve o caminho do arquivo."""
    con = duckdb.connect()
    tabela = con.read_csv(str(caminho_csv), header=True, dtype=esquema()).project(", ".join(COLUNAS))

    linhas, datas, imoveis, data = tabela.aggregate(
        "count(*), count(DISTINCT coletado_em), count(DISTINCT fonte || ':' || codigo), min(coletado_em)"
    ).fetchone()
    if linhas == 0:
        raise ValueError(f"{caminho_csv} está vazio")
    if datas != 1:
        raise ValueError(f"{caminho_csv} deveria ter uma única data de coleta, tem {datas}")
    if imoveis != linhas:
        raise ValueError(f"{caminho_csv} tem imóveis repetidos ({linhas} linhas, {imoveis} imóveis)")

    destino = caminho_snapshot(pasta, data)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabela.order("fonte, codigo").write_parquet(str(destino), compression="zstd")
    return destino


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Salva o CSV da coleta como snapshot Parquet.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--destino", type=Path, default=PASTA_PADRAO, help="pasta dos snapshots")
    args = parser.parse_args(argv)
    print(salvar_snapshot(args.csv, args.destino))


if __name__ == "__main__":
    main()
