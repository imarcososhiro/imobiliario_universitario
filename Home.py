from pathlib import Path

import streamlit as st
from streamlit_folium import st_folium

from app import formatacao as fmt
from app.dados import aplicar_filtros, carregar_imoveis
from app.historico import carregar_historico, marcar_novidades
from app.interface import (bairros_em_conta, cartoes, estilo, filtros, legenda_do_mapa, numeros,
                           tabela_imoveis)
from app.mapa import criar_mapa, faixas_de_preco, legenda
from app.metricas import resumo_por_bairro

st.set_page_config(page_title="Onde morar em São Carlos", page_icon=":material/home:", layout="wide")
estilo()

PASTA_ASSETS = Path(__file__).resolve().parent / "assets"
ALTURA_MAPA = 460
POR_PAGINA = 12
# Ordem dos cartões: rótulo -> (coluna, crescente?)
ORDENACAO = {
    "Menor preço por quarto": ("custo_por_dormitorio", True),
    "Menor aluguel total": ("total_mensal", True),
    "Mais perto": ("distancia_km", True),
    "Novidades primeiro": ("novidade", False),  # novos ou que baixaram de preço na última semana
    "Mais espaço": ("area_m2", False),
}

historico = carregar_historico()  # None se não der para baixar agora: a página funciona sem ele
imoveis = marcar_novidades(carregar_imoveis(), historico)

st.title("Bora achar um lugar pra morar?")
st.markdown(f"Os aluguéis de São Carlos perto da **USP** e da **UFSCar**, num lugar só. "
            f"Atualizado todo dia (o último foi em {fmt.data(imoveis['coletado_em'].max())}), "
            "com os anúncios das imobiliárias Cardinali e Roca.")

escolhas = filtros()
df = aplicar_filtros(imoveis, escolhas)

if df.empty:
    st.info("Nenhum imóvel com esses filtros. Que tal aumentar a distância, o preço ou os quartos?",
            icon=":material/search_off:")
    st.image(str(PASTA_ASSETS / "nopuedeser.jpg"), width=320)
    st.stop()

numeros(df, historico_carregado=historico is not None)
resumo = resumo_por_bairro(df)

# --- Mapa e bairros mais em conta ----------------------------------------------------------
st.header("Onde ficam", anchor="mapa")
coluna_mapa, coluna_bairros = st.columns([3, 2], gap="medium")
with coluna_mapa:
    retorno = st_folium(criar_mapa(resumo, escolhas.perto_de, escolhas.distancia_max_km), key="mapa",
                        height=ALTURA_MAPA, use_container_width=True, returned_objects=["last_active_drawing"])
    legenda_do_mapa(legenda(faixas_de_preco(resumo["custo_por_dormitorio"])))
    st.caption("Toque ou clique num bairro para ver os imóveis dele logo abaixo.")
with coluna_bairros:
    st.subheader("Bairros mais em conta")
    bairros_em_conta(resumo, escolhas.perto_de)

# Clicar num bairro do mapa seleciona o bairro na lista de imóveis. O mapa devolve o último
# bairro clicado em toda execução, então só um clique novo muda a seleção.
clicado = ((retorno or {}).get("last_active_drawing") or {}).get("properties", {}).get("bairro")
if clicado and clicado != st.session_state.get("ultimo_bairro_clicado"):
    st.session_state["ultimo_bairro_clicado"] = clicado
    st.session_state["bairro"] = clicado

# --- Imóveis -------------------------------------------------------------------------------
bairros = sorted(df["bairro"].unique())
if st.session_state.get("bairro") not in bairros:
    st.session_state["bairro"] = None  # nenhum bairro escolhido = todos
st.header("Imóveis", anchor="imoveis")
coluna_bairro, coluna_ordem = st.columns(2)
# Sem bairro escolhido, a caixa mostra o texto de exemplo (placeholder), que some quando a
# pessoa começa a digitar. Com "Todos os bairros" como uma opção de verdade, o texto ficava lá.
bairro = coluna_bairro.selectbox("Bairro", bairros, index=None, key="bairro",
                                 placeholder="Todos os bairros (digite para buscar)")
ordem = coluna_ordem.selectbox("Ordenar por", list(ORDENACAO), key="ordem")

selecao = df if bairro is None else df[df["bairro"] == bairro]
coluna, crescente = ORDENACAO[ordem]
selecao = selecao.sort_values([coluna, "custo_por_dormitorio"], ascending=[crescente, True], na_position="last")
quantidade = st.session_state.setdefault("quantidade", POR_PAGINA)
st.caption(f"{fmt.numero(len(selecao))} {'imóvel' if len(selecao) == 1 else 'imóveis'}"
           + ("" if bairro is None else f" em {bairro}"))
cartoes(selecao.head(quantidade), escolhas.perto_de)
if len(selecao) > quantidade:
    st.button(f"Mostrar mais {min(POR_PAGINA, len(selecao) - quantidade)}", key="mostrar_mais", width="stretch",
              icon=":material/expand_more:",
              on_click=lambda: st.session_state.update(quantidade=quantidade + POR_PAGINA))

with st.expander(f"Ver todos os {fmt.numero(len(selecao))} em uma tabela", icon=":material/table:"):
    tabela_imoveis(selecao)

with st.expander("Como funciona", icon=":material/help:"):
    st.markdown(f"""
- **Preço por quarto**: o total do mês (aluguel + condomínio + IPTU) dividido pelo número de quartos. Se cada
  pessoa ficar com um quarto, é quanto cada uma paga, então dá para comparar uma kitnet com uma casa de república.
  Kitnet sem o número de quartos no anúncio conta como 1 quarto.
- **Preço típico**: a mediana. Metade dos imóveis custa menos que isso, metade custa mais. Diferente da média,
  ela não se deixa levar por um anúncio caríssimo.
- **Distância**: em linha reta, do bairro até o campus (ou a rodoviária). O site não informa o endereço, então
  todos os imóveis de um bairro aparecem com a mesma distância. O tempo a pé soma 30% ao caminho, porque as ruas
  fazem curvas.
- **Rodoviária**: muita gente da UFSCar mora no centro e vai de ônibus, que sai da rodoviária. Por isso, quem
  estuda na UFSCar escolhe se a distância é até a rodoviária ou até o campus.
- **Novo** e **Baixou de preço**: comparando com as coletas dos últimos dias (os sites são lidos todo dia).
  Imóveis reservados ficam de fora.
- **Também na outra imobiliária?**: o mesmo bairro e nº de quartos, com área e preço parecidos, aparece nas
  duas. Pode ser o mesmo imóvel anunciado duas vezes (às vezes com preços diferentes), então vale comparar.
""")

st.divider()
st.caption("Projeto acadêmico, sem vínculo com as imobiliárias. Código e dados: "
           "[github.com/imarcososhiro/imobiliario_universitario](https://github.com/imarcososhiro/imobiliario_universitario)")
