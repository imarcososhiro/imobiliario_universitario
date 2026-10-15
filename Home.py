import streamlit as st
from streamlit_folium import st_folium

from app import formatacao as fmt
from app.dados import aplicar_filtros, carregar_imoveis
from app.interface import (barra_lateral, destaque, grade_de_cartoes, indicadores, ranking_bairros,
                           tabela_imoveis)
from app.mapa import METRICAS_MAPA, PASTA_ASSETS, criar_mapa
from app.metricas import MINIMO_IMOVEIS_BAIRRO, escolher_campus, indice_custo_beneficio, resumo_por_bairro

st.set_page_config(page_title="Análise Imobiliária Universitária", page_icon=":material/home_work:", layout="wide")

TODOS = "Todos os bairros"
ALTURA_MAPA = 520
# Ordenação dos cartões: rótulo -> (coluna, crescente?)
ORDENACAO = {
    "Melhor custo-benefício": ("indice", False),
    "Menor custo por dormitório": ("custo_por_dormitorio", True),
    "Menor aluguel total": ("total_mensal", True),
    "Mais perto do campus": ("distancia_km", True),
    "Maior área": ("area_m2", False),
}

imoveis = carregar_imoveis()
escolhas = barra_lateral(imoveis)
df = escolher_campus(aplicar_filtros(imoveis, escolhas.filtros), escolhas.campus)
df = df.assign(indice=indice_custo_beneficio(df, escolhas.pesos))
resumo = resumo_por_bairro(df)

st.title(":material/query_stats: Análise imobiliária universitária")
st.caption(f"Aluguéis em São Carlos (SP) perto da USP e da UFSCar · atualizado em "
           f"{fmt.data(imoveis['coletado_em'].max())} · dados da imobiliária Cardinali")

if df.empty:
    st.info("Nenhum imóvel com esses filtros. Tente ampliar a faixa de preço, os dormitórios ou a área.")
    st.image(str(PASTA_ASSETS / "nopuedeser.jpg"), width=320)
    st.stop()

indicadores(df)
destaque(resumo)

with st.expander("Como ler este painel", icon=":material/help:"):
    st.markdown(f"""
- **Custo por dormitório**: total por mês (aluguel + condomínio + IPTU) dividido pelo nº de dormitórios. É quanto
  cada morador pagaria dividindo o imóvel, o jeito mais justo de comparar uma kitnet com uma casa de república.
- **Preço por m²**: total por mês dividido pela área. Mostra quanto espaço o dinheiro compra.
- **Distância**: em linha reta, do bairro até o campus escolhido na barra lateral. O site não informa o endereço
  dos imóveis, então todos os imóveis de um bairro têm a mesma distância.
- **Índice custo-benefício (0 a 100)**: compara os imóveis da tela entre si nos três critérios acima. Em cada
  um, o melhor imóvel ganha 100 e o pior, 0; o índice é a média, com os pesos que você escolher na barra
  lateral. Por isso ele muda quando você muda os filtros.
- No mapa e no ranking, cada bairro mostra a **mediana** dos seus imóveis, que não se deixa levar por um
  anúncio fora da curva.
""")

coluna_mapa, coluna_ranking = st.columns([3, 2], gap="large")
with coluna_mapa:
    metrica = st.radio("Pintar os bairros por", list(METRICAS_MAPA), horizontal=True,
                       format_func=lambda m: METRICAS_MAPA[m].rotulo, key="metrica_mapa")
    mapa = criar_mapa(resumo, metrica, escolhas.distancia_ate,
                      ver_cidade_toda=not escolhas.filtros.so_regiao_universitaria)
    retorno = st_folium(mapa, key="mapa", height=ALTURA_MAPA, use_container_width=True,
                        returned_objects=["last_active_drawing"])
    st.caption(f"Cor de cada bairro: mediana dos imóveis, {METRICAS_MAPA[metrica].leitura}. "
               "Passe o mouse num bairro para ver os números; clique para ver os imóveis dele logo abaixo.")
with coluna_ranking:
    st.subheader("Bairros com melhor custo-benefício")
    st.caption(f"Bairros com pelo menos {MINIMO_IMOVEIS_BAIRRO} imóveis; valores são a mediana do bairro.")
    ranking_bairros(resumo, altura=ALTURA_MAPA)

# Clicar num bairro do mapa seleciona o bairro na lista de imóveis. O mapa devolve o último
# bairro clicado em toda execução, então só um clique novo muda a seleção.
clicado = ((retorno or {}).get("last_active_drawing") or {}).get("properties", {}).get("bairro")
if clicado and clicado != st.session_state.get("ultimo_bairro_clicado"):
    st.session_state["ultimo_bairro_clicado"] = clicado
    st.session_state["bairro"] = clicado

st.header("Imóveis", anchor="imoveis")
bairros = [TODOS] + sorted(df["bairro"].unique())
if st.session_state.get("bairro") not in bairros:
    st.session_state["bairro"] = TODOS
coluna_bairro, coluna_ordem, coluna_quantidade = st.columns([2, 2, 1])
bairro = coluna_bairro.selectbox("Bairro", bairros, key="bairro")
ordem = coluna_ordem.selectbox("Ordenar por", list(ORDENACAO), key="ordem")
quantidade = coluna_quantidade.radio("Mostrar", [12, 24, 48], horizontal=True, key="quantidade")

selecao = df if bairro == TODOS else df[df["bairro"] == bairro]
coluna, crescente = ORDENACAO[ordem]
selecao = selecao.sort_values([coluna, "total_mensal"], ascending=[crescente, True], na_position="last")
st.caption(f"{fmt.numero(len(selecao))} imóveis" + ("" if bairro == TODOS else f" em {bairro}")
           + (f" · mostrando os {quantidade} primeiros" if len(selecao) > quantidade else ""))
grade_de_cartoes(selecao.head(quantidade), escolhas.distancia_ate)

with st.expander(f"Ver todos os {fmt.numero(len(selecao))} imóveis em uma tabela", icon=":material/table:"):
    tabela_imoveis(selecao)

st.divider()
st.caption("Projeto acadêmico, sem vínculo com a imobiliária. Código e dados: "
           "[github.com/imarcososhiro/imobiliario_universitario](https://github.com/imarcososhiro/imobiliario_universitario)")
