import pandas as pd

# Formatando os itens e transformando em Dataset

def Dataset(aps_dados):
    aps_dados_limpos = []

    # Formatando a vírgula e o tipo dos números, e o nome dos bairros
    for dados in aps_dados:
        lista_tuplas = []

        for categoria,info in dados:
            # Transformando os preços em floats
            if categoria == 'Total / Mês':
                info = info.replace('.','')
                info = info.replace(',','.')
                info = float(info)

            # Transformando o nº de dormitórios em ints
            elif categoria == 'Dormitórios':
                info = int(info)

            lista_tuplas.append((categoria, info))

        aps_dados_limpos.append(dict(lista_tuplas))

    df = pd.DataFrame(aps_dados_limpos)

    # Preço limite dos aps = R$ 3000
    return df[df['Total / Mês'] <= 3000]
