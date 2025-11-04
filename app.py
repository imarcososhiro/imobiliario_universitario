import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from scripts.tabulacao_de_dados import Dataset
from scripts.web_scraping import Scraper
from scripts.mapa import Criar_Mapa
from scripts.analises_formatacao import Tirar_infos_bairros # Temporário

# Esse script vai fazer o web app, receber os filtros do usuário, e filtrar
# o banco de dados conforme eles.
# No app, o usuário vai começar a filtrar os dados que ele quer visualizar:
# primeiro por nº de dormitórios, depois por range de valor, e depois vai
# escolher qual das análises ele quer ver: Média/Oferta/Valor mín ou máx por bairro.
# Depois, esse script vai filtrar o banco de dados conforme esses filtros e
# enviar pro script mapa.py, pra ele criar o mapa baseado nessas informações.
# O mapa.py retorna o mapa criado pra cá, e ele é plotado no app

st.set_page_config(layout="wide") # Pra tirar as bordas brancas padrão da página

@st.cache_data # Comando para fazer o cache do banco de dados coletado e filtrado (para não ficar chamando a função varias vezes pra cada filtro)
def carregar_dados():
    dados_limpos = Dataset(Scraper())
    return dados_limpos

st.title('Análise imobiliária no contexto universitário - São Carlos/SP')
df_principal = carregar_dados()

df_infos = Tirar_infos_bairros(df_principal)

# Como esse script ainda não está recebendo nenhum filtro pelo usuário, coloquei dados teste na função Criar_Mapa só
# para testar o plot

mapa = Criar_Mapa(df_infos)

st_folium(
        mapa,
        width='50%',
        height=750,
    )

