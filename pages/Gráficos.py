import altair as alt
import streamlit as st

from app import formatacao as fmt
from app.dados import aplicar_filtros, carregar_imoveis
from app.interface import barra_lateral, ranking_bairros
from app.metricas import MINIMO_IMOVEIS_BAIRRO, escolher_campus, indice_custo_beneficio, resumo_por_bairro

st.set_page_config(page_title="Gráficos · Análise Imobiliária Universitária", page_icon=":material/bar_chart:",
                   layout="wide")

# Uma série só: o azul validado contra o fundo escuro do app (contraste >= 3:1).
# Cinza para o contexto quando um bairro está em destaque.
COR_SERIE = "#3987e5"
COR_CONTEXTO = "#64748b"
NENHUM = "Nenhum"

LOCALE_BR = alt.Locale(number=alt.NumberLocale(decimal=",", thousands=".", grouping=[3], currency=["R$ ", ""]))

imoveis = carregar_imoveis()
escolhas = barra_lateral(imoveis)
df = escolher_campus(aplicar_filtros(imoveis, escolhas.filtros), escolhas.campus)
df = df.assign(indice=indice_custo_beneficio(df, escolhas.pesos))
resumo = resumo_por_bairro(df)

st.title(":material/bar_chart: Gráficos")
st.caption("Os mesmos filtros da página principal, na barra lateral. Passe o mouse nos gráficos para ver os números.")

if df.empty:
    st.info("Nenhum imóvel com esses filtros.")
    st.stop()

# --- Custo por dormitório por bairro -------------------------------------------------------
st.subheader("Quanto custa cada dormitório, por bairro")
confiaveis = resumo[resumo["imoveis"] >= MINIMO_IMOVEIS_BAIRRO].dropna(subset=["custo_por_dormitorio"])
st.caption(f"Mediana do custo por dormitório (total por mês ÷ dormitórios), do bairro mais barato ao mais caro. "
           f"Só bairros com pelo menos {MINIMO_IMOVEIS_BAIRRO} imóveis.")
barras = (
    alt.Chart(confiaveis)
    .mark_bar(color=COR_SERIE, cornerRadiusEnd=4, size=14)
    .encode(
        x=alt.X("custo_por_dormitorio:Q", title="R$ por dormitório por mês (mediana)",
                axis=alt.Axis(format="$,.0f", grid=True)),
        y=alt.Y("bairro:N", sort="x", title=None, axis=alt.Axis(labelLimit=280)),
        tooltip=[
            alt.Tooltip("bairro:N", title="Bairro"),
            alt.Tooltip("custo_por_dormitorio:Q", title="Por dormitório (mediana)", format="$,.0f"),
            alt.Tooltip("total_mensal:Q", title="Aluguel total (mediana)", format="$,.0f"),
            alt.Tooltip("imoveis:Q", title="Imóveis"),
            alt.Tooltip("distancia_km:Q", title=f"Distância {escolhas.distancia_ate} (km)", format=",.1f"),
        ],
    )
    .properties(height=max(120, 24 * len(confiaveis)))
    .configure(locale=LOCALE_BR)
)
st.altair_chart(barras, width="stretch")

# --- Distância x custo por dormitório ------------------------------------------------------
st.subheader("Morar mais perto custa mais caro?")
st.caption("Cada ponto é um imóvel. Como o site não informa o endereço, a distância é a do bairro: "
           "cada coluna de pontos é um bairro.")
destacado = st.selectbox("Destacar um bairro", [NENHUM] + sorted(df["bairro"].unique()), key="destaque_grafico")
cor = (alt.value(COR_SERIE) if destacado == NENHUM
       else alt.condition(alt.datum.bairro == destacado, alt.value(COR_SERIE), alt.value(COR_CONTEXTO)))
pontos = (
    alt.Chart(df.dropna(subset=["custo_por_dormitorio", "distancia_km"]))
    .mark_circle(size=70, opacity=0.7, stroke="#1d293d", strokeWidth=1)
    .encode(
        x=alt.X("distancia_km:Q", title=f"Distância {escolhas.distancia_ate} (km)", axis=alt.Axis(format=",.1f")),
        y=alt.Y("custo_por_dormitorio:Q", title="R$ por dormitório por mês", axis=alt.Axis(format="$,.0f")),
        color=cor,
        # O destacado fica por cima dos demais
        order=alt.condition(alt.datum.bairro == destacado, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("titulo:N", title="Anúncio"),
            alt.Tooltip("bairro:N", title="Bairro"),
            alt.Tooltip("total_mensal:Q", title="Total por mês", format="$,.0f"),
            alt.Tooltip("custo_por_dormitorio:Q", title="Por dormitório", format="$,.0f"),
            alt.Tooltip("dormitorios:Q", title="Dormitórios"),
            alt.Tooltip("distancia_km:Q", title="Distância (km)", format=",.1f"),
        ],
    )
    .properties(height=420)
    .configure(locale=LOCALE_BR)
)
st.altair_chart(pontos, width="stretch")

with st.expander("Ver os números por bairro em uma tabela", icon=":material/table:"):
    st.caption(f"{fmt.numero(len(resumo))} bairros, {fmt.numero(len(df))} imóveis")
    ranking_bairros(resumo, altura=420, completo=True)
