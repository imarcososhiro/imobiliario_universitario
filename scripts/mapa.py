import folium
import branca.colormap as cm

'''

# Dados de teste, só pra testar o script

import webbrowser
import pandas as pd
from scripts.analises_formatacao import Tirar_infos_bairros 

df = [{'Bairro': 'Jardim Lutfalla', 'Aluguel': 1500.5, 'C. Bonificação': 1250.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 2200, 'Dormitórios': 1.0},{'Bairro': 'Jardim Lutfalla', 'Aluguel': 2200, 'C. Bonificação': 1250.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 2200, 'Dormitórios': 1.0},{'Bairro': 'Jardim Lutfalla', 'Aluguel': 2200, 'C. Bonificação': 2778.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 2200, 'Dormitórios': 1.0},{'Bairro': 'Cidade Jardim', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 2000, 'Dormitórios': 3.0},{'Bairro': 'Cidade Jardim', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 1300, 'Dormitórios': 3.0},{'Bairro': 'Centro', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 3704.0, 'Dormitórios': 3.0},{'Bairro': 'Jardim Macarengo', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 689.0, 'IPTU': 237.0, 'Total / Mês': 3704.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 3333.75, 'C. Bonificação': 2667.0, 'Condomínio': 282.0, 'Total / Mês': 2949.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3750.0, 'C. Bonificação': 3000.0, 'Condomínio': 395.0, 'Total / Mês': 3395.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3056.25, 'C. Bonificação': 2445.0, 'Condomínio': 506.41, 'IPTU': 100.52, 'Total / Mês': 3051.93, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3500.0, 'C. Bonificação': 2800.0, 'Condomínio': 440.0, 'Total / Mês': 3240.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2083.75, 'C. Bonificação': 1667.0, 'Condomínio': 835.0, 'IPTU': 206.0, 'Total / Mês': 2708.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 3195.0, 'C. Bonificação': 2556.0, 'Condomínio': 517.0, 'IPTU': 160.45, 'Total / Mês': 3233.45, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2500.0, 'C. Bonificação': 2000.0, 'Condomínio': 835.0, 'IPTU': 206.0, 'Total / Mês': 3041.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 3056.25, 'C. Bonificação': 2445.0, 'Condomínio': 750.0, 'IPTU': 100.0, 'Total / Mês': 3295.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 500.0, 'Total / Mês': 3278.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 458.43, 'IPTU': 208.95, 'Total / Mês': 3445.38, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 1625.0, 'C. Bonificação': 1300.0, 'Condomínio': 208.21, 'IPTU': 28.04, 'Total / Mês': 1536.25, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 1800.0, 'Condomínio': 667.0, 'IPTU': 126.0, 'Total / Mês': 2593.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2778.75, 'C. Bonificação': 2223.0, 'Condomínio': 240.0, 'IPTU': 43.0, 'Total / Mês': 2506.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3000.0, 'C. Bonificação': 2400.0, 'Condomínio': 500.0, 'IPTU': 101.0, 'Total / Mês': 3001.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2700.0, 'Condomínio': 420.0, 'Total / Mês': 3120.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2112.0, 'Condomínio': 280.0, 'IPTU': 89.0, 'Total / Mês': 2481.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1958.75, 'C. Bonificação': 1567.0, 'Condomínio': 330.0, 'IPTU': 50.0, 'Total / Mês': 1947.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3625.0, 'C. Bonificação': 2900.0, 'Condomínio': 218.0, 'IPTU': 43.59, 'Total / Mês': 3161.59, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3125.0, 'C. Bonificação': 2500.0, 'Condomínio': 879.22, 'IPTU': 183.34, 'Total / Mês': 3562.56, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2750.0, 'C. Bonificação': 2200.0, 'Condomínio': 670.0, 'IPTU': 176.0, 'Total / Mês': 3046.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2083.75, 'C. Bonificação': 1667.0, 'Condomínio': 1200.0, 'IPTU': 115.0, 'Total / Mês': 2982.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2350.0, 'Condomínio': 260.0, 'IPTU': 40.0, 'Total / Mês': 2650.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3195.0, 'C. Bonificação': 2556.0, 'Condomínio': 288.25, 'IPTU': 47.44, 'Total / Mês': 2891.69, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 2626.25, 'C. Bonificação': 2101.0, 'Condomínio': 558.76, 'IPTU': 116.0, 'Total / Mês': 2775.76, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2186.25, 'C. Bonificação': 1749.0, 'Condomínio': 288.25, 'IPTU': 74.56, 'Total / Mês': 2111.81, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3056.25, 'C. Bonificação': 2445.0, 'Condomínio': 650.0, 'IPTU': 115.0, 'Total / Mês': 3210.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2481.25, 'C. Bonificação': 1985.0, 'Condomínio': 586.0, 'Total / Mês': 2571.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2778.75, 'C. Bonificação': 2223.0, 'Condomínio': 280.0, 'IPTU': 45.0, 'Total / Mês': 2548.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 1945.0, 'C. Bonificação': 1556.0, 'Condomínio': 481.22, 'IPTU': 42.26, 'Total / Mês': 2079.48, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3333.75, 'C. Bonificação': 2667.0, 'Condomínio': 750.0, 'IPTU': 106.0, 'Total / Mês': 3523.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1668.75, 'C. Bonificação': 1335.0, 'Condomínio': 1035.47, 'IPTU': 104.0, 'Total / Mês': 2474.47, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2375.0, 'C. Bonificação': 1900.0, 'Condomínio': 680.0, 'IPTU': 207.0, 'Total / Mês': 2787.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 1250.0, 'C. Bonificação': 1000.0, 'Condomínio': 880.0, 'Total / Mês': 1880.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 2487.5, 'C. Bonificação': 1990.0, 'Condomínio': 990.0, 'IPTU': 245.0, 'Total / Mês': 3225.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 312.15, 'IPTU': 101.11, 'Total / Mês': 3191.26, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2500.0, 'C. Bonificação': 2000.0, 'Total / Mês': 2000.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2640.0, 'C. Bonificação': 2112.0, 'Condomínio': 450.0, 'IPTU': 100.0, 'Total / Mês': 2662.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1562.5, 'C. Bonificação': 1250.0, 'Total / Mês': 1250.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1250.0, 'C. Bonificação': 1000.0, 'Total / Mês': 1000.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 2361.25, 'C. Bonificação': 1889.0, 'Condomínio': 198.0, 'IPTU': 94.55, 'Total / Mês': 2181.55, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1806.25, 'C. Bonificação': 1445.0, 'Condomínio': 350.0, 'IPTU': 40.0, 'Total / Mês': 1835.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3472.5, 'C. Bonificação': 2778.0, 'Condomínio': 400.0, 'Total / Mês': 3178.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2500.0, 'C. Bonificação': 2000.0, 'Condomínio': 360.38, 'IPTU': 183.4, 'Total / Mês': 2543.78, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1945.0, 'C. Bonificação': 1556.0, 'Condomínio': 369.02, 'IPTU': 64.91, 'Total / Mês': 1989.93, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 2778.75, 'C. Bonificação': 2223.0, 'Condomínio': 350.0, 'IPTU': 50.0, 'Total / Mês': 2623.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1528.75, 'C. Bonificação': 1223.0, 'Condomínio': 950.0, 'IPTU': 80.0, 'Total / Mês': 2253.0, 'Dormitórios': 4.0}, {'Bairro': 'Centro', 'Aluguel': 1390.0, 'C. Bonificação': 1112.0, 'Condomínio': 142.0, 'IPTU': 20.0, 'Total / Mês': 1274.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 3125.0, 'C. Bonificação': 2500.0, 'Condomínio': 490.0, 'IPTU': 100.0, 'Total / Mês': 3090.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2917.5, 'C. Bonificação': 2334.0, 'Condomínio': 490.0, 'IPTU': 100.52, 'Total / Mês': 2924.52, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 3056.25, 'C. Bonificação': 2445.0, 'Condomínio': 666.65, 'IPTU': 113.15, 'Total / Mês': 3224.8, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 1320.0, 'C. Bonificação': 1056.0, 'Condomínio': 234.0, 'IPTU': 46.0, 'Total / Mês': 1336.0, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 1123.0, 'Condomínio': 390.0, 'IPTU': 69.0, 'Total / Mês': 1582.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 2000.0, 'C. Bonificação': 1600.0, 'Condomínio': 500.0, 'IPTU': 22.58, 'Total / Mês': 2122.58, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 1806.25, 'C. Bonificação': 1445.0, 'Condomínio': 250.0, 'IPTU': 102.24, 'Total / Mês': 1797.24, 'Dormitórios': 1.0}, {'Bairro': 'Centro', 'Aluguel': 972.5, 'C. Bonificação': 778.0, 'Condomínio': 430.0, 'IPTU': 78.0, 'Total / Mês': 1286.0, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 1500.0, 'C. Bonificação': 1200.0, 'Condomínio': 560.0, 'IPTU': 64.83, 'Total / Mês': 1824.83, 'Dormitórios': 2.0}, {'Bairro': 'Centro', 'Aluguel': 2361.25, 'C. Bonificação': 1889.0, 'Condomínio': 1638.0, 'IPTU': 358.0, 'Total / Mês': 3885.0, 'Dormitórios': 3.0}, {'Bairro': 'Centro', 'Aluguel': 3750.0, 'C. Bonificação': 3000.0, 'Condomínio': 1250.0, 'IPTU': 380.0, 'Total / Mês': 4630.0, 'Dormitórios': 3.0}]
df_filtrado = pd.DataFrame(df)
df_infos = Tirar_infos_bairros(df_filtrado)

'''

# Cria o mapa com os dados
def Criar_Mapa(df_infos): # Pega o DataFrame do script analises_formatacao.py
    mapa = folium.Map(location=(-22.01253461042532, -47.8904440945462), zoom_start=15, control_scale=True)

    analise_escolhida = 'Quantidade' #Teste. Essa info vai vir do app.py
    legenda = 'Oferta de imóveis' #Teste tb. Vou fazer um if pra ir mudando a legenda conforme a analise aqui

    # Definindo valor máximo e mínimo da análise pra definir os extremos do degradê de cores
    valor_minimo = df_infos[analise_escolhida].min()
    valor_maximo = df_infos[analise_escolhida].max()

    # Definindo cores do degradê de cada análise
    if analise_escolhida == 'Media':
        degrade = ['green', 'yellow', 'red']
    elif analise_escolhida == 'Quantidade':
        degrade = ['yellow','orange']

    # Cria uma escala de cores baseado nos extremos definidos
    escala_cores = cm.LinearColormap(
            colors=degrade,
            vmin=valor_minimo,
            vmax=valor_maximo
        )

    # Legenda informativa das cores
    escala_cores.caption = legenda
    mapa.add_child(escala_cores)

    # Criando círculos bairro por bairro (iterando linha por linha)
    for index,linha in df_infos.iterrows():

        info_cor = linha[analise_escolhida] # Valor da análise escolhida do bairro, pra definir a cor dele no degradê
        coordenada = (linha['Latitude'],linha['Longitude']) # Coordenada do bairro

    # Criando o círculo dos bairros em degradê
        folium.CircleMarker(
            location=coordenada,
            radius=30,
            color=escala_cores(info_cor),
            stroke=False,
            fill=True,
            fill_color=escala_cores(info_cor),
            fill_opacity=0.6,
            opacity=1,
            popup=f'{linha['Bairro']}\n{analise_escolhida}: {info_cor}',
            tooltip=f'{linha['Bairro']} - {analise_escolhida}: {info_cor}',
        ).add_to(mapa)

    # Add logos da USP e da UFSCar nas respectivas localizações
    # NOTA: Depois vou colocar o caminho das imagens no código pra não ter que duplicar as imagens em pastas diferentes
    icone_usp = 'usp-logo.png'
    icone_ufscar = 'ufscar-logo.png'

    icone_usp_mapa = folium.CustomIcon(
        icon_image=icone_usp,
        icon_size=(75, 75),
        icon_anchor=(17, 35),
        popup_anchor=(-3, -35)
    )

    icone_ufscar_mapa = folium.CustomIcon(
        icon_image=icone_ufscar,
        icon_size=(135, 135),
        icon_anchor=(17, 35),
        popup_anchor=(-3, -35)
    )

    folium.Marker(
        location=(-22.005262729794488, -47.89860782362475),
        icon=icone_usp_mapa,
        popup='USP CAASO'
    ).add_to(mapa)

    folium.Marker(
        location=(-21.98268217980934, -47.88155633256063),
        icon=icone_ufscar_mapa,
        popup='UFSCar'
    ).add_to(mapa)

    #mapa.save('mapa.html')
    #webbrowser.open('mapa.html') #Comandos pra teste do script também

    return mapa
