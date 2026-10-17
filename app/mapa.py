"""Mapa dos bairros: cada um pintado pelo preço típico por quarto, com os campi e a rodoviária."""
import html
from bisect import bisect_right

import folium
import pandas as pd

from app import formatacao as fmt
from app.bairros import RODOVIARIA, buscar_contorno
from app.metricas import CAMPI

# Escala sequencial de um tom só (azul): mais escuro = mais caro. Um tom só lê bem para
# daltônicos; arco-íris e vermelho/verde não. São 5 degraus bem separados da mesma escala azul.
CORES_FAIXAS = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
COR_SEM_DADO = "#d9dce5"
COR_DESTAQUE = "#4f46e5"  # a cor principal do tema (.streamlit/config.toml)
CENTRO_DA_CIDADE = (-22.005, -47.89)
# Zoom de acordo com a distância escolhida: dá para ver o círculo inteiro numa tela de computador.
# (Enquadrar automaticamente, com fit_bounds, não funciona bem: o streamlit-folium cria o mapa num
# tamanho e depois o redimensiona, e o enquadramento fica calculado para o tamanho errado.)
ZOOM_POR_DISTANCIA = {1.5: 15, 3.0: 14, 5.0: 13}
ZOOM_CIDADE_TODA = 13

# Ícones "school" e "directions_bus" do Material Design (licença Apache 2.0), desenhados em SVG
ICONE_CAMPUS = "M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"
ICONE_ONIBUS = ("M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 "
                "0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67"
                "-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5"
                "-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z")

# O CSS vale dentro do mapa (que o streamlit-folium desenha num iframe à parte).
# - Tiles do OpenStreetMap em cinza: o mapa vira fundo e as cores dos bairros aparecem mais.
# - Os marcadores são etiquetas com ícone, com uma pontinha embaixo apontando o lugar.
ESTILO = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700&display=swap');
.leaflet-container {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; background: #eceef3; }}
.leaflet-tile-pane {{ filter: grayscale(1) brightness(1.06) contrast(0.9); }}
.leaflet-tooltip {{
    border: none; border-radius: 12px; padding: 10px 12px; color: #171a26;
    box-shadow: 0 6px 20px rgba(23, 26, 38, .18); font-size: 13px; line-height: 1.45;
}}
.leaflet-tooltip .grande {{ font-size: 17px; font-weight: 700; }}
.leaflet-tooltip .fraco {{ color: #5d6275; }}
.pino-caixa {{ background: none; border: none; }}
.pino {{
    position: absolute; transform: translate(-50%, calc(-100% - 7px));
    display: flex; align-items: center; gap: 6px; padding: 5px 12px 5px 5px;
    border-radius: 999px; background: #fff; color: #171a26; white-space: nowrap;
    font-weight: 700; font-size: 13px; box-shadow: 0 3px 10px rgba(23, 26, 38, .28);
}}
.pino::after {{
    content: ""; position: absolute; left: 50%; bottom: -7px; transform: translateX(-50%);
    border: 7px solid transparent; border-top-color: #fff; border-bottom: 0;
}}
.pino svg {{ width: 16px; height: 16px; padding: 4px; border-radius: 50%; fill: currentColor; background: #eef0f6; }}
.pino.escolhido {{ background: {COR_DESTAQUE}; color: #fff; font-size: 14px; z-index: 2; }}
.pino.escolhido::after {{ border-top-color: {COR_DESTAQUE}; }}
.pino.escolhido svg {{ background: rgba(255, 255, 255, .22); }}
.pino.so-icone {{ padding: 3px; }}  /* só o ícone: o nome aparece ao passar o mouse */
.pino.so-icone svg {{ width: 13px; height: 13px; padding: 3px; background: #171a26; color: #fff; }}
</style>
"""


def faixas_de_preco(valores: pd.Series, quantidade: int = len(CORES_FAIXAS)) -> list[float]:
    """Limites entre as cores do mapa, para cada cor ficar com mais ou menos o mesmo número de bairros.

    Com faixas assim (e não divididas por igual entre o mais barato e o mais caro), um bairro
    caríssimo não deixa todos os outros com a mesma cor clara. Os limites são arredondados em R$ 50.
    """
    valores = valores.dropna()
    if valores.nunique() < 2:
        return []
    limites = valores.quantile([parte / quantidade for parte in range(1, quantidade)])
    return sorted({round(limite / 50) * 50 for limite in limites})


def cor_da_faixa(valor, limites: list[float]) -> str:
    if pd.isna(valor):
        return COR_SEM_DADO
    # Com menos faixas (poucos bairros), usa cores espaçadas da mesma escala, do clarinho ao escuro
    cores = [CORES_FAIXAS[round(i * (len(CORES_FAIXAS) - 1) / max(1, len(limites)))] for i in range(len(limites) + 1)]
    return cores[bisect_right(limites, valor)]


def legenda(limites: list[float]) -> list[tuple[str, str]]:
    """(cor, texto) de cada faixa, para mostrar abaixo do mapa."""
    if not limites:
        return []
    textos = ([f"até {fmt.reais(limites[0])}"]
              + [f"{fmt.reais(de)} a {fmt.reais(ate)}" for de, ate in zip(limites, limites[1:])]
              + [f"mais de {fmt.reais(limites[-1])}"])
    return [(cor_da_faixa(valor, limites), texto)
            for valor, texto in zip([limites[0] - 1] + limites, textos)]


def _texto_dica(linha: pd.Series, campus: str) -> str:
    return (
        f"<b>{html.escape(linha['bairro'])}</b><br>"
        f"<span class='grande'>{fmt.reais(linha['custo_por_dormitorio'])}</span> por quarto "
        f"<span class='fraco'>(típico)</span><br>"
        f"{fmt.numero(linha['imoveis'])} {'imóvel' if linha['imoveis'] == 1 else 'imóveis'} · "
        f"a partir de {fmt.reais(linha['mais_barato'])}<br>"
        f"<span class='fraco'>{fmt.km(linha['distancia_km'])} da {campus} · "
        f"{fmt.minutos_a_pe(linha['distancia_km'])}</span>"
    )


def _pino(mapa: folium.Map, local, nome: str, icone: str, classe: str, dica: str) -> None:
    desenho = f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{icone}"/></svg>'
    nome = f"<span>{nome}</span>" if nome else ""
    folium.Marker(
        location=local, tooltip=dica, z_index_offset=1000,
        icon=folium.DivIcon(html=f'<div class="pino {classe}">{desenho}{nome}</div>',
                            class_name="pino-caixa", icon_size=(0, 0)),
    ).add_to(mapa)


def criar_mapa(resumo: pd.DataFrame, campus: str, distancia_max_km: float | None) -> folium.Map:
    """Pinta cada bairro do resumo (uma linha por bairro, de metricas.resumo_por_bairro)."""
    if distancia_max_km is None:
        centro, zoom = CENTRO_DA_CIDADE, ZOOM_CIDADE_TODA
    else:
        centro, zoom = CAMPI[campus], ZOOM_POR_DISTANCIA.get(distancia_max_km, ZOOM_CIDADE_TODA)
    mapa = folium.Map(location=centro, zoom_start=zoom, min_zoom=12, max_zoom=17, tiles="OpenStreetMap",
                      control_scale=True)
    mapa.get_root().header.add_child(folium.Element(ESTILO))

    limites = faixas_de_preco(resumo["custo_por_dormitorio"])
    for _, linha in resumo.iterrows():
        contorno = buscar_contorno(linha["bairro"])
        if contorno is None:  # bairro sem contorno: aparece só na lista de imóveis
            continue
        cor = cor_da_faixa(linha["custo_por_dormitorio"], limites)
        folium.GeoJson(
            contorno,
            # Borda branca: separa bairros vizinhos que têm cores parecidas
            style_function=lambda _, cor=cor: {"fillColor": cor, "color": "white", "weight": 1.5, "fillOpacity": 0.72},
            highlight_function=lambda _: {"color": COR_DESTAQUE, "weight": 3, "fillOpacity": 0.85},
            tooltip=folium.Tooltip(_texto_dica(linha, campus), sticky=True),
        ).add_to(mapa)

    if distancia_max_km is not None:
        # O raio do filtro de distância, em volta do campus
        folium.Circle(CAMPI[campus], radius=distancia_max_km * 1000, color=COR_DESTAQUE, weight=2,
                      dash_array="6 8", fill=False, interactive=False).add_to(mapa)

    for nome, local in CAMPI.items():
        classe = "escolhido" if nome == campus else ""
        _pino(mapa, local, nome, ICONE_CAMPUS, classe, f"Campus {'1 da USP' if nome == 'USP' else 'da UFSCar'}")
    # A rodoviária fica a ~800 m da USP: com o nome escrito, as duas etiquetas se cobririam
    _pino(mapa, RODOVIARIA, "", ICONE_ONIBUS, "so-icone", "Rodoviária de São Carlos")
    return mapa
