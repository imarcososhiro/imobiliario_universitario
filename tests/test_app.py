"""Testes da leitura de dados do dashboard (usam o dados/geo/bairros.geojson do repositório)."""
import csv

import pandas as pd
import pytest

from app.bairros import RODOVIARIA, UFSCAR, USP, buscar_contorno, buscar_coords, distancia_km, padronizar_bairro
from app.dados import Filtros, aplicar_filtros, carregar_imoveis, marcar_duplicatas
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
    assert distancia_km(USP, RODOVIARIA) == pytest.approx(0.8, abs=0.1)  # a rodoviária fica no centro


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
    # 4: sem total; 5: acima de R$ 8000; 7: só comercial; 8: reservado
    assert sorted(df.index) == [1, 2, 3, 6]
    assert df.loc[2, "dormitorios"] == 1                      # kitnet sem dormitório informado
    assert df.loc[2, "bairro"] == df.loc[6, "bairro"] == "Jardim Paraíso"
    assert df.loc[3, "bairro"] == "Swiss Park Residencial"
    assert df.loc[1, "custo_por_dormitorio"] == 1000


def test_aplicar_filtros(csv_de_exemplo):
    df = carregar_imoveis(csv_de_exemplo)

    def codigos(**filtros):
        return sorted(aplicar_filtros(df, Filtros(**filtros))["codigo"])

    assert codigos() == [1, 2, 3, 6]
    # Distâncias até a USP: Jardim Paraíso ~0,6 km, Centro ~1,3 km, Swiss Park ~2,9 km
    assert codigos(distancia_max_km=1) == [2, 6]
    assert codigos(distancia_max_km=2) == [1, 2, 6]
    # A UFSCar fica do outro lado da cidade: o Swiss Park está a ~5,9 km dela
    assert codigos(distancia_max_km=5) == [1, 2, 3, 6]
    assert codigos(perto_de="UFSCar", distancia_max_km=5) == [1, 2, 6]
    assert codigos(tipo="Casa") == [3]
    assert codigos(dormitorios=[1]) == [2]
    assert codigos(dormitorios=[4]) == [6]                          # "4+" inclui 5 dormitórios
    # Por quarto: 1 -> R$ 1000, 2 -> R$ 1060 (kitnet), 3 -> R$ 750, 6 -> R$ 360 (5 quartos)
    assert codigos(preco_max_por_quarto=800) == [3, 6]


def test_distancia_vem_do_lugar_escolhido(csv_de_exemplo):
    df = carregar_imoveis(csv_de_exemplo)

    def distancias(lugar):
        return aplicar_filtros(df, Filtros(perto_de=lugar)).set_index("codigo")["distancia_km"]

    usp, ufscar, rodoviaria = distancias("USP"), distancias("UFSCar"), distancias("Rodoviária")
    assert usp[2] < 1 < 3 < ufscar[2]  # o Jardim Paraíso fica do lado da USP
    # O Centro fica mais perto da rodoviária que da USP; o Jardim Paraíso, o contrário
    assert rodoviaria[1] < usp[1] < 3 < ufscar[1]
    assert usp[2] < rodoviaria[2]


def test_filtro_de_imobiliaria(csv_de_exemplo):
    df = carregar_imoveis(csv_de_exemplo).assign(fonte=["cardinali", "roca", "cardinali", "roca"])
    assert sorted(aplicar_filtros(df, Filtros(imobiliarias=["roca"]))["codigo"]) == [2, 6]
    assert len(aplicar_filtros(df, Filtros(imobiliarias=[]))) == 4  # nada marcado: todas


def test_marcar_duplicatas():
    df = pd.DataFrame([
        # fonte, bairro, quartos, área, total
        ("cardinali", "Centro", 2, 60.0, 2000.0),
        ("roca", "Centro", 2, 61.0, 2080.0),        # área 1,6% e total 3,8% diferentes: parece o mesmo
        ("roca", "Centro", 2, 60.0, 2300.0),        # total 13% maior: outro imóvel
        ("roca", "Centro", 3, 60.0, 2000.0),        # outro nº de quartos
        ("roca", "Jardim Paraíso", 2, 60.0, 2000.0),  # outro bairro
        ("cardinali", "Centro", 2, 60.0, 2010.0),   # mesma imobiliária que o 1º: não é duplicata entre elas
        ("roca", "Centro", 2, None, 2000.0),        # sem área: não compara
    ], columns=["fonte", "bairro", "dormitorios", "area_m2", "total_mensal"], index=range(10, 17))
    duplicata = marcar_duplicatas(df)["duplicata_de"]
    assert duplicata.dropna().to_dict() == {10: "roca", 11: "cardinali", 15: "roca"}
