"""Testes das métricas de custo-benefício."""
import math

import pandas as pd
import pytest

from app.bairros import UFSCAR, USP, buscar_coords, distancia_km
from app.metricas import (adicionar_metricas, escolher_campus, indice_custo_beneficio, notas_por_criterio,
                          resumo_por_bairro)


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
    assert df["preco_m2"].iloc[0] == 40.0


def test_distancia_do_bairro_a_cada_campus():
    df = adicionar_metricas(imoveis(bairro=["Centro", "Bairro Que Não Existe"]))
    centro = buscar_coords("Centro")
    assert df["distancia_usp_km"].iloc[0] == pytest.approx(distancia_km(centro, USP))
    assert df["distancia_ufscar_km"].iloc[0] == pytest.approx(distancia_km(centro, UFSCAR))
    assert math.isnan(df["distancia_usp_km"].iloc[1])


def test_escolher_campus():
    df = pd.DataFrame({"distancia_usp_km": [1.0, 3.0], "distancia_ufscar_km": [2.0, 0.5]})
    assert escolher_campus(df, "USP")["distancia_km"].tolist() == [1.0, 3.0]
    assert escolher_campus(df, "UFSCar")["distancia_km"].tolist() == [2.0, 0.5]
    assert escolher_campus(df, "Tanto faz")["distancia_km"].tolist() == [1.0, 0.5]  # o mais perto


def tres_imoveis():
    return pd.DataFrame({
        "custo_por_dormitorio": [500.0, 1000.0, 1500.0],
        "preco_m2": [20.0, 30.0, 40.0],
        "distancia_km": [3.0, 2.0, 1.0],
    })


def test_notas_vao_de_1_no_melhor_a_0_no_pior():
    notas = notas_por_criterio(tres_imoveis())
    assert notas["custo_por_dormitorio"].tolist() == [1.0, 0.5, 0.0]
    assert notas["distancia_km"].tolist() == [0.0, 0.5, 1.0]


def test_indice_com_pesos_iguais_e_diferentes():
    df = tres_imoveis()
    assert indice_custo_beneficio(df).tolist() == [67.0, 50.0, 33.0]
    so_distancia = {"custo_por_dormitorio": 0, "preco_m2": 0, "distancia_km": 1}
    assert indice_custo_beneficio(df, so_distancia).tolist() == [0.0, 50.0, 100.0]
    # Todos os pesos zerados não faz sentido: volta para pesos iguais
    assert indice_custo_beneficio(df, dict.fromkeys(so_distancia, 0)).tolist() == [67.0, 50.0, 33.0]


def test_indice_ignora_criterio_sem_dado():
    df = tres_imoveis()
    df.loc[0, "preco_m2"] = None
    indice = indice_custo_beneficio(df)
    # O 1º imóvel é avaliado só por custo por dormitório (nota 1) e distância (nota 0)
    assert indice.iloc[0] == 50.0


def test_indice_com_um_imovel_so():
    assert indice_custo_beneficio(tres_imoveis().head(1)).tolist() == [100.0]


def test_resumo_por_bairro_usa_mediana():
    df = pd.DataFrame({
        "bairro": ["Centro", "Centro", "Centro", "Vila Prado"],
        "total_mensal": [1000.0, 1100.0, 9000.0, 2000.0],
        "custo_por_dormitorio": [1000.0, 550.0, 3000.0, 1000.0],
        "preco_m2": [20.0, 25.0, 90.0, None],
        "distancia_km": [1.2, 1.2, 1.2, 2.0],
        "indice": [80.0, 90.0, 10.0, 50.0],
    })
    resumo = resumo_por_bairro(df).set_index("bairro")
    assert resumo.loc["Centro", "imoveis"] == 3
    assert resumo.loc["Centro", "total_mensal"] == 1100.0  # a média seria 3.700, puxada pelo anúncio de R$ 9.000
    assert resumo.loc["Centro", ["minimo", "maximo"]].tolist() == [1000.0, 9000.0]
    assert math.isnan(resumo.loc["Vila Prado", "preco_m2"])
