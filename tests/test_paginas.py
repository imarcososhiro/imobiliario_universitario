"""Testes de fumaça: as páginas do Streamlit rodam do começo ao fim, sem navegador.

Usam o dados/imoveis.csv do repositório. Pegam erros que só aparecem com a página
inteira montada (como um módulo do app chamando uma função que não existe mais).
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent


def abrir(pagina: str) -> AppTest:
    return AppTest.from_file(str(RAIZ / pagina), default_timeout=60).run()


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
