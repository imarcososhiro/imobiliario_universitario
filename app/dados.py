# Carrega o CSV gerado pelo scraper e deixa no formato que o dashboard usa
import os
import pandas as pd
from app.bairros import Na_regiao_universitaria, Nome_padrao

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

def Carregar_imoveis(caminho=CAMINHO_CSV, so_regiao_universitaria=True):
    df = pd.read_csv(caminho)
    df['bairro'] = df['bairro'].map(Nome_padrao)

    # Sem total (aluguel "Consulte-nos") não dá pra comparar preço
    filtro = df['total_mensal'].notna() & (df['total_mensal'] <= VALOR_MAXIMO)
    if so_regiao_universitaria:
        filtro &= df['bairro'].map(Na_regiao_universitaria)
    df = df[filtro].copy()

    um_comodo = df['subtipo'].str.lower().str.contains(SUBTIPOS_DE_UM_DORMITORIO, na=False)
    df.loc[um_comodo & df['dormitorios'].isna(), 'dormitorios'] = 1

    return df.rename(columns=COLUNAS_EXIBICAO)
