import folium
import branca.colormap as cm

# Cria o mapa com os dados
def Criar_Mapa(df_infos, analise): # Pega o DataFrame do script analises.py

    mapa = folium.Map(location=(-21.99428551038883, -47.88574553256096), zoom_start=14, min_zoom=12,max_zoom=15,scrollWheelZoom=True,zoom_control=False,doubleClickZoom=False)

    # Criando legendas pra descrição das cores
    if analise == 'Media':
        legenda = 'Média de valores por bairro'
    elif analise == 'Quantidade':
        legenda = 'Quantidade de apartamentos por bairro'

    # Definindo valor máximo e mínimo da análise pra definir os extremos do degradê de cores
    valor_minimo = df_infos[analise].min()
    valor_maximo = df_infos[analise].max()

    # Definindo cores do degradê de cada análise
    if analise == 'Media':
        degrade = ['green', 'yellow', 'red']
    elif analise == 'Quantidade':
        degrade = ['lightblue','darkblue']

    # Cria uma escala de cores baseado nos extremos definidos
    escala_cores = cm.LinearColormap(
            colors=degrade,
            vmin=valor_minimo,
            vmax=valor_maximo
        )

    # Legenda informativa das cores
    escala_cores.caption = legenda
    mapa.add_child(escala_cores)

    # Função que cria o círculo dos bairros em degradê
    def Circulo(coordenada, escala_cores, html, mapa, bairro):
        folium.CircleMarker(
            location=coordenada,
            radius=20,
            color=escala_cores(info_cor),
            stroke=False,
            fill=True,
            fill_color=escala_cores(info_cor),
            fill_opacity=0.8,
            opacity=1,
            popup=bairro,
            tooltip=html,
        ).add_to(mapa)

    # Criando círculos bairro por bairro (iterando linha por linha)
    for index,linha in df_infos.iterrows():
        info_cor = linha[analise] # Valor da análise escolhida do bairro, pra definir a cor dele no degradê
        coordenada = (linha['Latitude'],linha['Longitude']) # Coordenada do bairro

        # Formatações html pra deixar os popups mais bonitos
        html_texto = f"""
            <h4 style='margin-bottom:5px;'>{linha['Bairro']}</h4>
            <strong>Média:</strong> R$ {linha['Media']}<br>
            <strong>Apartamentos disponíveis:</strong> {linha['Quantidade']}<br>
            <strong>Valor mínimo:</strong> R$ {linha['Min']}<br>
            <strong>Valor máximo:</strong> R$ {linha['Max']}
            """

        Circulo(coordenada, escala_cores, html_texto, mapa, linha['Bairro'])


    # Add logos da USP e da UFSCar nas respectivas localizações
    # NOTA: Depois vou colocar o caminho das imagens no código pra não ter que duplicar as imagens em pastas diferentes
    icone_usp = 'usp-logo.png'
    icone_usp_mapa = folium.CustomIcon(
        icon_image=icone_usp,
        icon_size=(70, 70),
        icon_anchor=(25, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=(-22.006213906979283, -47.89752552863632),
        icon=icone_usp_mapa,
        popup=f"""
            <h4 style='margin-bottom:5px;>USP CAASO</h4>'""",
        tooltip='Universidade de São Paulo (USP)'
    ).add_to(mapa)

    icone_ufscar = 'ufscar-logo.png'
    icone_ufscar_mapa = folium.CustomIcon(
        icon_image=icone_ufscar,
        icon_size=(90, 90),
        icon_anchor=(40, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=(-21.982364333434838, -47.87966644394043),
        icon=icone_ufscar_mapa,
        popup=f"""
                <h4 style='margin-bottom:5px;>UFSCar</h4>'""",
        tooltip='Universidade Federal de São Carlos (UFSCar)'
    ).add_to(mapa)
    #mapa.save('mapa.html')
    #webbrowser.open('mapa.html') #Comandos pra teste do script também

    icone_rodoviaria = 'icone-rodoviaria.png'
    icone_rodoviaria_mapa = folium.CustomIcon(
        icon_image=icone_rodoviaria,
        icon_size=(30, 30),
        icon_anchor=(40, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=(-22.00521597624045, -47.88955145780041),
        icon=icone_rodoviaria_mapa,
        popup='Rodoviária de São Carlos',
        tooltip='Rodoviária de São Carlos'
    ).add_to(mapa)

    return mapa
