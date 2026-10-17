"""Testes das métricas: preço por quarto, área, distância e o resumo por bairro."""
import math

import pandas as pd
import pytest

from app.bairros import RODOVIARIA, UFSCAR, USP, buscar_coords, distancia_km
from app.metricas import adicionar_metricas, medir_distancia, resumo_por_bairro


def imoveis(**colunas):
    base = {"bairro": "Centro", "total_mensal": 2000.0, "dormitorios": 2.0,
            "area_util_m2": 50.0, "area_construida_m2": None}
    quantidade = max(len(valor) for valor in colunas.values() if isinstance(valor, list))
    return pd.DataFrame({nome: colunas.get(nome, [valor] * quantidade) for nome, valor in base.items()})


def test_custo_por_dormitorio_e_preco_por_m2():
    df = adicionar_metricas(imoveis(total_mensal=[2000.0, 1500.0, 900.0], dormitorios=[2.0, 0.0, None],
                                    area_util_m2=[50.0, None, 3.0], area_construida_m2=[None, 120.0, None]))
    assert df["custo_por_dormitorio"].tolist()[0] == 1000.0
    assert df["custo_por_dormitorio"].isna().tolist()[1:] == [True, True]  # 0 ou sem dormitórios
    assert df["area_m2"].tolist()[:2] == [50.0, 120.0]  # sem área útil, usa a construída
    assert math.isnan(df["area_m2"].iloc[2])             # 3 m² é erro de cadastro


def test_distancia_do_bairro_a_cada_lugar():
    df = adicionar_metricas(imoveis(bairro=["Centro", "Bairro Que Não Existe"]))
    centro = buscar_coords("Centro")
    assert df["distancia_usp_km"].iloc[0] == pytest.approx(distancia_km(centro, USP))
    assert df["distancia_ufscar_km"].iloc[0] == pytest.approx(distancia_km(centro, UFSCAR))
    assert df["distancia_rodoviaria_km"].iloc[0] == pytest.approx(distancia_km(centro, RODOVIARIA))
    assert math.isnan(df["distancia_usp_km"].iloc[1])


def test_medir_distancia():
    df = pd.DataFrame({"distancia_usp_km": [1.0, 3.0], "distancia_ufscar_km": [2.0, 0.5],
                       "distancia_rodoviaria_km": [0.4, 2.5]})
    assert medir_distancia(df, "USP")["distancia_km"].tolist() == [1.0, 3.0]
    assert medir_distancia(df, "UFSCar")["distancia_km"].tolist() == [2.0, 0.5]
    assert medir_distancia(df, "Rodoviária")["distancia_km"].tolist() == [0.4, 2.5]


def test_resumo_por_bairro_usa_mediana():
    df = pd.DataFrame({
        "bairro": ["Centro", "Centro", "Centro", "Vila Prado"],
        "total_mensal": [1000.0, 1100.0, 9000.0, 2000.0],
        "custo_por_dormitorio": [1000.0, 550.0, 3000.0, None],
        "distancia_km": [1.2, 1.2, 1.2, 2.0],
    })
    resumo = resumo_por_bairro(df).set_index("bairro")
    assert resumo.loc["Centro", "imoveis"] == 3
    assert resumo.loc["Centro", "total_mensal"] == 1100.0  # a média seria 3.700, puxada pelo anúncio de R$ 9.000
    assert resumo.loc["Centro", ["custo_por_dormitorio", "mais_barato"]].tolist() == [1000.0, 550.0]
    assert resumo.loc["Vila Prado", "distancia_km"] == 2.0
    assert math.isnan(resumo.loc["Vila Prado", "custo_por_dormitorio"])  # sem nº de quartos
