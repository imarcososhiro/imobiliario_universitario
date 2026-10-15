# Carrega o CSV gerado pelo scraper e deixa no formato que o dashboard usa
import os
import pandas as pd
from app.coord_bairros import Buscar_coords, Nome_padrao

CAMINHO_CSV = os.path.join(os.path.dirname(__file__), '..', 'dados', 'imoveis.csv')
VALOR_MAXIMO = 8000 # Teto do projeto para o valor total (aluguel + condomínio + IPTU)

# Colunas do CSV -> nomes exibidos no dashboard
COLUNAS_EXIBICAO = {
    'bairro': 'Bairro',
    'tipo': 'Tipo',
    'url': 'Link',
    'aluguel': 'Aluguel Cheio',
    'aluguel_bonificado': 'Aluguel com Bonificação',
    'condominio': 'Condomínio',
    'iptu': 'IPTU',
    'total_mensal': 'Total / Mês',
    'dormitorios': 'Dormitórios',
    'banheiros': 'Banheiros',
    'vagas': 'Garagens',
    'suites': 'Suítes',
}

# Kitnets e studios às vezes vêm sem nº de dormitórios no site, mas têm um cômodo
SUBTIPOS_DE_UM_DORMITORIO = 'kitchnet|kitnet|studio|flat'

def Carregar_imoveis(caminho=CAMINHO_CSV):
    df = pd.read_csv(caminho)

    # O scraper coleta a cidade toda; por enquanto o mapa mostra só a região
    # universitária, que são os bairros com coordenada cadastrada
    na_regiao = df['bairro'].map(lambda bairro: Buscar_coords(bairro) is not None)
    # Sem total (aluguel "Consulte-nos") não dá pra comparar preço
    com_total = df['total_mensal'].notna() & (df['total_mensal'] <= VALOR_MAXIMO)
    df = df[na_regiao & com_total].copy()

    df['bairro'] = df['bairro'].map(Nome_padrao)
    um_comodo = df['subtipo'].str.lower().str.contains(SUBTIPOS_DE_UM_DORMITORIO, na=False)
    df.loc[um_comodo & df['dormitorios'].isna(), 'dormitorios'] = 1

    return df.rename(columns=COLUNAS_EXIBICAO)
