"""Testes do mapa: faixas de preço, cores, legenda e o que aparece desenhado."""
import folium
import pandas as pd

from app.bairros import RODOVIARIA, UFSCAR, USP, buscar_coords
from app.dados import Filtros, aplicar_filtros, carregar_imoveis
from app.mapa import COR_SEM_DADO, CORES_FAIXAS, cor_da_faixa, criar_mapa, faixas_de_preco, legenda
from app.metricas import resumo_por_bairro


def test_faixas_tem_quantidades_parecidas_de_bairros():
    # 10 bairros de R$ 600 a R$ 1500 e um caríssimo: ele não empurra os limites para cima
    valores = pd.Series([600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 6000])
    assert faixas_de_preco(valores) == [800, 1000, 1200, 1400]
    assert faixas_de_preco(pd.Series([900, 900, None])) == []  # um valor só: nada para comparar


def test_cor_da_faixa():
    limites = [800, 1000, 1200, 1400]
    assert cor_da_faixa(500, limites) == CORES_FAIXAS[0]      # mais barato: o azul mais claro
    assert cor_da_faixa(1000, limites) == CORES_FAIXAS[2]     # o limite já é da faixa de cima
    assert cor_da_faixa(9000, limites) == CORES_FAIXAS[-1]
    assert cor_da_faixa(float("nan"), limites) == COR_SEM_DADO
    # Com poucas faixas, as cores pulam degraus para continuarem bem diferentes entre si
    assert [cor_da_faixa(valor, [1000]) for valor in (500, 1500)] == [CORES_FAIXAS[0], CORES_FAIXAS[-1]]


def test_legenda():
    assert [texto for _, texto in legenda([800, 1000])] == ["até R$ 800", "R$ 800 a R$ 1.000", "mais de R$ 1.000"]
    assert legenda([]) == []


def desenhar(perto_de, distancia_max_km, destaque=None):
    """O mapa e o que foi desenhado nele: as etiquetas (HTML), os círculos (centro, raio em metros) e o
    centro do mapa."""
    df = aplicar_filtros(carregar_imoveis(), Filtros(perto_de=perto_de, distancia_max_km=distancia_max_km))
    mapa = criar_mapa(resumo_por_bairro(df), perto_de, distancia_max_km, destaque)
    filhos = list(mapa._children.values())
    pinos = [pino for grupo in filhos if isinstance(grupo, folium.FeatureGroup) for pino in grupo._children.values()]
    etiquetas = [icone.options["html"] for marcador in pinos if isinstance(marcador, folium.Marker)
                 for icone in marcador._children.values() if isinstance(icone, folium.DivIcon)]
    circulos = [(tuple(circulo.location), circulo.options["radius"]) for circulo in filhos
                if isinstance(circulo, folium.Circle)]
    return etiquetas, circulos, tuple(mapa.location)


def escolhida(etiquetas):
    """A etiqueta destacada (a do lugar escolhido): tem de haver uma só."""
    escolhidas = [etiqueta for etiqueta in etiquetas if 'class="pino escolhido"' in etiqueta]
    assert len(escolhidas) == 1
    return escolhidas[0]


def test_mapa_destaca_o_lugar_escolhido_e_mostra_o_raio():
    etiquetas, circulos, _ = desenhar("UFSCar", 3.0)
    assert len(etiquetas) == 3  # USP, UFSCar e rodoviária
    assert "<span>UFSCar</span>" in escolhida(etiquetas)
    assert circulos == [(UFSCAR, 3000.0)]
    assert desenhar("USP", None)[1] == []  # "qualquer distância": sem círculo


def test_mapa_perto_da_rodoviaria():
    etiquetas, circulos, _ = desenhar("Rodoviária", 1.5)
    assert "<span>Rodoviária</span>" in escolhida(etiquetas)
    assert circulos == [(RODOVIARIA, 1500.0)]
    # A USP fica a ~800 m: só com o ícone, para as duas etiquetas não se cobrirem
    assert sum('class="pino so-icone"' in etiqueta for etiqueta in etiquetas) == 1
    assert not any("<span>USP</span>" in etiqueta for etiqueta in etiquetas)


def test_mapa_destaca_o_bairro_do_ver_no_mapa():
    etiquetas, _, centro = desenhar("USP", 3.0, destaque="Centro")
    assert centro == buscar_coords("Centro")  # o mapa centraliza no bairro
    destacados = [etiqueta for etiqueta in etiquetas if 'class="pino bairro"' in etiqueta]
    assert len(destacados) == 1 and "<span>Centro</span>" in destacados[0]
    # Um bairro que não está no mapa (os filtros o tiraram) é ignorado
    etiquetas, _, centro = desenhar("USP", 3.0, destaque="Bairro Que Não Existe")
    assert centro == USP and not any("pino bairro" in etiqueta for etiqueta in etiquetas)
