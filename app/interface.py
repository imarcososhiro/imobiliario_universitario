"""Peças da página: filtros, números do resumo, lista de bairros e os cartões dos imóveis."""
import html

import pandas as pd
import streamlit as st

from app import formatacao as fmt
from app.dados import DORMITORIOS_OU_MAIS, IMOBILIARIAS, Filtros
from app.historico import DIAS_NOVIDADE
from app.metricas import DO_LUGAR, MINIMO_IMOVEIS_BAIRRO

TIPOS = {"Tanto faz": None, "Apartamento": "Apartamento", "Casa": "Casa"}
# Quem estuda na UFSCar escolhe de onde medir a distância. Muita gente mora no centro, perto da
# rodoviária, e vai de ônibus (é de lá que saem as linhas para o campus); por isso ela vem primeiro.
PERTO_DA_UFSCAR = {"Rodoviária": ":material/directions_bus: Rodoviária", "UFSCar": ":material/school: UFSCar"}
# Distância do bairro até o lugar escolhido, em linha reta (km); None = qualquer distância
DISTANCIAS = {"A pé (até 1,5 km)": 1.5, "Até 3 km": 3.0, "Até 5 km": 5.0, "Qualquer distância": None}
SEM_LIMITE = "Sem limite"
PRECOS_POR_QUARTO = list(range(500, 3001, 100)) + [SEM_LIMITE]

# Estilo dos cartões e da lista de bairros. Fica aqui (e não no config.toml) porque o tema do
# Streamlit não tem como desenhar esses blocos, que são HTML próprio.
CSS = """
<style>
/* Menos espaço vazio no topo da página (o padrão do Streamlit é bem alto) */
[data-testid="stMainBlockContainer"] { padding-top: 2.5rem; }
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
    h1 { font-size: 2rem !important; }
}
.numeros { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
@media (max-width: 640px) { .numeros { grid-template-columns: 1fr 1fr; } }
.numero { display: flex; flex-direction: column; padding: 14px 16px; border-radius: 18px; background: #fff;
          border: 1px solid #e6e8f0; }
.numero b { font-size: 26px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; }
.numero span { font-weight: 600; font-size: 14px; }
.numero small { color: #5d6275; font-size: 12.5px; }
.cartoes { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 18px; }
.cartao {
    display: flex; flex-direction: column; overflow: hidden; border-radius: 20px; background: #fff;
    color: #171a26 !important; text-decoration: none !important; border: 1px solid #e6e8f0;
    box-shadow: 0 1px 2px rgba(23, 26, 38, .05); transition: transform .15s ease, box-shadow .15s ease;
}
.cartao:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(23, 26, 38, .12); }
.cartao .foto { position: relative; aspect-ratio: 4 / 3; background: #eceef4; }
.cartao .foto img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cartao .sem-foto { display: grid; place-items: center; height: 100%; color: #8a8fa3; font-size: 13px; }
.cartao .selos { position: absolute; top: 10px; left: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
.selo { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: #fff;
        box-shadow: 0 2px 6px rgba(23, 26, 38, .2); }
.selo.novo { background: #4f46e5; color: #fff; }
.selo.queda { background: #0b7a43; color: #fff; }
.selo.duplicata { background: #fff; color: #171a26; cursor: help; }
.cartao .detalhes span.imobiliaria { background: #eef0fe; color: #4f46e5; font-weight: 600; }
.cartao .corpo { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 4px; }
.cartao .preco { font-size: 24px; font-weight: 800; letter-spacing: -.02em; }
.cartao .preco small { font-size: 14px; font-weight: 600; color: #5d6275; letter-spacing: 0; }
.cartao .total { font-size: 13px; color: #5d6275; }
.cartao .total s { color: #8a8fa3; }
.cartao .titulo { margin-top: 6px; font-weight: 600; font-size: 14px; line-height: 1.35;
                  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cartao .lugar { font-size: 13px; color: #5d6275; }
.cartao .detalhes { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.cartao .detalhes span { padding: 3px 10px; border-radius: 999px; background: #f1f2f8; font-size: 12.5px; }
/* No celular, cartões deitados (foto à esquerda): cabem uns 3 por tela, em vez de 1 */
@media (max-width: 640px) {
    .cartoes { gap: 12px; }
    .cartao { flex-direction: row; border-radius: 16px; }
    .cartao .foto { flex: none; width: 38%; aspect-ratio: auto; min-height: 150px; }
    .cartao .corpo { padding: 10px 12px 12px; min-width: 0; gap: 2px; }
    .cartao .preco { font-size: 20px; }
    .cartao .preco small { font-size: 12.5px; }
    .cartao .titulo { margin-top: 4px; font-size: 13px; }
    .cartao .total, .cartao .lugar { font-size: 12px; }
    .cartao .detalhes { margin-top: 6px; gap: 4px; }
    .cartao .detalhes span { padding: 2px 8px; font-size: 11.5px; }
    .cartao .selos { top: 8px; left: 8px; flex-direction: column; align-items: flex-start; }
    .selo { font-size: 10.5px; padding: 3px 8px; }
}
.bairros { display: flex; flex-direction: column; gap: 8px; }
.bairro-linha { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 16px;
                background: #fff; border: 1px solid #e6e8f0; }
.bairro-linha .posicao { flex: none; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
                         background: #eef0fe; color: #4f46e5; font-weight: 800; font-size: 13px; }
.bairro-linha .nome { flex: 1; min-width: 0; font-weight: 600; font-size: 14px; }
.bairro-linha .nome small { display: block; font-weight: 400; color: #5d6275; font-size: 12.5px; }
.bairro-linha .valor { font-weight: 800; font-size: 16px; white-space: nowrap; }
.bairro-linha .valor small { font-weight: 500; color: #5d6275; font-size: 12px; }
.legenda { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12.5px; color: #5d6275; margin-top: 4px; }
.legenda span { display: inline-flex; align-items: center; gap: 6px; }
.legenda i { width: 14px; height: 14px; border-radius: 4px; display: inline-block; }
</style>
"""


def estilo() -> None:
    st.html(CSS)


def filtros() -> Filtros:
    """As perguntas do topo da página, do jeito que um estudante pensa na busca."""
    with st.container(border=True):
        campus, quartos, tipo, imobiliaria = st.columns([1.35, 1, 1.6, 1])
        estuda_na = campus.radio("Você estuda na", ["USP", "UFSCar"], horizontal=True, key="campus",
                                 help="A distância é medida até o Campus 1 da USP. Na UFSCar, você escolhe: "
                                      "até o campus ou até a rodoviária, de onde saem os ônibus")
        perto_de = estuda_na
        if estuda_na == "UFSCar":
            perto_de = campus.radio(
                "Quer morar perto da", list(PERTO_DA_UFSCAR), horizontal=True, key="perto_da_ufscar",
                format_func=PERTO_DA_UFSCAR.get,
                help="Muita gente da UFSCar mora no centro, perto da rodoviária, e vai de ônibus: é de lá que "
                     "saem as linhas para o campus. Quem prefere ir a pé escolhe a UFSCar")
        dormitorios = quartos.pills(
            "Quantos quartos?", list(range(1, DORMITORIOS_OU_MAIS + 1)), selection_mode="multi", key="quartos",
            format_func=lambda n: f"{n}+" if n == DORMITORIOS_OU_MAIS else str(n),
            help="Vai dividir com amigos? Conte um quarto para cada pessoa")
        escolha_tipo = tipo.radio("Tipo", list(TIPOS), horizontal=True, key="tipo")
        imobiliarias = imobiliaria.pills("Imobiliária", list(IMOBILIARIAS), selection_mode="multi",
                                         format_func=IMOBILIARIAS.get, key="imobiliarias",
                                         help="Nenhuma marcada: mostra os imóveis de todas")
        preco, distancia = st.columns(2)
        preco_max = preco.select_slider(
            "Até quanto por quarto?", PRECOS_POR_QUARTO, value=SEM_LIMITE, key="preco",
            format_func=lambda valor: valor if valor == SEM_LIMITE else fmt.reais(valor),
            help="Aluguel + condomínio + IPTU, dividido pelo número de quartos. Com um quarto para "
                 "cada pessoa, é quanto cada uma paga")
        # O rótulo muda com o lugar ("Quão perto da rodoviária?"), mas o filtro continua o mesmo: o que
        # identifica o widget é a key, então a distância escolhida não se perde
        distancia_max = distancia.select_slider(f"Quão perto {DO_LUGAR[perto_de]}?", list(DISTANCIAS),
                                                value="Até 3 km", key="distancia",
                                                help="Em linha reta, do bairro até lá (o site não informa o "
                                                     "endereço dos imóveis)")
    return Filtros(perto_de=perto_de, distancia_max_km=DISTANCIAS[distancia_max], tipo=TIPOS[escolha_tipo],
                   dormitorios=list(dormitorios or []),
                   preco_max_por_quarto=None if preco_max == SEM_LIMITE else float(preco_max),
                   imobiliarias=list(imobiliarias or []))


def numeros(df: pd.DataFrame, historico_carregado: bool) -> None:
    """Os números principais da busca, sem jargão: quantos imóveis, preço típico e as novidades.

    Em HTML (e não st.metric) para virarem uma grade 2 x 2 no celular, em vez de 4 blocos empilhados.
    """
    blocos = [
        (fmt.numero(len(df)), "imóveis pra você", f"em {df['bairro'].nunique()} bairros"),
        (fmt.reais(df["custo_por_dormitorio"].median()), "preço típico por quarto", "metade custa menos que isso"),
    ]
    if historico_carregado:
        blocos += [
            (fmt.numero(int(df["novo"].sum())), "novos esta semana", f"apareceram nos últimos {DIAS_NOVIDADE} dias"),
            (fmt.numero(int(df["total_anterior"].notna().sum())), "baixaram de preço",
             f"nos últimos {DIAS_NOVIDADE} dias"),
        ]
    st.html('<div class="numeros">' + "".join(
        f'<div class="numero"><b>{valor}</b><span>{rotulo}</span><small>{detalhe}</small></div>'
        for valor, rotulo, detalhe in blocos) + "</div>")
    if not historico_carregado:
        st.caption(":material/history: O histórico de preços não pôde ser carregado agora, por isso os "
                   "imóveis novos e as quedas de preço não aparecem. Recarregue a página mais tarde.")


def legenda_do_mapa(itens: list[tuple[str, str]]) -> None:
    faixas = "".join(f'<span><i style="background:{cor}"></i>{texto}</span>' for cor, texto in itens)
    st.html(f'<div class="legenda"><span><b>Preço típico por quarto:</b></span>{faixas}</div>')


def bairros_em_conta(resumo: pd.DataFrame, perto_de: str, quantidade: int = 6) -> None:
    """Os bairros com o menor preço típico por quarto (entre os que têm imóveis suficientes)."""
    candidatos = (resumo[resumo["imoveis"] >= MINIMO_IMOVEIS_BAIRRO].dropna(subset=["custo_por_dormitorio"])
                  .sort_values(["custo_por_dormitorio", "imoveis"], ascending=[True, False]).head(quantidade))
    if candidatos.empty:
        st.caption(f"Nenhum bairro tem {MINIMO_IMOVEIS_BAIRRO} imóveis com esses filtros.")
        return
    linhas = "".join(
        f'<div class="bairro-linha"><span class="posicao">{posicao}</span>'
        f'<div class="nome">{html.escape(linha["bairro"])}<small>{fmt.numero(linha["imoveis"])} imóveis · '
        f'{fmt.minutos_a_pe(linha["distancia_km"])} {DO_LUGAR[perto_de]}</small></div>'
        f'<span class="valor">{fmt.reais(linha["custo_por_dormitorio"])}<small>/quarto</small></span></div>'
        for posicao, (_, linha) in enumerate(candidatos.iterrows(), start=1))
    st.html(f'<div class="bairros">{linhas}</div>')


def _cartao(imovel: pd.Series, perto_de: str) -> str:
    """Um cartão em HTML. Tudo o que vem do site é escapado antes de entrar no HTML."""
    foto = imovel["foto_url"]
    if isinstance(foto, str) and foto.startswith("https://"):
        imagem = f'<img src="{html.escape(foto, quote=True)}" alt="" loading="lazy">'
    else:
        imagem = '<div class="sem-foto">sem foto</div>'
    selos = ""
    if imovel["novo"]:
        selos += '<span class="selo novo">Novo</span>'
    if pd.notna(imovel["total_anterior"]):
        selos += '<span class="selo queda">Baixou de preço</span>'
    if pd.notna(imovel["duplicata_de"]):
        outras = " e ".join(IMOBILIARIAS.get(fonte, fonte) for fonte in imovel["duplicata_de"].split(", "))
        selos += (f'<span class="selo duplicata" title="Outro anúncio com o mesmo bairro e nº de quartos, área '
                  f'e preço parecidos: pode ser o mesmo imóvel. Vale comparar.">Também na {outras}?</span>')
    if selos:
        selos = f'<div class="selos">{selos}</div>'

    if pd.notna(imovel["custo_por_dormitorio"]):
        preco = f'{fmt.reais(imovel["custo_por_dormitorio"])} <small>/quarto</small>'
        # A conta à vista: quem vai morar sozinho ou dividir o quarto refaz do seu jeito
        quartos = int(imovel["dormitorios"])
        if quartos > 1:
            total = f'{fmt.reais(imovel["total_mensal"])} por mês ÷ {quartos} quartos'
        else:
            total = "1 quarto: é o total do mês"
    else:  # sem nº de quartos não dá para dividir: mostra só o total
        preco, total = f'{fmt.reais(imovel["total_mensal"])} <small>/mês</small>', "total por mês"
    if pd.notna(imovel["total_anterior"]):
        total += f' · antes <s>{fmt.reais(imovel["total_anterior"])}</s>'

    titulo = imovel["titulo"] if isinstance(imovel["titulo"], str) else f"{imovel['subtipo']} em {imovel['bairro']}"
    detalhes = [imovel["tipo"]]  # o primeiro chip (a imobiliária) é montado à parte, com destaque
    if pd.notna(imovel["dormitorios"]):
        detalhes.append(f"{int(imovel['dormitorios'])} {'quarto' if imovel['dormitorios'] == 1 else 'quartos'}")
    if pd.notna(imovel["area_m2"]):
        detalhes.append(fmt.metros_quadrados(imovel["area_m2"]))
    lugar = html.escape(imovel["bairro"])
    if pd.notna(imovel["distancia_km"]):
        lugar += f" · {fmt.km(imovel['distancia_km'])} {DO_LUGAR[perto_de]} · {fmt.minutos_a_pe(imovel['distancia_km'])}"

    return (
        f'<a class="cartao" href="{html.escape(imovel["url"], quote=True)}" target="_blank" rel="noopener">'
        f'<div class="foto">{imagem}{selos}</div>'
        f'<div class="corpo"><div class="preco">{preco}</div><div class="total">{total}</div>'
        f'<div class="titulo">{html.escape(titulo)}</div><div class="lugar">{lugar}</div>'
        f'<div class="detalhes"><span class="imobiliaria">{IMOBILIARIAS.get(imovel["fonte"], imovel["fonte"])}</span>'
        f'{"".join(f"<span>{html.escape(str(d))}</span>" for d in detalhes)}</div>'
        "</div></a>"
    )


def cartoes(df: pd.DataFrame, perto_de: str) -> None:
    # Tudo numa linha só: no Markdown, uma linha em branco ou um recuo quebrariam o bloco de HTML
    st.markdown(f'<div class="cartoes">{"".join(_cartao(imovel, perto_de) for _, imovel in df.iterrows())}</div>',
                unsafe_allow_html=True)


def tabela_imoveis(df: pd.DataFrame) -> None:
    colunas = {
        "titulo": st.column_config.TextColumn("Anúncio", width="large"),
        "imobiliaria": st.column_config.TextColumn("Imobiliária"),
        "bairro": st.column_config.TextColumn("Bairro"),
        "custo_por_dormitorio": st.column_config.NumberColumn("Por quarto (R$)", format="localized"),
        "total_mensal": st.column_config.NumberColumn("Total por mês (R$)", format="localized"),
        "total_anterior": st.column_config.NumberColumn(
            "Antes da queda (R$)", format="localized",
            help=f"Total por mês antes da queda de preço, se ela aconteceu nos últimos {DIAS_NOVIDADE} dias"),
        "novo": st.column_config.CheckboxColumn("Novo", help=f"Apareceu no site nos últimos {DIAS_NOVIDADE} dias"),
        "dormitorios": st.column_config.NumberColumn("Quartos", format="%d"),
        "area_m2": st.column_config.NumberColumn("Área (m²)", format="%d"),
        "distancia_km": st.column_config.NumberColumn("Distância (km)", format="localized"),
        "subtipo": st.column_config.TextColumn("Tipo"),
        "aluguel": st.column_config.NumberColumn("Aluguel (R$)", format="localized"),
        "condominio": st.column_config.NumberColumn("Condomínio (R$)", format="localized"),
        "iptu": st.column_config.NumberColumn("IPTU (R$)", format="localized"),
        "duplicata_de": st.column_config.TextColumn(
            "Talvez também em", help="Outra imobiliária com um anúncio parecido (bairro, quartos, área e preço)"),
        "url": st.column_config.LinkColumn("Link", display_text="Ver anúncio"),
    }
    nomes = lambda fontes: ", ".join(IMOBILIARIAS.get(fonte, fonte) for fonte in fontes.split(", "))  # noqa: E731
    df = df.assign(imobiliaria=df["fonte"].map(IMOBILIARIAS).fillna(df["fonte"]),
                   duplicata_de=df["duplicata_de"].map(nomes, na_action="ignore"))
    tabela = df[list(colunas)].assign(custo_por_dormitorio=lambda t: t["custo_por_dormitorio"].round(),
                                      distancia_km=lambda t: t["distancia_km"].round(1))
    st.dataframe(tabela, hide_index=True, column_config=colunas)
