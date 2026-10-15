"""Lê o CSV do scraper e prepara os imóveis para o dashboard."""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

from app.bairros import na_regiao_universitaria, padronizar_bairro
from app.metricas import adicionar_metricas

CAMINHO_CSV = Path(__file__).resolve().parent.parent / "dados" / "imoveis.csv"
VALOR_MAXIMO = 8000  # Teto do projeto para o valor total (aluguel + condomínio + IPTU)
# Kitnets e studios às vezes vêm sem nº de dormitórios no site, mas têm um cômodo
SUBTIPOS_DE_UM_DORMITORIO = "kitchnet|kitnet|studio|flat"
DORMITORIOS_OU_MAIS = 4  # a opção "4+" do filtro


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_imoveis(caminho: Path = CAMINHO_CSV) -> pd.DataFrame:
    """Imóveis residenciais da cidade toda, com bairro padronizado e as métricas de custo-benefício.

    Fica em cache por 1 hora: o CSV só muda uma vez por dia.
    """
    df = preparar_imoveis(pd.read_csv(caminho))
    df["coletado_em"] = pd.to_datetime(df["coletado_em"]).dt.date
    return df


def preparar_imoveis(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa uma tabela no formato de scraper/modelo.py e acrescenta as métricas.

    Serve tanto para o CSV do dia quanto para o histórico, que assim passam pelas mesmas regras.
    """
    df = df.assign(bairro=df["bairro"].map(padronizar_bairro))
    # Sem total (aluguel "Consulte-nos") não dá pra comparar; imóvel só comercial não é moradia
    df = df[df["total_mensal"].notna() & (df["total_mensal"] <= VALOR_MAXIMO)
            & (df["finalidade"].fillna("") != "Comercial")].copy()

    um_comodo = df["subtipo"].str.lower().str.contains(SUBTIPOS_DE_UM_DORMITORIO, na=False)
    df.loc[um_comodo & df["dormitorios"].isna(), "dormitorios"] = 1
    df["regiao_universitaria"] = df["bairro"].map(na_regiao_universitaria)
    df["reservado"] = df["situacao"].fillna("").str.upper().str.startswith("RESERVADO")
    return adicionar_metricas(df)


@dataclass
class Filtros:
    so_regiao_universitaria: bool = True
    incluir_reservados: bool = False
    tipo: str | None = None                               # "Apartamento", "Casa" ou None (todos)
    dormitorios: list[int] = field(default_factory=list)  # vazio = todos; 4 vale "4 ou mais"
    faixa_total: tuple[float, float] | None = None        # aluguel total por mês (mín, máx)


def aplicar_filtros(df: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    selecao = pd.Series(True, index=df.index)
    if filtros.so_regiao_universitaria:
        selecao &= df["regiao_universitaria"]
    if not filtros.incluir_reservados:
        selecao &= ~df["reservado"]
    if filtros.tipo:
        selecao &= df["tipo"] == filtros.tipo
    if filtros.dormitorios:
        quatro_ou_mais = DORMITORIOS_OU_MAIS in filtros.dormitorios
        selecao &= df["dormitorios"].isin(filtros.dormitorios) | (quatro_ou_mais & (df["dormitorios"] >= DORMITORIOS_OU_MAIS))
    if filtros.faixa_total:
        selecao &= df["total_mensal"].between(*filtros.faixa_total)
    return df[selecao]
