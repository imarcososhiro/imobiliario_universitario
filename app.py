import streamlit as st
import pandas as pd
from scripts.tabulacao_de_dados import Dataset
from scripts.web_scraping import Scraper


@st.cache_data # Comando para fazer o cache do banco de dados coletado e filtrado (para não ficar chamando a função varias vezes pra cada filtro)
def carregar_dados():
    dados_limpos = Dataset(Scraper())
    return dados_limpos

st.title('Análise imobiliária no contexto universitário - São Carlos/SP')
df_principal = carregar_dados()

df_principal
