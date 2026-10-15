"""Consultas ao histórico com DuckDB: SQL direto nos arquivos Parquet, sem servidor.

Uso: python -m historico.consultas historico-data/snapshots

Atenção ao comparar períodos: até 14/10/2026 a coleta cobria só ~30 bairros da
região universitária (até R$ 8000); a partir de 15/10/2026 cobre a cidade toda.
"""
import argparse
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from historico.snapshot import PASTA_PADRAO

INICIO_CIDADE_TODA = date(2026, 10, 15)


def conectar(pasta: Path) -> duckdb.DuckDBPyConnection:
    """Abre o DuckDB com a view `snapshots`, que junta todos os dias num tabelão."""
    con = duckdb.connect()
    padrao = str(Path(pasta) / "**" / "*.parquet").replace("'", "''")
    # union_by_name: se uma coluna nova surgir no futuro, os dias antigos continuam legíveis
    con.execute(f"CREATE VIEW snapshots AS SELECT * FROM read_parquet('{padrao}', union_by_name = true)")
    return con


def datas_disponiveis(con) -> list[date]:
    return [linha[0] for linha in con.execute("SELECT DISTINCT coletado_em FROM snapshots ORDER BY 1").fetchall()]


def resumo_por_imovel(con) -> pd.DataFrame:
    """Uma linha por imóvel: quando apareceu, quando foi visto pela última vez e como o preço andou."""
    return con.sql("""
        SELECT
            fonte, codigo,
            arg_max(bairro, coletado_em)       AS bairro,
            arg_max(tipo, coletado_em)         AS tipo,
            arg_max(url, coletado_em)          AS url,
            min(coletado_em)                   AS primeira_vez,
            max(coletado_em)                   AS ultima_vez,
            count(*)                           AS dias_com_anuncio,
            arg_min(total_mensal, coletado_em) AS primeiro_total,
            arg_max(total_mensal, coletado_em) AS ultimo_total,
            min(total_mensal)                  AS menor_total,
            max(coletado_em) = (SELECT max(coletado_em) FROM snapshots) AS ainda_anunciado
        FROM snapshots
        GROUP BY fonte, codigo
        ORDER BY fonte, codigo
    """).df()


def mudancas_de_preco(con) -> pd.DataFrame:
    """Cada vez que o total mensal de um imóvel mudou em relação à observação anterior."""
    return con.sql("""
        SELECT *, total_novo - total_anterior AS variacao,
               round(100 * (total_novo - total_anterior) / total_anterior, 1) AS variacao_pct
        FROM (
            SELECT fonte, codigo, bairro, coletado_em,
                   round(lag(total_mensal) OVER imovel, 2) AS total_anterior,
                   round(total_mensal, 2)                  AS total_novo
            FROM snapshots
            WINDOW imovel AS (PARTITION BY fonte, codigo ORDER BY coletado_em)
        )
        WHERE total_anterior IS NOT NULL AND total_novo IS NOT NULL AND total_novo <> total_anterior
        ORDER BY coletado_em, fonte, codigo
    """).df()


def novidades(con, dia: date | None = None) -> dict[str, pd.DataFrame]:
    """O que mudou num dia em relação ao snapshot anterior.

    - novos: imóveis vistos pela primeira vez nesse dia
    - sairam: estavam no snapshot anterior e não estão mais
    - mudaram_de_preco: total mensal diferente do snapshot anterior
    """
    datas = datas_disponiveis(con)
    dia = dia or datas[-1]
    anteriores = [d for d in datas if d < dia]
    anterior = anteriores[-1] if anteriores else None

    novos = con.execute("""
        SELECT * FROM snapshots atual
        WHERE coletado_em = $dia
          AND NOT EXISTS (SELECT 1 FROM snapshots antes
                          WHERE antes.coletado_em < $dia
                            AND antes.fonte = atual.fonte AND antes.codigo = atual.codigo)
        ORDER BY fonte, codigo
    """, {"dia": dia}).df()
    sairam = con.execute("""
        SELECT * FROM snapshots antes
        WHERE coletado_em = $anterior
          AND NOT EXISTS (SELECT 1 FROM snapshots atual
                          WHERE atual.coletado_em = $dia
                            AND atual.fonte = antes.fonte AND atual.codigo = antes.codigo)
        ORDER BY fonte, codigo
    """, {"dia": dia, "anterior": anterior}).df()
    precos = mudancas_de_preco(con)
    return {
        "novos": novos,
        "sairam": sairam,
        "mudaram_de_preco": precos[precos["coletado_em"] == pd.Timestamp(dia)].reset_index(drop=True),
    }


def serie_por_bairro(con) -> pd.DataFrame:
    """Quantidade de imóveis e mediana do total mensal por bairro, dia a dia."""
    return con.sql("""
        SELECT coletado_em, bairro, count(*) AS imoveis, median(total_mensal) AS mediana_total
        FROM snapshots
        WHERE total_mensal IS NOT NULL
        GROUP BY coletado_em, bairro
        ORDER BY coletado_em, bairro
    """).df()


def ultima_observacao_por_semana(con) -> pd.DataFrame:
    """Uma linha por imóvel e semana (de segunda a domingo): como ele estava no último dia da semana.

    Contar cada imóvel uma vez por semana, e não uma vez por dia, evita que os anúncios que
    ficam muito tempo no site pesem mais numa mediana do que os que são alugados rápido.
    """
    return con.sql("""
        SELECT date_trunc('week', coletado_em) AS semana, *
        FROM snapshots
        QUALIFY row_number() OVER (PARTITION BY date_trunc('week', coletado_em), fonte, codigo
                                   ORDER BY coletado_em DESC) = 1
        ORDER BY semana, fonte, codigo
    """).df()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Mostra um resumo do histórico de imóveis.")
    parser.add_argument("pasta", type=Path, nargs="?", default=PASTA_PADRAO, help="pasta dos snapshots")
    args = parser.parse_args(argv)

    con = conectar(args.pasta)
    datas = datas_disponiveis(con)
    imoveis = resumo_por_imovel(con)
    saidos = imoveis[~imoveis["ainda_anunciado"]]
    precos = mudancas_de_preco(con)
    ultimo_dia = novidades(con)

    print(f"Histórico: {len(datas)} dias, de {datas[0]} a {datas[-1]}")
    print(f"Imóveis diferentes já vistos: {len(imoveis)} (ainda anunciados: {imoveis['ainda_anunciado'].sum()})")
    tempo_anunciado = (saidos["ultima_vez"] - saidos["primeira_vez"]).dt.days.median()
    print(f"Tempo mediano anunciado dos que já saíram: {tempo_anunciado:.0f} dias")
    print(f"Mudanças de preço: {len(precos)} ({(precos['variacao'] < 0).sum()} quedas, "
          f"{(precos['variacao'] > 0).sum()} aumentos)")
    print(f"Em {datas[-1]}: {len(ultimo_dia['novos'])} novos, {len(ultimo_dia['sairam'])} saíram, "
          f"{len(ultimo_dia['mudaram_de_preco'])} mudaram de preço")
    if datas[-1] == INICIO_CIDADE_TODA:
        print("(nesse dia a coleta passou a cobrir a cidade toda, por isso tantos imóveis novos)")


if __name__ == "__main__":
    main()
