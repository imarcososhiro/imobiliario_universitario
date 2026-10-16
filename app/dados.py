"""Lê o CSV do scraper e prepara os imóveis para o dashboard."""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

from app.bairros import padronizar_bairro
from app.metricas import adicionar_metricas, escolher_campus

CAMINHO_CSV = Path(__file__).resolve().parent.parent / "dados" / "imoveis.csv"
VALOR_MAXIMO = 8000  # Teto do projeto para o valor total (aluguel + condomínio + IPTU)
# Kitnets e studios às vezes vêm sem nº de dormitórios no site, mas têm um cômodo
SUBTIPOS_DE_UM_DORMITORIO = "kitchnet|kitnet|studio|flat"
DORMITORIOS_OU_MAIS = 4  # a opção "4+" do filtro


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_imoveis(caminho: Path = CAMINHO_CSV) -> pd.DataFrame:
    """Imóveis para morar disponíveis na cidade toda, com bairro padronizado e as métricas.

    Fica em cache por 1 hora: o CSV só muda uma vez por dia.
    """
    df = pd.read_csv(caminho)
    df["bairro"] = df["bairro"].map(padronizar_bairro)
    # Fica de fora o que não dá para alugar ou comparar: aluguel "Consulte-nos" (sem total), imóvel só
    # comercial e imóvel reservado (já tem alguém negociando, mesmo que ainda apareça no site)
    reservado = df["situacao"].fillna("").str.upper().str.startswith("RESERVADO")
    df = df[df["total_mensal"].notna() & (df["total_mensal"] <= VALOR_MAXIMO)
            & (df["finalidade"].fillna("") != "Comercial") & ~reservado].copy()

    um_comodo = df["subtipo"].str.lower().str.contains(SUBTIPOS_DE_UM_DORMITORIO, na=False)
    df.loc[um_comodo & df["dormitorios"].isna(), "dormitorios"] = 1
    df["coletado_em"] = pd.to_datetime(df["coletado_em"]).dt.date
    return adicionar_metricas(df)


@dataclass
class Filtros:
    campus: str = "USP"                                   # de onde medir a distância: "USP" ou "UFSCar"
    distancia_max_km: float | None = None                 # None = qualquer distância
    tipo: str | None = None                               # "Apartamento", "Casa" ou None (tanto faz)
    dormitorios: list[int] = field(default_factory=list)  # vazio = todos; 4 vale "4 ou mais"
    preco_max_por_pessoa: float | None = None             # None = sem limite


def aplicar_filtros(df: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    """Os imóveis que passam pelos filtros, com a distância até o campus escolhido em `distancia_km`."""
    df = escolher_campus(df, filtros.campus)
    selecao = pd.Series(True, index=df.index)
    if filtros.distancia_max_km is not None:
        selecao &= df["distancia_km"] <= filtros.distancia_max_km
    if filtros.tipo:
        selecao &= df["tipo"] == filtros.tipo
    if filtros.dormitorios:
        quatro_ou_mais = DORMITORIOS_OU_MAIS in filtros.dormitorios
        selecao &= df["dormitorios"].isin(filtros.dormitorios) | (quatro_ou_mais & (df["dormitorios"] >= DORMITORIOS_OU_MAIS))
    if filtros.preco_max_por_pessoa is not None:
        selecao &= df["custo_por_dormitorio"] <= filtros.preco_max_por_pessoa
    return df[selecao]
