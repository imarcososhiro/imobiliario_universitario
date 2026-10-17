"""Testes de fumaça: a página do Streamlit roda do começo ao fim, sem navegador.

Usam o dados/imoveis.csv do repositório e um histórico sintético feito a partir dele.
Pegam erros que só aparecem com a página inteira montada (como um módulo do app
chamando uma função que não existe mais).
"""
import re
import tarfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dados import CAMINHO_CSV, Filtros, aplicar_filtros, carregar_imoveis
from app.historico import DIAS_NOVIDADE, VARIAVEL_URL
from app.metricas import COLUNAS_DISTANCIA
from historico.consultas import INICIO_CIDADE_TODA
from historico.snapshot import salvar_snapshot

RAIZ = Path(__file__).resolve().parent.parent


def abrir(pagina: str) -> AppTest:
    return AppTest.from_file(str(RAIZ / pagina), default_timeout=60).run()


@pytest.fixture(scope="module")
def url_historico(tmp_path_factory):
    """Um .tar.gz como o do branch `data`, com dois dias feitos a partir do CSV do repositório.

    Há um mês, três imóveis a até 3 km da USP (o que a página mostra ao abrir) ainda não existiam
    e um quarto custava R$ 100 a mais; num dia da última semana, tudo já estava como hoje. Então,
    para o painel, há 3 imóveis novos e 1 que baixou de preço.
    """
    pasta = tmp_path_factory.mktemp("historico")
    csv = pd.read_csv(CAMINHO_CSV, dtype=str, keep_default_na=False)  # texto: grava de volta igualzinho
    hoje = date.fromisoformat(csv["coletado_em"].iloc[0])
    perto = aplicar_filtros(carregar_imoveis(), Filtros(perto_de="USP", distancia_max_km=3.0))
    codigos = perto["codigo"].astype(str).tolist()
    novos, baixou = codigos[:3], codigos[3]

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


def cartoes(at: AppTest) -> str:
    """O HTML de todos os cartões dos imóveis (um st.markdown por cartão)."""
    return "".join(markdown.value for markdown in at.markdown if 'class="cartao"' in markdown.value)


def numeros(at: AppTest) -> dict[str, str]:
    """Os números do topo da página: rótulo -> valor."""
    grade = next(bloco.proto.body for bloco in at.get("html") if 'class="numeros"' in bloco.proto.body)
    return dict((rotulo, valor) for valor, rotulo in re.findall(r"<b>(.*?)</b><span>(.*?)</span>", grade))


def test_pagina_principal():
    at = abrir("Home.py")
    assert not at.exception
    assert list(numeros(at)) == ["imóveis pra você", "preço típico por quarto", "novos esta semana",
                                 "baixaram de preço"]
    assert int(numeros(at)["imóveis pra você"].replace(".", "")) > 0
    assert at.selectbox(key="bairro").value is None  # nenhum bairro escolhido: mostra todos
    assert cartoes(at).count('class="cartao"') == 12


@pytest.mark.parametrize("mudar", [
    lambda at: at.radio(key="campus").set_value("UFSCar"),
    lambda at: at.radio(key="campus").set_value("UFSCar").run().radio(key="perto_da_ufscar").set_value("UFSCar"),
    lambda at: at.select_slider(key="distancia").set_value("Qualquer distância"),
    lambda at: at.radio(key="tipo").set_value("Casa"),
    lambda at: at.button_group(key="quartos").set_value([2, 3]),
    lambda at: at.select_slider(key="preco").set_value(1000),
    lambda at: at.selectbox(key="ordem").set_value("Mais perto"),
    lambda at: at.selectbox(key="bairro").set_value("Centro"),
    lambda at: at.button_group(key="imobiliarias").set_value(["cardinali"]),
], ids=["campus", "perto_da_ufscar", "distancia", "tipo", "quartos", "preco", "ordem", "bairro", "imobiliaria"])
def test_pagina_principal_com_filtros(mudar):
    at = abrir("Home.py")
    mudar(at)
    at.run()
    assert not at.exception
    assert 'class="cartao"' in cartoes(at)


def rolagens(at: AppTest) -> list[str]:
    """O HTML dos scripts de rolagem da página (cada um vira um iframe invisível)."""
    return [iframe.proto.srcdoc for iframe in at.get("iframe")]


def test_rolagem_pedida_acontece_uma_vez():
    # É o que um clique num bairro do mapa pede (o AppTest não consegue clicar dentro do mapa)
    at = abrir("Home.py")
    assert rolagens(at) == []  # ao abrir, a página não rola sozinha
    at.session_state["rolar_ate"] = "imoveis"
    at.run()
    assert len(rolagens(at)) == 1 and 'getElementById("imoveis")' in rolagens(at)[0]
    at.run()
    assert rolagens(at) == []  # na próxima vez que a página roda, não rola de novo


def test_ufscar_comeca_pela_rodoviaria():
    at = abrir("Home.py")
    assert [radio.key for radio in at.radio] == ["campus", "tipo"]  # na USP, não há a pergunta da rodoviária
    at.radio(key="campus").set_value("UFSCar").run()
    assert at.radio(key="perto_da_ufscar").value == "Rodoviária"
    assert at.select_slider(key="distancia").label == "Quão perto da rodoviária?"
    assert "km da rodoviária" in cartoes(at)

    at.radio(key="perto_da_ufscar").set_value("UFSCar").run()
    assert at.select_slider(key="distancia").label == "Quão perto da UFSCar?"
    assert "km da UFSCar" in cartoes(at)


def test_ver_no_mapa():
    at = abrir("Home.py")
    botao = next(botao for botao in at.button if botao.key.startswith("ver-no-mapa-"))
    botao.click().run()
    assert not at.exception
    assert f"{at.session_state['destaque']} ·" in cartoes(at)  # o bairro do primeiro cartão
    assert len(rolagens(at)) == 1 and 'getElementById("mapa")' in rolagens(at)[0]

    at.selectbox(key="ordem").set_value("Mais perto").run()
    assert rolagens(at) == []  # mudar outra coisa não rola a página de novo


def test_mostrar_mais():
    at = abrir("Home.py")
    at.button(key="mostrar_mais").click().run()
    assert not at.exception
    assert cartoes(at).count('class="cartao"') == 24


def test_pagina_principal_mostra_novidades():
    at = abrir("Home.py")
    assert (numeros(at)["novos esta semana"], numeros(at)["baixaram de preço"]) == ("3", "1")

    at.selectbox(key="ordem").set_value("Novidades primeiro").run()
    grade = cartoes(at)
    assert grade.count('class="selo novo"') == 3
    assert grade.count('class="selo queda"') == 1
    assert grade.count("<s>") == 1  # o preço de antes, riscado


def test_pagina_funciona_sem_historico(monkeypatch, tmp_path):
    monkeypatch.setenv(VARIAVEL_URL, (tmp_path / "nao_existe.tar.gz").as_uri())
    at = abrir("Home.py")
    assert not at.exception
    assert any("não pôde ser carregado" in caption.value for caption in at.caption)
    assert list(numeros(at)) == ["imóveis pra você", "preço típico por quarto"]
    assert "selo novo" not in cartoes(at) and "selo queda" not in cartoes(at)


def test_pagina_principal_sem_resultados_mostra_aviso(monkeypatch):
    # Todos os imóveis a 10 km de tudo: com a distância de quando a página abre (até 3 km), nenhum
    # aparece. (Não dá para usar um filtro "impossível" com o CSV real: ele muda todo dia.)
    longe = carregar_imoveis().assign(**{coluna: 10.0 for coluna in COLUNAS_DISTANCIA.values()})
    monkeypatch.setattr("app.dados.carregar_imoveis", lambda: longe)
    at = abrir("Home.py")
    assert not at.exception
    assert "Nenhum imóvel" in at.info[0].value
