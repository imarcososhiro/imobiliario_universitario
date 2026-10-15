"""Testes da leitura de dados do dashboard (usam o dados/geo/bairros.geojson do repositório)."""
import csv

import pytest

from app.bairros import (UFSCAR, USP, buscar_contorno, buscar_coords, distancia_km, na_regiao_universitaria,
                         padronizar_bairro)
from app.dados import Filtros, aplicar_filtros, carregar_imoveis
from scraper.modelo import COLUNAS


def test_padronizar_bairro_junta_grafias_do_mesmo_bairro():
    assert padronizar_bairro("Jardim Paraiso") == padronizar_bairro("Jardim Paraíso") == "Jardim Paraíso"
    assert padronizar_bairro("Jardim Hikari") == "Jardim Hikare"                    # pela tabela de aliases
    assert padronizar_bairro("Parque Arnold Schimidt") == "Parque Arnold Schmidt"   # idem
    assert padronizar_bairro("Bairro Que Não Existe") == "Bairro Que Não Existe"
    # Bairro sem contorno também junta as grafias pelo nome da tabela
    assert padronizar_bairro("Vila Monteiro (Gleba I)") == padronizar_bairro("Vila Monteiro Gleba I")


def test_contorno_e_coordenadas():
    assert buscar_contorno("Centro")["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert buscar_coords("Jardim Paraíso") == buscar_coords("jardim paraiso") is not None
    assert buscar_coords("Bairro Que Não Existe") is None


def test_distancia_entre_usp_e_ufscar():
    assert distancia_km(USP, UFSCAR) == pytest.approx(3.2, abs=0.1)


def test_regiao_universitaria():
    assert na_regiao_universitaria("Centro")
    assert na_regiao_universitaria("Parque Arnold Schmidt")
    assert na_regiao_universitaria("Vila Prado")                  # a borda chega a ~2,2 km da USP
    assert not na_regiao_universitaria("Swiss Park Residencial")  # a borda fica a ~2,7 km
    assert not na_regiao_universitaria("Bairro Que Não Existe")


@pytest.fixture
def csv_de_exemplo(tmp_path):
    padrao = {"fonte": "cardinali", "tipo": "Apartamento", "subtipo": "Padrão", "finalidade": "Residencial",
              "situacao": "DISPONÍVEL", "dormitorios": 2, "coletado_em": "2026-10-15"}
    linhas = [
        {"codigo": 1, "bairro": "Centro", "total_mensal": 2000},
        {"codigo": 2, "bairro": "Jardim Paraíso", "subtipo": "Kitchnet sem Condomínio", "total_mensal": 1060,
         "dormitorios": ""},
        {"codigo": 3, "bairro": "Swiss Park", "total_mensal": 1500, "tipo": "Casa"},
        {"codigo": 4, "bairro": "Centro", "total_mensal": ""},                    # "Consulte-nos"
        {"codigo": 5, "bairro": "Centro", "total_mensal": 9500},                  # acima de R$ 8000
        {"codigo": 6, "bairro": "Jardim Paraiso", "total_mensal": 1800, "dormitorios": 5},
        {"codigo": 7, "bairro": "Centro", "total_mensal": 3000, "finalidade": "Comercial"},
        {"codigo": 8, "bairro": "Centro", "total_mensal": 2500, "situacao": "RESERVADO"},
    ]
    caminho = tmp_path / "imoveis.csv"
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, restval="")
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({**padrao, **linha})
    return caminho


def test_carregar_imoveis(csv_de_exemplo):
    df = carregar_imoveis(csv_de_exemplo).set_index("codigo")
    # 4: sem total; 5: acima de R$ 8000; 7: só comercial
    assert sorted(df.index) == [1, 2, 3, 6, 8]
    assert df.loc[2, "dormitorios"] == 1                      # kitnet sem dormitório informado
    assert df.loc[2, "bairro"] == df.loc[6, "bairro"] == "Jardim Paraíso"
    assert df.loc[3, "bairro"] == "Swiss Park Residencial"
    assert df["regiao_universitaria"].to_dict() == {1: True, 2: True, 3: False, 6: True, 8: True}
    assert df["reservado"].to_dict() == {1: False, 2: False, 3: False, 6: False, 8: True}
    assert df.loc[1, "custo_por_dormitorio"] == 1000


def test_aplicar_filtros(csv_de_exemplo):
    df = carregar_imoveis(csv_de_exemplo)

    def codigos(**filtros):
        return sorted(aplicar_filtros(df, Filtros(**filtros))["codigo"])

    assert codigos() == [1, 2, 6]                                   # região universitária, sem reservados
    assert codigos(so_regiao_universitaria=False) == [1, 2, 3, 6]
    assert codigos(incluir_reservados=True) == [1, 2, 6, 8]
    assert codigos(so_regiao_universitaria=False, tipo="Casa") == [3]
    assert codigos(dormitorios=[1]) == [2]
    assert codigos(dormitorios=[4]) == [6]                          # "4+" inclui 5 dormitórios
    assert codigos(faixa_total=(1000, 1900)) == [2, 6]
