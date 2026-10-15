"""Mapa com a área de cada bairro pintada conforme a métrica escolhida."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import branca.colormap as cm
import folium
import pandas as pd

from app import formatacao as fmt
from app.bairros import RODOVIARIA, UFSCAR, USP, buscar_contorno

PASTA_ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Escala sequencial de um tom só (azul), do claro ao escuro: mais escuro = valor maior.
# Um tom só lê bem para daltônicos; arco-íris e vermelho/verde não.
ESCALA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
COR_SEM_DADO = "#c3c2b7"


@dataclass(frozen=True)
class MetricaMapa:
    rotulo: str
    formatar: Callable
    leitura: str  # o que significa a cor mais escura


METRICAS_MAPA = {
    "indice": MetricaMapa("Índice custo-benefício", fmt.numero, "mais escuro = melhor"),
    "custo_por_dormitorio": MetricaMapa("Custo por dormitório", fmt.reais, "mais escuro = mais caro"),
    "total_mensal": MetricaMapa("Aluguel total", fmt.reais, "mais escuro = mais caro"),
    "preco_m2": MetricaMapa("Preço por m²", fmt.reais, "mais escuro = mais caro"),
    "imoveis": MetricaMapa("Oferta de imóveis", fmt.numero, "mais escuro = mais opções"),
}

# Explicação no tooltip dos bairros cujo contorno não veio pronto do OpenStreetMap
AVISO_CONTORNO = {
    "enderecos": "Contorno estimado pelos endereços do bairro no OpenStreetMap",
    "aproximado": "Contorno aproximado (o bairro só tem um ponto no OpenStreetMap)",
}


def _texto_tooltip(linha: pd.Series, origem: str, distancia_ate: str) -> str:
    linhas = [
        f"<b style='font-size:14px'>{linha['bairro']}</b>",
        f"{fmt.numero(linha['imoveis'])} imóveis · {fmt.km(linha['distancia_km'])} {distancia_ate}",
        f"Aluguel total (mediana): <b>{fmt.reais(linha['total_mensal'])}</b>",
        f"Por dormitório (mediana): <b>{fmt.reais(linha['custo_por_dormitorio'])}</b>",
        f"Preço por m² (mediana): <b>{fmt.reais(linha['preco_m2'])}</b>",
        f"Índice custo-benefício: <b>{fmt.numero(linha['indice'])}</b>",
    ]
    if origem in AVISO_CONTORNO:
        linhas.append(f"<em style='font-size:11px'>{AVISO_CONTORNO[origem]}</em>")
    return "<br>".join(linhas)


def _marcador(mapa: folium.Map, local, imagem: str, tamanho: tuple[int, int], ancora: tuple[int, int], nome: str):
    icone = folium.CustomIcon(icon_image=str(PASTA_ASSETS / imagem), icon_size=tamanho, icon_anchor=ancora)
    folium.Marker(location=local, icon=icone, tooltip=nome).add_to(mapa)


def criar_mapa(resumo: pd.DataFrame, metrica: str, distancia_ate: str, ver_cidade_toda: bool) -> folium.Map:
    """Pinta cada bairro do resumo (uma linha por bairro, de metricas.resumo_por_bairro).

    `distancia_ate` completa o texto da distância no tooltip, ex.: "da USP".
    """
    centro, zoom = ((-22.005, -47.89), 13) if ver_cidade_toda else ((-21.997, -47.888), 14)
    mapa = folium.Map(location=centro, zoom_start=zoom, min_zoom=12, max_zoom=17, tiles="OpenStreetMap")

    definicao = METRICAS_MAPA[metrica]
    valores = resumo[metrica].dropna()
    escala = None
    if not valores.empty:
        minimo, maximo = float(valores.min()), float(valores.max())
        escala = cm.LinearColormap(ESCALA_AZUL, vmin=minimo, vmax=maximo if maximo > minimo else minimo + 1,
                                   max_labels=6)
        escala.width = 300  # o padrão (450 px) não cabe no mapa no celular
        escala.caption = definicao.rotulo  # a leitura das cores vai no texto abaixo do mapa
        mapa.add_child(escala)

    for _, linha in resumo.iterrows():
        contorno = buscar_contorno(linha["bairro"])
        if contorno is None:  # bairro sem contorno: aparece só na lista de imóveis
            continue
        valor = linha[metrica]
        cor = escala(valor) if escala is not None and pd.notna(valor) else COR_SEM_DADO
        folium.GeoJson(
            contorno,
            # Borda branca fina: separa bairros vizinhos que têm cores parecidas
            style_function=lambda _, cor=cor: {"fillColor": cor, "color": "white", "weight": 1.2, "fillOpacity": 0.7},
            highlight_function=lambda _: {"color": "#1f2937", "weight": 2.5, "fillOpacity": 0.85},
            tooltip=folium.Tooltip(_texto_tooltip(linha, contorno["properties"]["origem"], distancia_ate)),
        ).add_to(mapa)

    _marcador(mapa, USP, "usp-logo.png", (70, 70), (25, 23), "Universidade de São Paulo (USP)")
    _marcador(mapa, UFSCAR, "ufscar-logo.png", (90, 90), (40, 23), "Universidade Federal de São Carlos (UFSCar)")
    _marcador(mapa, RODOVIARIA, "icone-rodoviaria.png", (45, 45), (40, 23), "Rodoviária de São Carlos")
    return mapa
