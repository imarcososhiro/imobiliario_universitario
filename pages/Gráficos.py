from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

from app import formatacao as fmt
from app.dados import aplicar_filtros, carregar_imoveis
from app.historico import carregar_historico, tendencia_semanal
from app.interface import barra_lateral, ranking_bairros
from app.metricas import MINIMO_IMOVEIS_BAIRRO, escolher_campus, indice_custo_beneficio, resumo_por_bairro
from historico.consultas import INICIO_CIDADE_TODA

st.set_page_config(page_title="Gráficos · Análise Imobiliária Universitária", page_icon=":material/bar_chart:",
                   layout="wide")

# Uma série só: o azul validado contra o fundo escuro do app (contraste >= 3:1).
# Cinza para o contexto quando um bairro está em destaque.
COR_SERIE = "#3987e5"
COR_CONTEXTO = "#64748b"
NENHUM = "Nenhum"
MEDIDAS_TENDENCIA = {"custo_por_dormitorio": "Custo por dormitório", "total_mensal": "Aluguel total"}
# Segunda-feira da semana em que a coleta passou a cobrir a cidade toda
SEMANA_CIDADE_TODA = INICIO_CIDADE_TODA - timedelta(days=INICIO_CIDADE_TODA.weekday())

LOCALE_BR = alt.Locale(
    number=alt.NumberLocale(decimal=",", thousands=".", grouping=[3], currency=["R$ ", ""]),
    time=alt.TimeLocale(
        dateTime="%A, %e de %B de %Y, %X", date="%d/%m/%Y", time="%H:%M:%S", periods=["AM", "PM"],
        days=["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
        shortDays=["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
        months=["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
                "outubro", "novembro", "dezembro"],
        shortMonths=["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]),
)

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

# --- Tendência ao longo do tempo -----------------------------------------------------------
st.subheader("Os aluguéis estão subindo ou caindo?")
historico = carregar_historico()
if historico is None:
    st.info("O histórico de preços não pôde ser carregado agora. Recarregue a página mais tarde para ver a "
            "tendência.", icon=":material/cloud_off:")
    st.stop()

area = "Região universitária" if escolhas.filtros.so_regiao_universitaria else "Cidade toda"
coluna_medida, coluna_bairro = st.columns(2)
medida = coluna_medida.radio("Medida", list(MEDIDAS_TENDENCIA), format_func=MEDIDAS_TENDENCIA.get, horizontal=True,
                             key="medida_tendencia")
comparar = coluna_bairro.selectbox("Comparar com um bairro", [NENHUM] + sorted(df["bairro"].unique()),
                                   key="bairro_tendencia")
bairro = None if comparar == NENHUM else comparar
tendencia = tendencia_semanal(aplicar_filtros(historico.semanal, escolhas.filtros), medida, area, bairro)
if bairro and bairro not in set(tendencia["serie"]):
    st.caption(f"{bairro} não teve {MINIMO_IMOVEIS_BAIRRO} imóveis com esses filtros em nenhuma semana: "
               "o gráfico mostra só a linha geral.")
    bairro = None
    tendencia = tendencia[tendencia["serie"] == area]
if tendencia.empty:
    st.info("Poucos imóveis com esses filtros para traçar a tendência. Tente ampliar os filtros.")
    st.stop()

mostra_mudanca_de_cobertura = tendencia["semana"].min() < pd.Timestamp(SEMANA_CIDADE_TODA)
st.caption(f"Mediana {'do custo por dormitório' if medida == 'custo_por_dormitorio' else 'do aluguel total'} "
           f"por semana, com os filtros da barra lateral. Cada imóvel conta uma vez por semana, e semanas com "
           f"menos de {MINIMO_IMOVEIS_BAIRRO} imóveis ficam de fora."
           + (f" Até {fmt.data(INICIO_CIDADE_TODA - timedelta(days=1))} a coleta cobria só uns 30 bairros da região "
              "universitária: a linha pontilhada marca a semana em que ela passou a cobrir a cidade toda, e parte "
              "da mudança nessa semana vem disso." if mostra_mudanca_de_cobertura else ""))

# Com um bairro escolhido, ele fica em azul e a linha geral vira o contexto (cinza e tracejada,
# para não depender só da cor); sem bairro, a linha geral é a única série e fica em azul
series = [area] + ([bairro] if bairro else [])
cores = [COR_CONTEXTO, COR_SERIE] if bairro else [COR_SERIE]
tracos = [[6, 4], [1, 0]] if bairro else [[1, 0]]
legenda = alt.Legend(title=None, orient="top", symbolType="stroke", symbolStrokeWidth=2) if bairro else None
eixo_y = "R$ por dormitório por mês (mediana)" if medida == "custo_por_dormitorio" else "R$ por mês (mediana)"

base = alt.Chart(tendencia).encode(
    x=alt.X("semana:T", title=None, axis=alt.Axis(format="%b/%y", tickCount="month", grid=False)),
    y=alt.Y("mediana:Q", title=eixo_y, scale=alt.Scale(zero=False), axis=alt.Axis(format="$,.0f", tickCount=6)),
    color=alt.Color("serie:N", scale=alt.Scale(domain=series, range=cores), legend=legenda),
    strokeDash=alt.StrokeDash("serie:N", scale=alt.Scale(domain=series, range=tracos), legend=legenda),
)
linhas = base.mark_line(strokeWidth=2)

# Passar o mouse destaca a semana mais próxima: uma régua vertical com os números das séries
passar_mouse = alt.selection_point(fields=["semana"], nearest=True, on="pointerover", empty=False,
                                   clear="pointerout")
pontos = base.mark_circle(size=64, stroke="#1d293d", strokeWidth=2).encode(
    opacity=alt.condition(passar_mouse, alt.value(1), alt.value(0)))
largo = tendencia.pivot(index="semana", columns="serie", values=["mediana", "imoveis"])
largo.columns = [f"{valor}_{series.index(serie)}" for valor, serie in largo.columns]
dicas = [alt.Tooltip("semana:T", title="Semana de", format="%d/%m/%Y")]
for posicao, serie in enumerate(series):
    dicas += [alt.Tooltip(f"mediana_{posicao}:Q", title=f"{serie} (mediana)", format="$,.0f"),
              alt.Tooltip(f"imoveis_{posicao}:Q", title=f"{serie} (imóveis)")]
regua = (
    alt.Chart(largo.reset_index())
    .mark_rule(color=COR_CONTEXTO, strokeWidth=1)
    .encode(x="semana:T", opacity=alt.condition(passar_mouse, alt.value(1), alt.value(0)), tooltip=dicas)
    .add_params(passar_mouse)
)
camadas = [linhas, regua, pontos]
if mostra_mudanca_de_cobertura:
    marco = alt.Chart(pd.DataFrame({"semana": [pd.Timestamp(SEMANA_CIDADE_TODA)],
                                    "texto": ["coleta passa a cobrir a cidade toda"]}))
    camadas += [marco.mark_rule(color=COR_CONTEXTO, strokeDash=[2, 3]).encode(x="semana:T"),
                marco.mark_text(align="right", baseline="top", dx=-6, dy=4, color="#94a3b8", fontSize=12)
                .encode(x="semana:T", y=alt.value(0), text="texto:N")]
# A margem à direita deixa espaço para o último mês do eixo (no celular, ele era cortado)
st.altair_chart(alt.layer(*camadas).properties(height=380, padding={"right": 16}).configure(locale=LOCALE_BR),
                width="stretch")

with st.expander("Ver a tendência em uma tabela", icon=":material/table:"):
    colunas = {"semana": st.column_config.DateColumn("Semana de", format="DD/MM/YYYY")}
    for posicao, serie in enumerate(series):
        colunas[f"mediana_{posicao}"] = st.column_config.NumberColumn(f"{serie}: mediana (R$)", format="localized")
        colunas[f"imoveis_{posicao}"] = st.column_config.NumberColumn(f"{serie}: imóveis", format="%d")
    st.dataframe(largo.reset_index().sort_values("semana", ascending=False).round(), hide_index=True,
                 column_config=colunas, column_order=list(colunas))
