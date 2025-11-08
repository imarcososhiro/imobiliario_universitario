import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from scripts.tabulacao_de_dados import Dataset
from scripts.web_scraping import Scraper
from scripts.mapa import Criar_Mapa
from scripts.analises import Tirar_infos_bairros # Temporário

st.set_page_config(layout="wide") # Pra tirar as bordas brancas padrão da página

st.title('Imóveis de perfil universitário')
st.subheader('USP São Carlos - Campus I')

@st.cache_data # Comando para fazer o cache do banco de dados coletado e filtrado (para não ficar chamando a função varias vezes pra cada filtro)
def carregar_dados():
    dados_limpos = Dataset(Scraper())
    return dados_limpos

try:
    # Banco de dados principal
    df_principal = carregar_dados()
except:
    st.write('Por favor, deixe o scraper rodar para inicializar a aplicação. Tente novamente.')

# Função que exibe métricas de média, mediana e quantidade de apartamentos
def exibir_metricas(df_principal):
    # Criando métricas
    titulo_metrica1 = 'Média'
    media_geral = df_principal['Total / Mês'].mean()

    titulo_metrica2 = 'Quantidade de apartamentos'
    qtde_aps = df_principal['Total / Mês'].count()

    titulo_metrica3 = 'Mediana'
    mediana_geral = df_principal['Total / Mês'].median()

    titulo_metrica4 = 'Valor mínimo'
    valor_minimo = df_principal['Total / Mês'].min()

    titulo_metrica5 = 'Valor máximo'
    valor_maximo = df_principal['Total / Mês'].max()

    # Exibindo métricas em colunas
    col1,col2,col3 = st.columns(3)
    with col1:
        st.metric(titulo_metrica1, f'R$ {media_geral.round(2)}')
    with col2:
        st.metric(titulo_metrica2, qtde_aps)
    with col3:
        st.metric(titulo_metrica3, f'R$ {mediana_geral.round(2)}')

    col4,colvazia,col5 = st.columns(3)
    with col4:
        st.metric(titulo_metrica4, f'R$ {valor_minimo.round(2)}')
    with colvazia:
        st.write('')
    with col5:
        st.metric(titulo_metrica5, f'R$ {valor_maximo.round(2)}')


# Criando filtros
def exibir_slider_val(df_principal):
    range_min = df_principal['Total / Mês'].min()
    range_max = df_principal['Total / Mês'].max()
    intervalo = st.sidebar.slider('Selecione um intervalo',
                          range_min, range_max,
                          value=(range_min, range_max)
                          )
    return intervalo

def exibir_radio_dorm(df_principal):
    dormitorios = df_principal['Dormitórios'].unique()
    n_dormitorios = st.sidebar.segmented_control(
    "Número de dormitórios", sorted(dormitorios), selection_mode="multi"
    )
    return n_dormitorios

def exibir_opcoes_analise(df_principal):
    analise = st.sidebar.radio(
        "Filtrar cores por",
        ('Média de preço', 'Oferta de apartamentos')
    )
    if analise == 'Média de preço':
        analise = 'Media'
    elif analise == 'Oferta de apartamentos':
        analise = 'Quantidade'
    return analise

analise = exibir_opcoes_analise(df_principal)
n_dormitorios = exibir_radio_dorm(df_principal)
intervalo = exibir_slider_val(df_principal)

# Aplicando filtros no banco de dados e printando mapa
if len(n_dormitorios) > 0:
    df_principal = df_principal[(df_principal['Total / Mês'] <= intervalo[1]) & (df_principal['Total / Mês'] >= intervalo[0]) & (df_principal['Dormitórios'].isin(n_dormitorios))]
else:
    df_principal = df_principal[(df_principal['Total / Mês'] <= intervalo[1]) & (df_principal['Total / Mês'] >= intervalo[0])]

df_info = Tirar_infos_bairros(df_principal) # Métricas tiradas pelo filtro
mapa = Criar_Mapa(df_info, analise) # Criando mapa

# Estrutura try/except pra se não tiver apartamento com algum filtro, não dar erro

try:
    exibir_metricas(df_principal)
    mapa_st = st_folium(
            mapa,
            width=850,
            height=450,
            )

except:
    st.write('Não há apartamentos com esses filtros') #Vou mudar pra algo engraçadinho dps

