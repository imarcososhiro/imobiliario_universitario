"""Testes de fumaça: as páginas do Streamlit rodam do começo ao fim, sem navegador.

Usam o dados/imoveis.csv do repositório e um histórico sintético feito a partir dele.
Pegam erros que só aparecem com a página inteira montada (como um módulo do app
chamando uma função que não existe mais).
"""
import tarfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dados import CAMINHO_CSV, Filtros, aplicar_filtros, carregar_imoveis
from app.historico import DIAS_NOVIDADE, VARIAVEL_URL
from historico.consultas import INICIO_CIDADE_TODA
from historico.snapshot import salvar_snapshot

RAIZ = Path(__file__).resolve().parent.parent


def abrir(pagina: str) -> AppTest:
    return AppTest.from_file(str(RAIZ / pagina), default_timeout=60).run()


@pytest.fixture(scope="module")
def url_historico(tmp_path_factory):
    """Um .tar.gz como o do branch `data`, com dois dias feitos a partir do CSV do repositório.

    Há um mês, três imóveis da região universitária ainda não existiam e um quarto custava
    R$ 100 a mais; num dia da última semana, tudo já estava como hoje. Então, para o painel,
    há 3 imóveis novos e 1 que baixou de preço.
    """
    pasta = tmp_path_factory.mktemp("historico")
    csv = pd.read_csv(CAMINHO_CSV, dtype=str, keep_default_na=False)  # texto: grava de volta igualzinho
    hoje = date.fromisoformat(csv["coletado_em"].iloc[0])
    regiao = aplicar_filtros(carregar_imoveis(), Filtros())["codigo"].astype(str).tolist()
    novos, baixou = regiao[:3], regiao[3]

    mes_passado = csv[~csv["codigo"].isin(novos)].copy()
    linha = mes_passado["codigo"] == baixou
    mes_passado.loc[linha, "total_mensal"] = str(float(mes_passado.loc[linha, "total_mensal"].iloc[0]) + 100)
    # Um dia da última semana que não seja o da mudança de cobertura (nele, ninguém conta como novo)
    recente = next(dia for dia in (hoje - timedelta(days=n) for n in range(DIAS_NOVIDADE))
                   if dia != INICIO_CIDADE_TODA)
    for dia, tabela in ((hoje - timedelta(days=30), mes_passado), (recente, csv)):
        tabela.assign(coletado_em=dia.isoformat()).to_csv(pasta / "coleta.csv", index=False)
        salvar_snapshot(pasta / "coleta.csv", pasta / "snapshots")

    arquivo = pasta / "data.tar.gz"
    with tarfile.open(arquivo, "w:gz") as tar:
        tar.add(pasta / "snapshots", arcname="imobiliario_universitario-data/snapshots")
    return arquivo.as_uri()


@pytest.fixture(autouse=True)
def com_historico(monkeypatch, url_historico):
    monkeypatch.setenv(VARIAVEL_URL, url_historico)


def test_pagina_principal():
    at = abrir("Home.py")
    assert not at.exception
    assert [metrica.label for metrica in at.metric] == [
        "Imóveis encontrados", "Aluguel total (mediana)", "Por dormitório (mediana)", "Preço por m² (mediana)"]
    assert int(at.metric[0].value.replace(".", "")) > 0


@pytest.mark.parametrize("mudar", [
    lambda at: at.sidebar.radio(key="area").set_value("Cidade toda"),
    lambda at: at.sidebar.radio(key="campus").set_value("UFSCar"),
    lambda at: at.sidebar.radio(key="tipo").set_value("Casa"),
    lambda at: at.sidebar.toggle(key="reservados").set_value(True),
    lambda at: at.sidebar.select_slider(key="peso_distancia_km").set_value("Muito"),
    lambda at: at.radio(key="metrica_mapa").set_value("custo_por_dormitorio"),
    lambda at: at.selectbox(key="ordem").set_value("Mais perto do campus"),
    lambda at: at.selectbox(key="bairro").set_value("Centro"),
], ids=["cidade toda", "campus", "tipo", "reservados", "peso", "metrica do mapa", "ordem", "bairro"])
def test_pagina_principal_com_filtros(mudar):
    at = abrir("Home.py")
    mudar(at)
    at.run()
    assert not at.exception


def test_pagina_principal_mostra_novidades():
    at = abrir("Home.py")
    linha = next(markdown.value for markdown in at.markdown if "esta semana" in markdown.value)
    assert "**3 imóveis novos** esta semana · 1 baixou de preço" in linha

    at.selectbox(key="ordem").set_value("Novidades primeiro").run()
    textos = [markdown.value for markdown in at.markdown]
    assert sum("Novo]" in texto for texto in textos) == 3            # o selo dos cartões
    assert sum("Baixou de preço]" in texto for texto in textos) == 1
    assert sum("~~" in texto for texto in textos) == 1                # o preço de antes, riscado


def test_paginas_funcionam_sem_historico(monkeypatch, tmp_path):
    monkeypatch.setenv(VARIAVEL_URL, (tmp_path / "nao_existe.tar.gz").as_uri())
    at = abrir("Home.py")
    assert not at.exception
    assert any("não pôde ser carregado" in caption.value for caption in at.caption)
    assert not any("Novo]" in markdown.value for markdown in at.markdown)


def test_pagina_principal_sem_resultados_mostra_aviso():
    at = abrir("Home.py")
    minimo = at.sidebar.slider(key="faixa").min
    at.sidebar.slider(key="faixa").set_value((minimo, minimo + 1)).run()
    assert not at.exception
    assert "Nenhum imóvel" in at.info[0].value


def test_pagina_de_graficos():
    at = abrir("pages/Gráficos.py")
    assert not at.exception
    at.selectbox(key="destaque_grafico").set_value("Centro").run()
    assert not at.exception

