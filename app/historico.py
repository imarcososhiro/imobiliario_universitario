"""Histórico diário dos imóveis (branch `data`), baixado pelo dashboard quando ele precisa.

O Streamlit Cloud só tem o branch main. Por isso o app baixa o branch `data` inteiro como um
.tar.gz direto do GitHub (poucos MB), extrai os Parquet numa pasta temporária e consulta tudo
com DuckDB (historico/consultas.py). Se o download falhar, o dashboard continua funcionando,
só sem as novidades e sem a tendência de preços.
"""
import logging
import os
import re
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO
from urllib.request import urlopen

import duckdb
import pandas as pd
import streamlit as st

from app.dados import preparar_imoveis
from app.metricas import MINIMO_IMOVEIS_BAIRRO
from historico import consultas

URL_HISTORICO = "https://codeload.github.com/imarcososhiro/imobiliario_universitario/tar.gz/refs/heads/data"
VARIAVEL_URL = "HISTORICO_URL"  # os testes apontam para um .tar.gz local (file:///...), sem internet
TEMPO_LIMITE_S = 15
HORAS_EM_CACHE = 3
DIAS_NOVIDADE = 7  # "novo" e "baixou de preço" valem por uma semana
CHAVE = ["fonte", "codigo"]  # identifica o mesmo imóvel em dias diferentes

# Só estes arquivos saem do .tar.gz: <pasta do branch>/snapshots/AAAA/AAAA-MM-DD.parquet
SNAPSHOT = re.compile(r"[^/]+/snapshots/(?P<ano>\d{4})/(?P<dia>\d{4}-\d{2}-\d{2})\.parquet")
# Falhas esperadas: sem internet, GitHub fora do ar, arquivo cortado ou corrompido, Parquet ilegível
ERROS_DE_CARREGAMENTO = (OSError, EOFError, tarfile.TarError, duckdb.Error, ValueError)

logger = logging.getLogger(__name__)


@dataclass
class Historico:
    primeiro_dia: pd.Timestamp
    ultimo_dia: pd.Timestamp
    por_imovel: pd.DataFrame  # quando cada imóvel apareceu, último total e última mudança de preço
    semanal: pd.DataFrame     # cada imóvel em cada semana, limpo pelas mesmas regras do CSV do dia


def extrair_snapshots(arquivo: BinaryIO, pasta: Path) -> int:
    """Extrai os snapshots de um .tar.gz do branch `data` para a pasta e devolve quantos eram.

    Cada arquivo é gravado num caminho montado aqui, e não no que vem escrito dentro do .tar.gz:
    assim um nome malicioso como "../../algum_arquivo" não consegue escrever fora da pasta.
    """
    quantidade = 0
    with tarfile.open(fileobj=arquivo, mode="r|gz") as tar:  # "r|": lê aos poucos, enquanto baixa
        for membro in tar:
            nome = SNAPSHOT.fullmatch(membro.name)
            if not (membro.isfile() and nome):
                continue
            destino = pasta / nome["ano"] / f"{nome['dia']}.parquet"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(tar.extractfile(membro).read())
            quantidade += 1
    return quantidade


def ler_historico(pasta: Path) -> Historico:
    """Consulta os snapshots de uma pasta e separa o que o dashboard usa."""
    con = consultas.conectar(pasta)
    try:
        datas = consultas.datas_disponiveis(con)
        resumo = consultas.resumo_por_imovel(con)
        mudancas = consultas.mudancas_de_preco(con)
        semanal = consultas.ultima_observacao_por_semana(con)
    finally:
        con.close()  # solta os arquivos: no Windows, a pasta temporária só pode ser apagada depois

    # As mudanças já vêm em ordem de data: a última de cada imóvel é a mais recente
    ultima_mudanca = mudancas.groupby(CHAVE).tail(1).rename(columns={"coletado_em": "data_mudanca"})
    por_imovel = resumo[CHAVE + ["primeira_vez", "ultimo_total"]].merge(
        ultima_mudanca[CHAVE + ["data_mudanca", "total_anterior", "total_novo"]], on=CHAVE, how="left")
    # Inteiros com falta (dormitórios, vagas...) viram float, como acontece quando o pandas lê o CSV
    semanal = semanal.astype({coluna: "float64" for coluna in semanal.select_dtypes("Int64").columns})
    return Historico(pd.Timestamp(datas[0]), pd.Timestamp(datas[-1]), por_imovel, preparar_imoveis(semanal))


@st.cache_data(ttl=timedelta(hours=HORAS_EM_CACHE), show_spinner="Baixando o histórico de preços...")
def baixar_historico(url: str) -> Historico:
    """Baixa e lê o histórico. Fica em cache por algumas horas: ganha um dia novo só uma vez por dia."""
    with tempfile.TemporaryDirectory() as pasta, urlopen(url, timeout=TEMPO_LIMITE_S) as resposta:
        if extrair_snapshots(resposta, Path(pasta)) == 0:
            raise ValueError(f"nenhum snapshot em {url}")
        return ler_historico(Path(pasta))


def carregar_historico() -> Historico | None:
    """O histórico, ou None se ele não puder ser baixado agora: o dashboard funciona sem ele.

    Depois de uma falha, a mesma sessão não tenta de novo a cada clique (cada tentativa pode
    demorar até TEMPO_LIMITE_S segundos); recarregar a página tenta outra vez.
    """
    if st.session_state.get("historico_indisponivel"):
        return None
    try:
        return baixar_historico(os.environ.get(VARIAVEL_URL, URL_HISTORICO))
    except ERROS_DE_CARREGAMENTO as erro:
        logger.warning("Histórico indisponível: %s", erro)
        st.session_state["historico_indisponivel"] = True
        return None


def marcar_novidades(imoveis: pd.DataFrame, historico: Historico | None) -> pd.DataFrame:
    """Acrescenta aos imóveis do dia o que mudou nos últimos DIAS_NOVIDADE dias.

    - novo: visto pela primeira vez nesse período
    - total_anterior: o total por mês de antes, se a última mudança de preço foi uma queda
      nesse período (vazio nos outros imóveis)
    - novidade: novo ou baixou de preço
    """
    if historico is None or imoveis.empty:
        return imoveis.assign(novo=False, total_anterior=float("nan"), novidade=False)

    hoje = pd.Timestamp(imoveis["coletado_em"].max())
    inicio = hoje - timedelta(days=DIAS_NOVIDADE - 1)
    info = imoveis[CHAVE + ["total_mensal"]].merge(historico.por_imovel, on=CHAVE, how="left",
                                                   validate="one_to_one")
    info.index = imoveis.index
    info["total_mensal"] = info["total_mensal"].round(2)  # o histórico guarda as mudanças com 2 casas

    if historico.ultimo_dia < hoje:
        # O histórico em cache ainda não tem a coleta de hoje: o CSV entra como a observação mais recente
        info["primeira_vez"] = info["primeira_vez"].fillna(historico.ultimo_dia + timedelta(days=1))
        mudou = info["ultimo_total"].notna() & (info["total_mensal"] != info["ultimo_total"].round(2))
        info.loc[mudou, "data_mudanca"] = hoje
        info.loc[mudou, "total_anterior"] = info.loc[mudou, "ultimo_total"]
        info.loc[mudou, "total_novo"] = info.loc[mudou, "total_mensal"]

    # No primeiro dia do histórico e no dia em que a coleta passou a cobrir a cidade toda, centenas
    # de imóveis aparecem "pela primeira vez" sem serem novos de verdade: nesses dias, ninguém é novo
    sem_comparacao = [historico.primeiro_dia, pd.Timestamp(consultas.INICIO_CIDADE_TODA)]
    novo = (info["primeira_vez"] >= inicio) & ~info["primeira_vez"].isin(sem_comparacao)
    # Só vale se o preço de hoje ainda é o da queda (o imóvel pode ter subido de novo depois)
    baixou = ((info["data_mudanca"] >= inicio) & (info["total_novo"] < info["total_anterior"])
              & (info["total_mensal"] == info["total_novo"]))
    return imoveis.assign(novo=novo, total_anterior=info["total_anterior"].where(baixou), novidade=novo | baixou)


def tendencia_semanal(semanal: pd.DataFrame, coluna: str, rotulo: str, bairro: str | None = None) -> pd.DataFrame:
    """Mediana de `coluna` por semana: uma série com todos os imóveis (chamada `rotulo`) e,
    se pedir, outra só com os de um bairro.

    Semanas com menos de MINIMO_IMOVEIS_BAIRRO imóveis ficam de fora, como no resto do painel.
    Colunas: semana, serie, mediana, imoveis.
    """
    series = {rotulo: semanal}
    if bairro:
        series[bairro] = semanal[semanal["bairro"] == bairro]
    partes = []
    for nome, df in series.items():
        por_semana = df.dropna(subset=[coluna]).groupby("semana")[coluna].agg(mediana="median", imoveis="size")
        partes.append(por_semana[por_semana["imoveis"] >= MINIMO_IMOVEIS_BAIRRO].reset_index().assign(serie=nome))
    return pd.concat(partes, ignore_index=True)[["semana", "serie", "mediana", "imoveis"]]
