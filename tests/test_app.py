"""Testes da leitura de dados do dashboard (usam o dados/geo/bairros.geojson do repositório)."""
import csv

import pytest

from app.bairros import UFSCAR, USP, Buscar_contorno, Buscar_coords, Distancia_km, Na_regiao_universitaria, Nome_padrao
from app.dados import Carregar_imoveis
from scraper.modelo import COLUNAS


def test_nome_padrao_junta_grafias_do_mesmo_bairro():
    assert Nome_padrao("Jardim Paraiso") == Nome_padrao("Jardim Paraíso") == "Jardim Paraíso"
    assert Nome_padrao("Jardim Hikari") == "Jardim Hikare"                    # pela tabela de aliases
    assert Nome_padrao("Parque Arnold Schimidt") == "Parque Arnold Schmidt"   # idem
    assert Nome_padrao("Bairro Que Não Existe") == "Bairro Que Não Existe"
    # Bairro ainda sem contorno: as grafias também se juntam pelo nome da tabela
    assert Nome_padrao("Loteamento Habitacional Sao Carlos I") == "Loteamento Habitacional São Carlos I"


def test_contorno_e_coordenadas():
    assert Buscar_contorno("Centro")["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert Buscar_coords("Jardim Paraíso") == Buscar_coords("jardim paraiso") is not None
    assert Buscar_coords("Bairro Que Não Existe") is None


def test_distancia_entre_usp_e_ufscar():
    assert Distancia_km(USP, UFSCAR) == pytest.approx(3.2, abs=0.1)


def test_regiao_universitaria():
    assert Na_regiao_universitaria("Centro")
    assert Na_regiao_universitaria("Parque Arnold Schmidt")
    assert Na_regiao_universitaria("Vila Prado")                  # a borda chega a ~2,2 km da USP
    assert not Na_regiao_universitaria("Swiss Park Residencial")  # a borda fica a ~2,7 km
    assert not Na_regiao_universitaria("Bairro Que Não Existe")


@pytest.fixture
def csv_de_exemplo(tmp_path):
    linhas = [
        {"codigo": 1, "bairro": "Centro", "subtipo": "Padrão", "total_mensal": 2000, "dormitorios": 2},
        {"codigo": 2, "bairro": "Jardim Paraíso", "subtipo": "Kitchnet sem Condomínio", "total_mensal": 1060},
        {"codigo": 3, "bairro": "Swiss Park", "subtipo": "Padrão", "total_mensal": 1500, "dormitorios": 1},
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


def test_carregar_imoveis_da_regiao_universitaria(csv_de_exemplo):
    df = Carregar_imoveis(csv_de_exemplo)
    # 3: bairro fora da região; 4: sem total ("Consulte-nos"); 5: acima de R$ 8000
    assert sorted(df["codigo"]) == [1, 2, 6]
    assert {"Bairro", "Total / Mês", "Dormitórios", "Link"} <= set(df.columns)
    por_codigo = df.set_index("codigo")
    # Kitnet sem dormitório informado conta como 1
    assert por_codigo.loc[2, "Dormitórios"] == 1
    # Grafias diferentes do mesmo bairro viram um nome só (uma área só no mapa)
    assert por_codigo.loc[2, "Bairro"] == por_codigo.loc[6, "Bairro"] == "Jardim Paraíso"


def test_carregar_imoveis_da_cidade_toda(csv_de_exemplo):
    df = Carregar_imoveis(csv_de_exemplo, so_regiao_universitaria=False)
    assert sorted(df["codigo"]) == [1, 2, 3, 6]
    assert df.set_index("codigo").loc[3, "Bairro"] == "Swiss Park Residencial"
