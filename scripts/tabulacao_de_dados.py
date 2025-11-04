import pandas as pd

# Pt. 1 - Limpando e formatando dados brutos
# Eliminando itens desnecessários (ex: valor de venda do imóvel), e formatando valores (ex: RS 700,00 -> str para 700.00 -> float)

def Dataset(aps_dados):
    aps_dados_atualizado = []

    nome_linhas = ['Aluguel', 'Total / Mês', 'Condomínio', 'C. Bonificação', 'IPTU', 'Dormitórios', 'POR: Aluguel']

    # Percorrendo a lista dos dados para refazê-la só com os itens necessários e formatada
    for dados in aps_dados:
        lista_tuplas = []
        for categoria,info in dados:

            # Transformando valores em floats
            if categoria in nome_linhas:
                info = info.replace('.','')
                info = info.replace(',','.')
                info = float(info)

            # Tirando ' - São Carlos/SP' do nome dos bairros
            if categoria == 'Bairro' and 'São Carlos' in info:
                info = info.split(' - ')[0]
                lista_tuplas.append((categoria, info))

            # Se tiver categoria DE/POR, o 'POR:' vira o valor da categoria Aluguel
            elif categoria == 'POR: Aluguel':
                categoria = 'Aluguel'
                lista_tuplas.append((categoria, info))

            # Ignorar categorias irrelevantes pro projeto
            elif categoria == 'Venda' or categoria == 'DE: Aluguel' or categoria == 'Total':
                continue

            # Se não precisar ser formatado, vai direto pra lista
            else:
                lista_tuplas.append((categoria, info))

        aps_dados_atualizado.append(dict(lista_tuplas))

    df = pd.DataFrame(aps_dados_atualizado)

    return df

'''

** Planejamento de filtros e dados **

- Média aluguel/bairro (/faixa de preço, /nº de dormitórios) 
- Nº de imóveis/bairro (/faixa de preço,/nº de dormitórios)
- Maior valor/bairro (/nº de dormitórios)
- Menor valor/bairro (/nº de dormitórios)

'''
