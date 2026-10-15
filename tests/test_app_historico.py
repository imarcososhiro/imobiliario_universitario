"""Testes do histórico no dashboard (app/historico.py), com snapshots Parquet sintéticos."""
import io
import tarfile
from datetime import date

import pandas as pd
import pytest

from app.historico import (baixar_historico, extrair_snapshots, ler_historico, marcar_novidades,
                           tendencia_semanal)
from historico.consultas import INICIO_CIDADE_TODA
from historico.snapshot import salvar_snapshot
from scraper.coleta import salvar_csv
from scraper.modelo import Imovel

HOJE = date(2026, 10, 20)


def imovel(codigo, total, dia, bairro="Centro", **outros):
    return Imovel(codigo=codigo, fonte="cardinali", url=f"https://www.cardinali.com.br/alugar/{codigo}",
                  tipo="Apartamento", subtipo="Padrão", bairro=bairro, total_mensal=total, dormitorios=2,
                  coletado_em=dia.isoformat(), **outros)


def salvar_dias(pasta, dias, tmp_path):
    """dias: {data: {codigo: total}} -> um snapshot Parquet por dia."""
    for dia, totais in dias.items():
        salvar_csv([imovel(codigo, total, dia) for codigo, total in totais.items()], tmp_path / "coleta.csv")
        salvar_snapshot(tmp_path / "coleta.csv", pasta)
    return pasta


# O que acontece com cada imóvel (HOJE = 20/10/2026):
# 1: baixou de 1000 para 900 no dia 18      -> baixou de preço
# 2: preço igual o tempo todo               -> nada
# 3: apareceu em 15/10, o dia em que a coleta passou a cobrir a cidade toda -> não conta como novo
# 4: apareceu no dia 18                     -> novo
# 5: apareceu hoje                          -> novo
# 6: baixou no dia 18 e subiu de novo hoje  -> nada (o preço de hoje não é o da queda)
# 7: baixou em 10/10, antes da última semana -> nada
DIAS = {
    date(2026, 9, 1): {1: 1000, 2: 2000, 6: 1500, 7: 3000},   # primeiro dia do histórico
    date(2026, 10, 10): {1: 1000, 2: 2000, 6: 1500, 7: 2800},
    INICIO_CIDADE_TODA: {1: 1000, 2: 2000, 3: 1200, 6: 1500, 7: 2800},
    date(2026, 10, 18): {1: 900, 2: 2000, 3: 1200, 4: 1100, 6: 1400, 7: 2800},
    HOJE: {1: 900, 2: 2000, 3: 1200, 4: 1100, 5: 800, 6: 1450, 7: 2800},
}


def imoveis_de_hoje(totais=DIAS[HOJE]):
    """Os imóveis do dia como o dashboard os recebe de carregar_imoveis (só as colunas usadas aqui)."""
    return pd.DataFrame({"fonte": "cardinali", "codigo": list(totais), "total_mensal": list(totais.values()),
                         "coletado_em": HOJE}, index=[10 * codigo for codigo in totais])


@pytest.fixture
def historico_completo(tmp_path):
    return ler_historico(salvar_dias(tmp_path / "snapshots", DIAS, tmp_path))


def novidades_por_codigo(df):
    return {"novos": sorted(df.loc[df["novo"], "codigo"]),
            "baixaram": df.dropna(subset=["total_anterior"]).set_index("codigo")["total_anterior"].to_dict()}


# --- download e leitura -------------------------------------------------------------------

def tar_gz(arquivos: dict[str, bytes]) -> io.BytesIO:
    memoria = io.BytesIO()
    with tarfile.open(fileobj=memoria, mode="w:gz") as tar:
        for nome, conteudo in arquivos.items():
            info = tarfile.TarInfo(nome)
            info.size = len(conteudo)
            tar.addfile(info, io.BytesIO(conteudo))
    memoria.seek(0)
    return memoria


def test_extrair_snapshots_so_extrai_os_parquet_dos_snapshots(tmp_path):
    destino = tmp_path / "destino"
    arquivo = tar_gz({
        "repo-data/snapshots/2026/2026-01-02.parquet": b"dia 2",
        "repo-data/README.md": b"outro arquivo",
        "repo-data/snapshots/2026/../../../../fora.parquet": b"tentativa de sair da pasta",
        "../fora.parquet": b"idem",
    })
    assert extrair_snapshots(arquivo, destino) == 1
    assert [p.relative_to(destino).as_posix() for p in destino.rglob("*") if p.is_file()] == [
        "2026/2026-01-02.parquet"]
    assert not (tmp_path / "fora.parquet").exists()


def test_ler_historico(historico_completo):
    assert (historico_completo.primeiro_dia, historico_completo.ultimo_dia) == (pd.Timestamp(2026, 9, 1),
                                                                                 pd.Timestamp(HOJE))
    imovel_1 = historico_completo.por_imovel.set_index("codigo").loc[1]
    assert (imovel_1["data_mudanca"], imovel_1["total_anterior"], imovel_1["total_novo"]) == (
        pd.Timestamp(2026, 10, 18), 1000.0, 900.0)
    # O semanal passa pelas mesmas regras do CSV do dia: tem as métricas e a região universitária
    semanal = historico_completo.semanal
    assert {"custo_por_dormitorio", "regiao_universitaria", "reservado"} <= set(semanal.columns)
    assert semanal["dormitorios"].dtype == "float64"


def test_baixar_historico_de_um_tar_gz(tmp_path):
    """O caminho completo: o .tar.gz (aqui um arquivo local, em vez do GitHub) até o Historico."""
    pasta = salvar_dias(tmp_path / "branch" / "snapshots", DIAS, tmp_path)
    arquivo = tmp_path / "data.tar.gz"
    with tarfile.open(arquivo, "w:gz") as tar:
        tar.add(pasta, arcname="imobiliario_universitario-data/snapshots")
    historico = baixar_historico(arquivo.as_uri())
    assert historico.ultimo_dia == pd.Timestamp(HOJE)
    assert len(historico.por_imovel) == 7


# --- novidades ----------------------------------------------------------------------------

def test_marcar_novidades(historico_completo):
    imoveis = imoveis_de_hoje()
    marcados = marcar_novidades(imoveis, historico_completo)
    assert novidades_por_codigo(marcados) == {"novos": [4, 5], "baixaram": {1: 1000.0}}
    assert sorted(marcados.loc[marcados["novidade"], "codigo"]) == [1, 4, 5]
    assert marcados.index.equals(imoveis.index)  # as colunas novas se alinham com as linhas certas


def test_marcar_novidades_com_historico_de_ontem(tmp_path):
    """O cache ainda guarda o histórico de antes da coleta de hoje: o CSV completa o que falta."""
    dias_ate_ontem = {dia: totais for dia, totais in DIAS.items() if dia < HOJE}
    historico = ler_historico(salvar_dias(tmp_path / "snapshots", dias_ate_ontem, tmp_path))
    hoje = {**DIAS[HOJE], 2: 1800}  # o imóvel 2 baixou hoje, e o histórico ainda não sabe
    assert novidades_por_codigo(marcar_novidades(imoveis_de_hoje(hoje), historico)) == {
        "novos": [4, 5], "baixaram": {1: 1000.0, 2: 2000.0}}


def test_marcar_novidades_sem_historico():
    marcados = marcar_novidades(imoveis_de_hoje(), None)
    assert not marcados["novo"].any() and not marcados["novidade"].any()
    assert marcados["total_anterior"].isna().all()


# --- tendência ----------------------------------------------------------------------------

def test_tendencia_semanal():
    semana_1, semana_2 = pd.Timestamp(2026, 10, 5), pd.Timestamp(2026, 10, 12)
    linhas = ([(semana_1, "Centro", valor) for valor in (1000, 1200, 1400)]
              + [(semana_1, "Jardim Paraíso", valor) for valor in (800, 850, 900)]
              + [(semana_2, "Centro", valor) for valor in (1100, 1300)]      # só 2: fica fora da série do Centro
              + [(semana_2, "Jardim Paraíso", valor) for valor in (700, None, 900, 1000)])  # sem dado não conta
    semanal = pd.DataFrame(linhas, columns=["semana", "bairro", "custo_por_dormitorio"])

    tendencia = tendencia_semanal(semanal, "custo_por_dormitorio", "Região", bairro="Centro")
    assert tendencia.values.tolist() == [
        [semana_1, "Região", 950.0, 6],
        [semana_2, "Região", 1000.0, 5],
        [semana_1, "Centro", 1200.0, 3],
    ]
    assert set(tendencia_semanal(semanal, "custo_por_dormitorio", "Região")["serie"]) == {"Região"}
