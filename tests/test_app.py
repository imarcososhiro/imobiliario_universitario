"""Testes da leitura de dados do dashboard."""
import csv

import pytest

from app.coord_bairros import Buscar_coords
from app.dados import Carregar_imoveis
from scraper.modelo import COLUNAS


def test_buscar_coords_ignora_acentos_e_pontuacao():
    assert Buscar_coords("Jardim Paraíso") == Buscar_coords("Jardim Paraiso") is not None
    assert Buscar_coords("Vila Monteiro (Gleba I)") == Buscar_coords("Vila Monteiro Gleba I") is not None
    assert Buscar_coords("Bairro Que Não Existe") is None


@pytest.fixture
def csv_de_exemplo(tmp_path):
    linhas = [
        {"codigo": 1, "bairro": "Centro", "subtipo": "Padrão", "total_mensal": 2000, "dormitorios": 2},
        {"codigo": 2, "bairro": "Jardim Paraíso", "subtipo": "Kitchnet sem Condomínio", "total_mensal": 1060},
        {"codigo": 3, "bairro": "Vila Jacobucci", "subtipo": "Padrão", "total_mensal": 1500, "dormitorios": 1},
        {"codigo": 4, "bairro": "Centro", "subtipo": "Padrão", "total_mensal": None, "dormitorios": 3},
        {"codigo": 5, "bairro": "Centro", "subtipo": "Padrão", "total_mensal": 9500, "dormitorios": 4},
        {"codigo": 6, "bairro": "Jardim Paraiso", "subtipo": "Padrão", "total_mensal": 1800, "dormitorios": 2},
    ]
    caminho = tmp_path / "imoveis.csv"
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, restval="")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({"fonte": "cardinali", "tipo": "Apartamento", **linha})
    return caminho


def test_carregar_imoveis(csv_de_exemplo):
    df = Carregar_imoveis(csv_de_exemplo)
    # 3: bairro fora da região; 4: sem total ("Consulte-nos"); 5: acima de R$ 8000
    assert sorted(df["codigo"]) == [1, 2, 6]
    assert {"Bairro", "Total / Mês", "Dormitórios", "Link"} <= set(df.columns)
    por_codigo = df.set_index("codigo")
    # Kitnet sem dormitório informado conta como 1
    assert por_codigo.loc[2, "Dormitórios"] == 1
    # Grafias diferentes do mesmo bairro viram um nome só (um círculo só no mapa)
    assert por_codigo.loc[2, "Bairro"] == por_codigo.loc[6, "Bairro"] == "Jardim Paraíso"
