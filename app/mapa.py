import os
import folium
import branca.colormap as cm
from app.bairros import RODOVIARIA, UFSCAR, USP, Buscar_contorno

# Caminho absoluto da pasta de imagens, pra funcionar independente de onde o app é executado
PASTA_ASSETS = os.path.join(os.path.dirname(__file__), '..', 'assets')

# Explicação no tooltip dos bairros cujo contorno não veio pronto do OpenStreetMap
AVISO_CONTORNO = {
    'enderecos': 'Contorno estimado pelos endereços do bairro no OpenStreetMap',
    'aproximado': 'Contorno aproximado (o bairro só tem um ponto no OpenStreetMap)',
}

# Cria o mapa com os dados
def Criar_Mapa(df_infos, analise): # Pega o DataFrame do script analises.py
    mapa = folium.Map(location=(-21.99428551038883, -47.88574553256096), zoom_start=14, min_zoom=12,max_zoom=15,scrollWheelZoom=True,zoom_control=False,doubleClickZoom=False)

    # Criando legendas pra descrição das cores
    if analise == 'Media':
        legenda = 'Média de valores por bairro'
    elif analise == 'Quantidade':
        legenda = 'Quantidade de imóveis por bairro'

    # Definindo valor máximo e mínimo da análise pra definir os extremos do degradê de cores
    valor_minimo = df_infos[analise].min()
    valor_maximo = df_infos[analise].max()

    # Definindo cores do degradê de cada análise
    if analise == 'Media':
        degrade = ['pink','red']
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

    # Função que pinta a área do bairro com a cor do degradê
    def Area_bairro(contorno, cor, html, mapa):
        folium.GeoJson(
            contorno,
            # Borda branca fina: separa bairros vizinhos que têm cores parecidas
            style_function=lambda feature: {'fillColor': cor, 'color': 'white', 'weight': 1.2, 'fillOpacity': 0.65},
            highlight_function=lambda feature: {'color': '#1f2937', 'weight': 2.5, 'fillOpacity': 0.85},
            tooltip=folium.Tooltip(html),
        ).add_to(mapa)

    # Pintando os bairros um por um (iterando linha por linha)
    for index,linha in df_infos.iterrows():
        contorno = Buscar_contorno(linha['Bairro'])
        if contorno is None: # Bairro sem contorno no mapa: aparece só na tabela
            continue
        cor = escala_cores(linha[analise]) # Cor do bairro no degradê, conforme a análise escolhida

        # Formatações html pra deixar os popups mais bonitos
        html_texto = f"""
            <h4 style='margin-bottom:5px;'>{linha['Bairro']}</h4>
            <strong>Média:</strong> R$ {linha['Media']}<br>
            <strong>Imóveis disponíveis:</strong> {linha['Quantidade']}<br>
            <strong>Valor mínimo:</strong> R$ {linha['Min']}<br>
            <strong>Valor máximo:</strong> R$ {linha['Max']}
            """
        aviso = AVISO_CONTORNO.get(contorno['properties']['origem'])
        if aviso:
            html_texto += f"<br><em style='font-size:11px;'>{aviso}</em>"

        Area_bairro(contorno, cor, html_texto, mapa)


    # Add logos da USP e da UFSCar nas respectivas localizações
    icone_usp = os.path.join(PASTA_ASSETS, 'usp-logo.png')
    icone_usp_mapa = folium.CustomIcon(
        icon_image=icone_usp,
        icon_size=(70, 70),
        icon_anchor=(25, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=USP,
        icon=icone_usp_mapa,
        popup='USP CAASO',
        tooltip='Universidade de São Paulo (USP)'
    ).add_to(mapa)

    icone_ufscar = os.path.join(PASTA_ASSETS, 'ufscar-logo.png')
    icone_ufscar_mapa = folium.CustomIcon(
        icon_image=icone_ufscar,
        icon_size=(90, 90),
        icon_anchor=(40, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=UFSCAR,
        icon=icone_ufscar_mapa,
        popup='UFSCar',
        tooltip='Universidade Federal de São Carlos (UFSCar)'
    ).add_to(mapa)
    #mapa.save('mapa.html')
    #webbrowser.open('mapa.html') #Comandos pra teste do script também

    icone_rodoviaria = os.path.join(PASTA_ASSETS, 'icone-rodoviaria.png')
    icone_rodoviaria_mapa = folium.CustomIcon(
        icon_image=icone_rodoviaria,
        icon_size=(45, 45),
        icon_anchor=(40, 23),
        popup_anchor=(0, 0)
    )

    folium.Marker(
        location=RODOVIARIA,
        icon=icone_rodoviaria_mapa,
        popup='Rodoviária de São Carlos',
        tooltip='Rodoviária de São Carlos'
    ).add_to(mapa)

    return mapa
