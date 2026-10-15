"""Peças da interface usadas pelas páginas do dashboard."""
import html
import re
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from app import formatacao as fmt
from app.dados import DORMITORIOS_OU_MAIS, Filtros
from app.historico import DIAS_NOVIDADE
from app.metricas import CRITERIOS, MINIMO_IMOVEIS_BAIRRO, QUALQUER_CAMPUS

OPCOES_CAMPUS = {"USP": "USP (Campus 1)", "UFSCar": "UFSCar", QUALQUER_CAMPUS: "Tanto faz (o mais perto)"}
DISTANCIA_ATE = {"USP": "da USP", "UFSCar": "da UFSCar", QUALQUER_CAMPUS: "do campus mais perto"}
IMPORTANCIA = {"Não importa": 0.0, "Pouco": 0.5, "Normal": 1.0, "Muito": 2.0}
AREAS = ("Região universitária", "Cidade toda")


@dataclass
class Escolhas:
    campus: str
    filtros: Filtros
    pesos: dict[str, float]

    @property
    def distancia_ate(self) -> str:
        return DISTANCIA_ATE[self.campus]


def escapar(texto: str) -> str:
    """Escapa caracteres que o Markdown do Streamlit interpretaria (*, _, #, :emoji:, $...$)."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~$:])", r"\\\1", texto)


def barra_lateral(imoveis: pd.DataFrame) -> Escolhas:
    with st.sidebar:
        campus = st.radio("Onde você estuda?", list(OPCOES_CAMPUS), format_func=OPCOES_CAMPUS.get, key="campus",
                          help="Usado para medir a distância de cada bairro até o campus")
        area = st.radio("Área", AREAS, key="area",
                        help="Região universitária: bairros que chegam a até 2,2 km da USP ou da UFSCar")
        tipo = st.radio("Tipo de imóvel", ["Todos", "Apartamento", "Casa"], horizontal=True, key="tipo")
        dormitorios = st.segmented_control(
            "Dormitórios", list(range(1, DORMITORIOS_OU_MAIS + 1)), selection_mode="multi", key="dormitorios",
            format_func=lambda n: f"{n}+" if n == DORMITORIOS_OU_MAIS else str(n))
        minimo, maximo = int(imoveis["total_mensal"].min()), int(imoveis["total_mensal"].max()) + 1
        faixa = st.slider("Aluguel total por mês", minimo, maximo, (minimo, maximo), step=50, format="R$ %d",
                          key="faixa", help="Aluguel + condomínio + IPTU")
        reservados = st.toggle("Incluir imóveis reservados", key="reservados",
                               help="Reservados já têm alguém negociando, mas ainda aparecem no site")
        with st.expander("Ajustar o índice de custo-benefício"):
            st.caption("Quanto cada critério pesa para você?")
            pesos = {criterio: IMPORTANCIA[st.select_slider(rotulo, list(IMPORTANCIA), value="Normal",
                                                            key=f"peso_{criterio}")]
                     for criterio, rotulo in CRITERIOS.items()}

    filtros = Filtros(so_regiao_universitaria=area == AREAS[0], incluir_reservados=reservados,
                      tipo=None if tipo == "Todos" else tipo,
                      dormitorios=list(dormitorios or []), faixa_total=faixa)
    return Escolhas(campus, filtros, pesos)


def indicadores(df: pd.DataFrame) -> None:
    """Números principais da seleção atual: medianas, para um anúncio fora da curva não distorcer."""
    colunas = st.columns(4)
    colunas[0].metric("Imóveis encontrados", fmt.numero(len(df)), border=True,
                      help=f"Em {df['bairro'].nunique()} bairros")
    colunas[1].metric("Aluguel total (mediana)", fmt.reais(df["total_mensal"].median()), border=True,
                      help="Aluguel + condomínio + IPTU, por mês")
    colunas[2].metric("Por dormitório (mediana)", fmt.reais(df["custo_por_dormitorio"].median()), border=True,
                      help="Total por mês dividido pelo nº de dormitórios: quanto cada morador pagaria")
    colunas[3].metric("Preço por m² (mediana)", fmt.reais(df["preco_m2"].median()), border=True,
                      help="Total por mês dividido pela área do imóvel")


def destaque(resumo: pd.DataFrame) -> None:
    """Uma frase com o bairro de melhor custo-benefício (entre os que têm opções suficientes)."""
    candidatos = resumo[resumo["imoveis"] >= MINIMO_IMOVEIS_BAIRRO].dropna(subset=["indice"])
    if candidatos.empty:
        return
    melhor = candidatos.sort_values(["indice", "imoveis"], ascending=False).iloc[0]
    st.markdown(
        f":material/lightbulb: Melhor custo-benefício: **{escapar(melhor['bairro'])}**, com índice "
        f"{fmt.numero(melhor['indice'])} e {fmt.reais(melhor['custo_por_dormitorio'])} por dormitório "
        f"(mediana de {fmt.numero(melhor['imoveis'])} imóveis)")


def novidades(df: pd.DataFrame, historico_carregado: bool) -> None:
    """Uma frase com quantos imóveis da seleção são novos ou baixaram de preço na última semana."""
    if not historico_carregado:
        st.caption(":material/history: O histórico de preços não pôde ser carregado agora, por isso os "
                   "imóveis novos e as quedas de preço não aparecem. Recarregue a página mais tarde.")
        return
    novos, baixaram = int(df["novo"].sum()), int(df["total_anterior"].notna().sum())
    if novos == 0:
        texto = "Nenhum imóvel novo esta semana"
    else:
        texto = f"**{fmt.numero(novos)} {'imóvel novo' if novos == 1 else 'imóveis novos'}** esta semana"
    if baixaram:
        texto += f" · {fmt.numero(baixaram)} {'baixou' if baixaram == 1 else 'baixaram'} de preço"
    st.markdown(f":material/new_releases: {texto}", help=(
        f"**Novo**: apareceu no site nos últimos {DIAS_NOVIDADE} dias. **Baixou de preço**: o total por mês "
        f"caiu nos últimos {DIAS_NOVIDADE} dias. Para vê-los no topo da lista, ordene os imóveis por "
        "\"Novidades primeiro\"."))


def ranking_bairros(resumo: pd.DataFrame, altura: int, completo: bool = False) -> None:
    """Bairros do melhor para o pior índice.

    A versão compacta (ao lado do mapa) mostra só os bairros com imóveis suficientes e três
    colunas; a completa mostra todos os bairros e todas as colunas.
    """
    colunas = ["bairro", "imoveis", "custo_por_dormitorio", "distancia_km", "indice"]
    if not completo:
        resumo = resumo[resumo["imoveis"] >= MINIMO_IMOVEIS_BAIRRO]
        colunas = ["bairro", "custo_por_dormitorio", "indice"]
    tabela = (resumo.sort_values(["indice", "imoveis"], ascending=False)
              .assign(custo_por_dormitorio=lambda t: t["custo_por_dormitorio"].round(),
                      distancia_km=lambda t: t["distancia_km"].round(1))[colunas])
    st.dataframe(tabela, hide_index=True, height=altura, column_config={
        "bairro": st.column_config.TextColumn("Bairro", width="medium"),
        "imoveis": st.column_config.NumberColumn("Imóveis", format="%d", width="small"),
        "custo_por_dormitorio": st.column_config.NumberColumn("R$/dorm.", format="localized", width="small",
                                                              help="Custo por dormitório (mediana)"),
        "distancia_km": st.column_config.NumberColumn("km", format="localized", width="small",
                                                      help="Distância até o campus escolhido"),
        "indice": st.column_config.ProgressColumn("Índice", min_value=0, max_value=100, format="%d",
                                                  width="small"),
    })


def cartao_imovel(imovel: pd.Series, distancia_ate: str) -> None:
    with st.container(border=True):
        if isinstance(imovel["foto_url"], str) and imovel["foto_url"].startswith("https://"):
            # Altura fixa com recorte (object-fit): fotos em pé ou deitadas não desalinham os cartões.
            # O endereço vem do site, então é escapado antes de entrar no HTML.
            st.markdown(f'<img src="{html.escape(imovel["foto_url"], quote=True)}" alt="" loading="lazy" '
                        'style="width:100%;height:180px;object-fit:cover;border-radius:6px">',
                        unsafe_allow_html=True)
        selos = []
        if imovel["novo"]:
            selos.append(":violet-badge[:material/new_releases: Novo]")
        if pd.notna(imovel["total_anterior"]):
            selos.append(":green-badge[:material/trending_down: Baixou de preço]")
        if selos:
            st.markdown(" ".join(selos))
        titulo = imovel["titulo"] if isinstance(imovel["titulo"], str) else f"{imovel['tipo']} em {imovel['bairro']}"
        st.markdown(f"**{escapar(titulo)}**")
        st.caption(f"{imovel['subtipo']} · {imovel['bairro']}")
        # Com dois "R$" na mesma linha, o Markdown leria o trecho entre eles como fórmula: daí o escapar()
        preco = f"{escapar(fmt.reais(imovel['total_mensal']))} /mês"
        if pd.notna(imovel["total_anterior"]):
            preco += f" :small[:gray[~~{escapar(fmt.reais(imovel['total_anterior']))}~~]]"  # o valor de antes, riscado
        st.markdown(f"#### {preco}")

        detalhes = [f"{fmt.reais(imovel['custo_por_dormitorio'])} por dormitório"]
        if pd.notna(imovel["dormitorios"]):
            detalhes.append(f"{int(imovel['dormitorios'])} dorm.")
        if pd.notna(imovel["area_m2"]):
            detalhes.append(fmt.metros_quadrados(imovel["area_m2"]))
        st.markdown(" · ".join(detalhes))
        st.markdown(f"{fmt.km(imovel['distancia_km'])} {distancia_ate} · "
                    f":blue-badge[Índice {fmt.numero(imovel['indice'])}]")
        st.link_button("Ver anúncio", imovel["url"], width="stretch", icon=":material/open_in_new:")


def grade_de_cartoes(df: pd.DataFrame, distancia_ate: str, colunas: int = 3) -> None:
    for inicio in range(0, len(df), colunas):
        for coluna, (_, imovel) in zip(st.columns(colunas), df.iloc[inicio:inicio + colunas].iterrows()):
            with coluna:
                cartao_imovel(imovel, distancia_ate)


def tabela_imoveis(df: pd.DataFrame) -> None:
    colunas = {
        "titulo": st.column_config.TextColumn("Anúncio", width="large"),
        "bairro": st.column_config.TextColumn("Bairro"),
        "subtipo": st.column_config.TextColumn("Tipo"),
        "total_mensal": st.column_config.NumberColumn("Total/mês (R$)", format="localized"),
        "total_anterior": st.column_config.NumberColumn(
            "Antes da queda (R$)", format="localized",
            help=f"Total por mês antes da queda de preço, se ela aconteceu nos últimos {DIAS_NOVIDADE} dias"),
        "novo": st.column_config.CheckboxColumn("Novo", help=f"Apareceu no site nos últimos {DIAS_NOVIDADE} dias"),
        "custo_por_dormitorio": st.column_config.NumberColumn("Por dormitório (R$)", format="localized"),
        "dormitorios": st.column_config.NumberColumn("Dorm.", format="%d"),
        "area_m2": st.column_config.NumberColumn("Área (m²)", format="%d"),
        "preco_m2": st.column_config.NumberColumn("R$/m²", format="localized"),
        "distancia_km": st.column_config.NumberColumn("Distância (km)", format="localized"),
        "indice": st.column_config.ProgressColumn("Índice", min_value=0, max_value=100, format="%d"),
        "aluguel": st.column_config.NumberColumn("Aluguel (R$)", format="localized"),
        "condominio": st.column_config.NumberColumn("Condomínio (R$)", format="localized"),
        "iptu": st.column_config.NumberColumn("IPTU (R$)", format="localized"),
        "url": st.column_config.LinkColumn("Link", display_text="Ver anúncio"),
    }
    tabela = df[list(colunas)].assign(
        custo_por_dormitorio=lambda t: t["custo_por_dormitorio"].round(),
        preco_m2=lambda t: t["preco_m2"].round(1),
        distancia_km=lambda t: t["distancia_km"].round(1))
    st.dataframe(tabela, hide_index=True, column_config=colunas)
