"""Testes do mapa: faixas de preço, cores, legenda e o que aparece desenhado."""
import folium
import pandas as pd

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


def desenhar(campus, distancia_max_km):
    """O mapa e o que foi desenhado nele: as etiquetas (HTML) e os raios dos círculos (em metros)."""
    df = aplicar_filtros(carregar_imoveis(), Filtros(campus=campus, distancia_max_km=distancia_max_km))
    mapa = criar_mapa(resumo_por_bairro(df), campus, distancia_max_km)
    filhos = list(mapa._children.values())
    etiquetas = [icone.options["html"] for marcador in filhos if isinstance(marcador, folium.Marker)
                 for icone in marcador._children.values() if isinstance(icone, folium.DivIcon)]
    raios = [circulo.options["radius"] for circulo in filhos if isinstance(circulo, folium.Circle)]
    return etiquetas, raios


def test_mapa_destaca_o_campus_escolhido_e_mostra_o_raio():
    etiquetas, raios = desenhar("UFSCar", 3.0)
    assert len(etiquetas) == 3  # USP, UFSCar e rodoviária
    escolhidos = [etiqueta for etiqueta in etiquetas if 'class="pino escolhido"' in etiqueta]
    assert len(escolhidos) == 1 and "<span>UFSCar</span>" in escolhidos[0]
    assert raios == [3000.0]
    assert desenhar("USP", None)[1] == []  # "qualquer distância": sem círculo
