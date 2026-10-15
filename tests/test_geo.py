"""Testes do mapa de bairros com dados sintéticos perto de São Carlos (sem acessar o OSM)."""
from collections import Counter

import pytest
from shapely.geometry import Point, box, shape

from geo import osm
from geo.gerar import Projecao, aproximar, contorno_por_enderecos, gerar
from geo.nomes import carregar_aliases, nome_padrao, normalizar

LAT, LON = -22.0, -47.9  # um ponto qualquer em São Carlos


def caminho(nome, lon, lat, lado=0.01, fechado=True, **tags):
    pontos = [(lon, lat), (lon + lado, lat), (lon + lado, lat + lado), (lon, lat + lado)]
    if fechado:
        pontos.append(pontos[0])
    return {"type": "way", "tags": {"place": "suburb", "name": nome, **tags},
            "geometry": [{"lon": x, "lat": y} for x, y in pontos]}


def no(nome, lon, lat):
    return {"type": "node", "tags": {"place": "suburb", "name": nome}, "lon": lon, "lat": lat}


def enderecos(bairro, lon, lat, quantidade=25, passo=0.0005):
    """Grade de endereços em volta de (lon, lat), marcados com o bairro."""
    lado = int(quantidade ** 0.5)
    return [{"type": "node", "tags": {"addr:suburb": bairro, "addr:street": "Rua X"},
             "lon": lon + (i - lado // 2) * passo, "lat": lat + (j - lado // 2) * passo}
            for i in range(lado) for j in range(lado)]


# --- nomes --------------------------------------------------------------------------------

def test_normalizar():
    assert normalizar("Vila Monteiro (Gleba I)") == normalizar("vila monteiro gleba i") == "vila monteiro gleba i"
    assert normalizar("Jardim São Carlos") == "jardim sao carlos"


def test_aliases(tmp_path):
    arquivo = tmp_path / "aliases.csv"
    arquivo.write_text("grafia,bairro\nJardim Hikari,Jardim Hikare\n", encoding="utf-8")
    aliases = carregar_aliases(arquivo)
    assert nome_padrao("jardim  HIKARI", aliases) == "Jardim Hikare"
    assert nome_padrao("Centro", aliases) == "Centro"


# --- leitura do OSM -----------------------------------------------------------------------

def test_ler_elementos():
    externo = caminho("x", LON, LAT, lado=0.02)["geometry"]
    interno = caminho("x", LON + 0.005, LAT + 0.005, lado=0.005)["geometry"]
    dados = {"elements": [
        caminho("Jardim Teste", LON, LAT),
        caminho("Quadra 1", LON, LAT),                    # quadra de condomínio: ignorada
        caminho("Rua Aberta", LON, LAT, fechado=False),   # caminho aberto não é área
        {"type": "relation", "tags": {"place": "suburb", "name": "Parque Com Buraco"}, "members": [
            {"type": "way", "role": "outer", "geometry": externo},
            {"type": "way", "role": "inner", "geometry": interno},
        ]},
        no("Centro", LON, LAT),
        *enderecos("Centro", LON, LAT, quantidade=4),
    ]}
    poligonos, pontos, enderecos_por_bairro = osm.ler_elementos(dados)
    assert set(poligonos) == {"Jardim Teste", "Parque Com Buraco"}
    assert poligonos["Parque Com Buraco"].area == pytest.approx(0.02 ** 2 - 0.005 ** 2)
    assert set(pontos) == {"Centro"}
    assert len(enderecos_por_bairro["Centro"]) == 4


def test_relacao_com_borda_dividida_em_dois_caminhos():
    a, b, c, d = (LON, LAT), (LON + 0.01, LAT), (LON + 0.01, LAT + 0.01), (LON, LAT + 0.01)
    relacao = {"members": [
        {"type": "way", "role": "outer", "geometry": [{"lon": x, "lat": y} for x, y in (a, b, c)]},
        {"type": "way", "role": "outer", "geometry": [{"lon": x, "lat": y} for x, y in (c, d, a)]},
    ]}
    assert osm.poligono_da_relacao(relacao).area == pytest.approx(0.01 ** 2)


# --- contornos calculados -----------------------------------------------------------------

def test_projecao_ida_e_volta():
    projecao = Projecao(LAT)
    ponto = Point(LON, LAT)
    assert projecao.para_graus(projecao.para_metros(ponto)).equals_exact(ponto, 1e-9)
    # 0,01 grau de latitude ~ 1,1 km
    assert projecao.para_metros(Point(0, 0.01)).y == pytest.approx(1105.4)


def pontos_de(elementos):
    return [Point(e["lon"], e["lat"]) for e in elementos]


def test_contorno_por_enderecos_envolve_os_enderecos():
    nuvem = pontos_de(enderecos("Centro", LON, LAT))
    contorno = contorno_por_enderecos(nuvem, Point(LON, LAT), ocupado=Point(0, 0).buffer(0.001))
    assert all(contorno.buffer(1e-9).contains(ponto) for ponto in nuvem)


def test_contorno_por_enderecos_ignora_endereco_isolado_longe():
    nuvem = pontos_de(enderecos("Centro", LON, LAT)) + [Point(LON + 0.05, LAT)]  # ~5 km dali
    contorno = contorno_por_enderecos(nuvem, Point(LON, LAT), ocupado=Point(0, 0).buffer(0.001))
    assert not contorno.contains(Point(LON + 0.05, LAT))


def test_contorno_por_enderecos_recusa_nuvem_longe_do_ponto_do_bairro():
    nuvem = pontos_de(enderecos("Vila Prado", LON, LAT))
    assert contorno_por_enderecos(nuvem, Point(LON, LAT + 0.01), ocupado=Point(0, 0).buffer(0.001)) is None


def test_contorno_por_enderecos_recusa_poucos_enderecos():
    nuvem = pontos_de(enderecos("Centro", LON, LAT, quantidade=9))
    assert contorno_por_enderecos(nuvem, None, ocupado=Point(0, 0).buffer(0.001)) is None


def test_aproximar_nao_invade_bairro_vizinho():
    vizinho = box(LON + 0.002, LAT - 0.01, LON + 0.02, LAT + 0.01)
    resultado = aproximar({"Vila Só Ponto": Point(LON, LAT)}, [vizinho.representative_point()], vizinho)
    contorno = resultado["Vila Só Ponto"]
    assert contorno.contains(Point(LON, LAT))
    assert contorno.intersection(vizinho).area == pytest.approx(0, abs=1e-12)
    # Raio de 700 m: ~0,0068 grau na longitude de São Carlos
    assert contorno.bounds[0] > LON - 0.0072


# --- geração completa ---------------------------------------------------------------------

def test_gerar_ponta_a_ponta():
    dados = {"elements": [
        caminho("Jardim Teste", LON - 0.03, LAT),
        caminho("Parque Desenhado", LON + 0.03, LAT),
        no("Centro", LON, LAT),
        *enderecos("Centro", LON, LAT),
        no("Vila So Ponto", LON, LAT - 0.03),
    ]}
    aliases = {normalizar("Jardim Teste Antigo"): "Jardim Teste"}
    desenho = box(LON + 0.03, LAT, LON + 0.035, LAT + 0.005)
    no_site = Counter({"Jardim Teste Antigo": 3, "Centro": 5, "Vila Só Ponto": 1, "Bairro Sem Nada": 2})

    features, sem_contorno = gerar(dados, aliases, {"Parque Desenhado": desenho}, {}, no_site)
    por_bairro = {f["properties"]["bairro"]: f for f in features}

    assert {nome: f["properties"]["origem"] for nome, f in por_bairro.items()} == {
        "Jardim Teste": "osm",          # grafia antiga do site resolvida pelo alias
        "Parque Desenhado": "manual",   # o desenho manual substitui o polígono do OSM
        "Centro": "enderecos",
        "Vila Só Ponto": "aproximado",  # a grafia com acento ganha da sem acento
    }
    assert shape(por_bairro["Parque Desenhado"]["geometry"]).area == pytest.approx(desenho.area, rel=0.01)
    centro = por_bairro["Centro"]["properties"]
    assert shape(por_bairro["Centro"]["geometry"]).contains(Point(centro["lon"], centro["lat"]))
    assert sem_contorno == ["Bairro Sem Nada (2)"]


def test_ponto_manual_vale_mais_que_o_do_osm():
    # O ponto do OSM está longe dos endereços; o ponto coletado à mão está no meio deles
    dados = {"elements": [no("Centro", LON, LAT - 0.01), *enderecos("Centro", LON, LAT)]}
    sem_manual, _ = gerar(dados, {}, {}, {}, Counter({"Centro": 1}))
    com_manual, _ = gerar(dados, {}, {}, {"Centro": Point(LON, LAT)}, Counter({"Centro": 1}))
    assert sem_manual[0]["properties"]["origem"] == "aproximado"
    assert com_manual[0]["properties"]["origem"] == "enderecos"
