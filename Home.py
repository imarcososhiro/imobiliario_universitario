import streamlit as st
import streamlit_folium
import pandas as pd
from scripts.tabulacao_de_dados import Dataset
from scripts.web_scraping import Scraper
from scripts.mapa import Criar_Mapa
from scripts.analises import Tirar_infos_bairros # Temporário
import os
from datetime import datetime

st.set_page_config(layout="wide") # Pra tirar as bordas brancas padrão da página

st.title('Imóveis de perfil universitário')
st.subheader('São Carlos - SP')

#O programa sempre vai ler os dados do arquivo csv
df_principal = pd.read_csv('dados.csv')

#Puxando a data da ultima modificação do csv
timestamp = os.path.getmtime('dados.csv')
ultima_modificacao = datetime.fromtimestamp(timestamp)

st.write(f'Ultima atualização dos dados: {ultima_modificacao.strftime('%d/%m/%Y %H:%M:%S')}')

#Cria o botão para o user atualizar o banco de dados
botao_scrap = st.button('Atualizar o banco de dados', type='primary')


# Se o user apertar o botão, o scraper é chamado, e os dados são atualizados, e o csv antigo é substituido
if botao_scrap:
    st.write('⏳ Rodando o Scraper... isso pode levar em torno de 5 minutos.')
    st.write('•   Você pode utilizar o dashboard enquanto isso. Verifique o andamento da atualização no seu terminal.')
    df_principal = Dataset(Scraper())
    df_principal.to_csv('dados.csv', index=False)

# Função que exibe métricas de média, mediana e quantidade de apartamentos
def exibir_metricas(df_filtrado):
    # Criando métricas
    titulo_metrica1 = 'Média geral'
    media_geral = df_filtrado['Total / Mês'].mean()

    titulo_metrica2 = 'Quantidade de apartamentos'
    qtde_aps = df_filtrado['Total / Mês'].count()

    titulo_metrica3 = 'Mediana geral'
    mediana_geral = df_filtrado['Total / Mês'].median()

    titulo_metrica4 = 'Valor mínimo'
    valor_minimo = df_filtrado['Total / Mês'].min()

    titulo_metrica5 = 'Valor máximo'
    valor_maximo = df_filtrado['Total / Mês'].max()

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
# Exibe o layout de filtro de preço, e recebe o filtro do usuário
def Intervalo_Slider():
    range_min = df_principal['Total / Mês'].min()
    range_max = df_principal['Total / Mês'].max()
    range_slider = (st.sidebar.slider('Selecione um intervalo',
                    range_min, range_max,
                    value=(range_min, range_max)
                    ))
    return range_slider

# Exibe o layout de filtro de dormitórios, e recebe o filtro do usuário
def Dormitorios_num():
    dormitorios = df_principal['Dormitórios'].unique()
    numero_dormitorios = st.sidebar.segmented_control(
    "Número de dormitórios", sorted(dormitorios), selection_mode="multi"
    )
    return numero_dormitorios

# Exibe o layout de filtro de análise, e recebe o filtro do usuário
def Analise_Escolhida():
    analise_escolhida = st.sidebar.radio(
        "Filtrar cores por",
        ('Média de preço', 'Oferta de apartamentos')
    )
    if analise_escolhida == 'Média de preço':
        analise_escolhida = 'Media' #nome da coluna que existe no df
    elif analise_escolhida == 'Oferta de apartamentos':
        analise_escolhida = 'Quantidade' #nome da coluna que existe no df
    return analise_escolhida

# Layout da exibição da tabela com a listagem dos apartamentos por bairro
def exibir_tabelas_bairros(df_filtro,opcao):
    # Exibir nada inicialmente
    if opcao == 'Todos':
        return df_filtro[['Bairro','Link','Total / Mês','Aluguel com Bonificação','Condomínio','IPTU','Dormitórios','Aluguel Cheio']].sort_values(by='Total / Mês')
    else:
        filtro = df_filtro[df_filtro['Bairro'] == opcao] #Listar dados só do bairro escolhido
        st.write("Dados dos apartamentos em:", opcao)
        return filtro[['Link','Total / Mês','Aluguel com Bonificação','Condomínio','IPTU','Dormitórios','Aluguel Cheio']].sort_values(by='Total / Mês')

analise = Analise_Escolhida()
n_dormitorios = Dormitorios_num()
intervalo = Intervalo_Slider()

# Aplicando filtros no banco de dados e printando mapa

# Se tiver filtro de dormitório, filtra por preço e dormitório
if len(n_dormitorios) > 0:
    df_filtrado = df_principal[(df_principal['Total / Mês'] <= intervalo[1]) & (df_principal['Total / Mês'] >= intervalo[0]) & (df_principal['Dormitórios'].isin(n_dormitorios))]
# Se não tiver, filtra só por preço
else:
    df_filtrado = df_principal[(df_principal['Total / Mês'] <= intervalo[1]) & (df_principal['Total / Mês'] >= intervalo[0])]

df_info = Tirar_infos_bairros(df_filtrado) # Produz um dataframe de métricas gerais (Média, mediana, valor mín, max, etc), conforme o filtro aplicado pelo usuário
mapa = Criar_Mapa(df_info, analise) # Cria o mapa a partir dessas métricas

# Estruturas try/except pra se não tiver apartamento com algum filtro, não imprimir erro
try:
    # Exibir as métricas e o mapa gerado, conforme os filtros
    exibir_metricas(df_filtrado)
    mapa_st = streamlit_folium.st_folium(
            mapa,
            width=850,
            height=450,
            )

except:
    st.write('Sem apartamentos')

#Select box com todos os bairros no mapa
opcoes = st.selectbox(
        'Selecione o bairro',
        ['Todos'] + sorted(df_filtrado['Bairro'].unique())
    )

# Exibir o dataframe com especificações de todos os apartamentos, por bairro, com link
st.subheader('Detalhamento')

# column_config pra fazer a URL virar hiperlink,
# display_text pra encurtar a URL
st.dataframe(
    exibir_tabelas_bairros(df_filtrado, opcoes),
    hide_index=True,
    column_config={
        'Link': st.column_config.LinkColumn('Link',
        display_text='Ver Anúncio')
    })











