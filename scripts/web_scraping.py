from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import os

# Settings pra fazer o scraper rodar em segundo plano no github actions
chrome_options = Options()
chrome_options.page_load_strategy = 'eager'
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("prefs", {"profile.managed_default_settings.images": 2})
chrome_options.add_argument('--log-level=3')

def Scraper():
    print('⏳ Iniciando scraping...\n')
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=chrome_options)
    espera = WebDriverWait(navegador, 10)

    # Pt. 1 - Filtrando apartamentos

    navegador.get('https://www.cardinali.com.br/pesquisa-de-imoveis/')
    navegador.maximize_window()

    #Abrir layout de filtros
    botao_pesquisa = espera.until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/section/div/div[1]/div[1]/button')))
    botao_pesquisa.click()

    print('✔️ Filtrando apartamentos')

    # Selecionar Locação
    operacao = espera.until(EC.element_to_be_clickable((By.TAG_NAME, 'select')))
    operacao_select = Select(operacao)
    operacao_select.select_by_value('L')

    # Filtrar por preço
    navegador.execute_script(""" 
        var slider = document.getElementById('slider_loc');
        if (slider && slider.noUiSlider) {
            slider.noUiSlider.set([0, 3000]); // min, max
        }
    """) # código em JS que eu peguei do gpt porque não manjo de JS

    # Filtrar pela cidade de São Carlos
    cidade_id = navegador.find_element(By.ID, 'id_cidade')
    cidade_select = Select(cidade_id)
    cidade_select.select_by_value('190')

    # Filtrar por tipo (Apartamento,Flat, Kitchnet, Studio, com/sem condomínio)
    tipo_imovel_id = navegador.find_element(By.ID,'id_tipo_imovel')
    tipo_imovel_select = Select(tipo_imovel_id)
    tipo_imovel_select.select_by_value('184') # Apartamento
    tipo_imovel_select.select_by_value('164') # Apartamento sem condomínio
    tipo_imovel_select.select_by_value('55') # Flat
    tipo_imovel_select.select_by_value('37') # Flat com Condomínio
    tipo_imovel_select.select_by_value('4') # Flat sem Condomínio
    tipo_imovel_select.select_by_value('61') # Kitchnet
    tipo_imovel_select.select_by_value('36') # Kitchnet com Condomínio
    tipo_imovel_select.select_by_value('6') # Kitchnet sem Condomínio
    tipo_imovel_select.select_by_value('8') # Padrão
    tipo_imovel_select.select_by_value('181') # Prédio
    tipo_imovel_select.select_by_value('161') # Studio

    # Filtrar pelos bairros - adicionar mais depois
    bairro_id = navegador.find_element(By.ID,'id_bairro')
    bairro_select = Select(bairro_id)
    bairro_select.select_by_value('16743') # Centro
    bairro_select.select_by_value('16859')  # Jardim Lutfalla
    bairro_select.select_by_value('4171')  # Cidade Jardim
    bairro_select.select_by_value('4146')  # Vila Monteiro (Gleba I)
    bairro_select.select_by_value('1690')  # Vila Monteiro Gleba I
    bairro_select.select_by_value('802')  # Jardim Paulistano
    bairro_select.select_by_value('793')  # Jardim Paraíso
    bairro_select.select_by_value('17022')  # Jardim Macarenco
    bairro_select.select_by_value('3871')  # Jardim Macarengo
    bairro_select.select_by_value('238')  # Cidade Universitária
    bairro_select.select_by_value('1144')  # Parque Arnold Schimidt
    bairro_select.select_by_value('895')  # Jardim Santa Paula
    bairro_select.select_by_value('100')  # Jardim Bandeirantes
    bairro_select.select_by_value('544')  # Jardim Centenario
    bairro_select.select_by_value('775')  # Jardim Nova Santa Paula
    bairro_select.select_by_value('1540')  # Tijuco Preto
    bairro_select.select_by_value('505')  # Jardim Bethania
    bairro_select.select_by_value('1621')  # Vila Elizabeth
    bairro_select.select_by_value('5266')  # Jardim São Carlos
    bairro_select.select_by_value('1255')  # Parque Santa Monica
    bairro_select.select_by_value('1258')  # Parque Santa Monica II
    bairro_select.select_by_value('478')  # Jardim Alvorada
    bairro_select.select_by_value('1606')  # Vila Celina
    bairro_select.select_by_value('1669')  # Vila Marina
    bairro_select.select_by_value('1666')  # Vila Marigo
    bairro_select.select_by_value('16994')  # Jardim Hikari
    bairro_select.select_by_value('3780')  # Jardim Hikare
    bairro_select.select_by_value('3121')  # Parque Industrial
    bairro_select.select_by_value('1156')  # Parque Delta
    bairro_select.select_by_value('16884')  # Monjolinho
    bairro_select.select_by_value('3538')  # Jardim Jockei Club A
    bairro_select.select_by_value('3777')  # Jardim Jockey Clube
    bairro_select.select_by_value('17341')  # Jardim Jockei Club
    bairro_select.select_by_value('394')  # Parque Espraiado

    # Confirmar filtro
    navegador.find_element(By.XPATH, '//*[@id="filtro"]/div/div/div[3]/div[2]/button').click()

    #===========================================================================================================#

    # Pt. 2 - Extração dos dados

    # Função que cria uma lista com os links dos apartamentos listados em uma página vitrine
    # NOTA: páginas vitrines são as páginas que tem vários apartamentos listados, só com
    # a foto, preço e bairro de cada um
    def Pegando_links_aps():
        lista_links_aps = []

        container = navegador.find_elements(By.CLASS_NAME, 'container')
        links_aps = container[1].find_elements(By.TAG_NAME, 'a')
        for site in links_aps:
            link = site.get_attribute('href')
            if link in lista_links_aps or 'javascript' in link or 'pag=' in link:
                continue
            lista_links_aps.append(link)
        return lista_links_aps

    aps_dados = [] # lista que vai guardar todos os dados dos apartamentos

    # Função que extrai os dados dos apartamentos a partir da página específica deles
    def Extrair_dados_aps(bairro, link):
        nonlocal aps_dados
        try:
            valores_agrupados = navegador.find_element(By.ID, 'valores_imovel')
            valores = valores_agrupados.find_elements(By.XPATH, './div')
            especificacoes = []
            especificacoes.append(('Bairro', bairro))
            especificacoes.append(('Link', link))
            categorias = ['C. Bonificação', 'Condomínio', 'IPTU', 'Total / Mês']
            for valor in valores:
                categoria, valor = map(str, valor.text.split('\n'))
                if categoria in categorias:
                    if categoria == 'C. Bonificação':
                        categoria = 'Aluguel com Bonificação'
                    pass
                elif 'POR:' in categoria:
                    categoria = 'Aluguel Cheio'
                elif 'Aluguel' == categoria:
                    categoria = 'Aluguel Cheio'
                else:
                    continue
                especificacoes.append((categoria, valor))

            dormitorios = navegador.find_element(By.XPATH, '/html/body/main/section[2]/div/div[1]/div[5]/div/div[3]/div/div').text
            especificacoes.append(('Dormitórios', dormitorios))
            aps_dados.append(especificacoes)
        except:
            pass

    # Pegando quantidade de imóveis encontrados
    texto_imoveis = navegador.find_element(By.XPATH, '/html/body/main/section/div/h1').text
    quantidade_imoveis = texto_imoveis.split(' ')[0]

    print(f'\n✔️ {quantidade_imoveis} imóveis encontrados')

    print('\nOBS: Nem todos os apartamentos coletados serão listados no mapa, pois, o site só conta com filtro de\nvalor de Aluguel e, consequentemente, alguns imóveis ultrapassam o valor de R$ 3000 quando somado o Aluguel ao Condomínio e IPTU.\n')

    print('✔️ Começando extração dos dados...\n')
    # loop para extração de dados dos apartamentos
    while True:
        #Pegando o link da próxima vitrine
        pagina_div = navegador.find_element(By.CLASS_NAME, 'pagination')
        pagina_ul = pagina_div.find_element(By.TAG_NAME, 'ul')
        paginas = pagina_ul.find_elements(By.TAG_NAME, 'li')
        links_paginas = pagina_ul.find_elements(By.TAG_NAME, 'a')

        #Link da próxima vitrine
        proxima_pagina = links_paginas[-1].get_attribute('href')

        #Pegando o link de todos os apartamentos da vitrine atual
        links_aps = Pegando_links_aps()

        #Extraindo dados de todos os apartamentos da página, usando os links coletados
        for link_apartamento in links_aps:
            navegador.get(link_apartamento)
            bairro = link_apartamento.split('/')[-2].replace('-', ' ') #Pego o nome do bairro diretamente da URL do ap
            Extrair_dados_aps(bairro, str(link_apartamento))
            if len(aps_dados) % 10 == 0:
                print(f'Aps extraídos: {len(aps_dados)}')
        # Quando chego na última vitrine, o link dela tem o formato 'JavaScript:void(0);'
        # portanto é um identificador pra parar o loop
        if 'javascript' in proxima_pagina.lower():
            break
        else:
            navegador.get(proxima_pagina)

    print(f'Aps extraídos: {len(aps_dados)}')
    print('\nVarredura completa! ✅\n')

    navegador.quit()

    #Função que pega o Dataset bruto do Scraper e faz a limpeza dos dados
    def Limpar_Dados(apartamentos):
        aps_dados_limpos = []

        # Formatando a vírgula e o tipo dos números, e o nome dos bairros
        for dados in apartamentos:
            lista_tuplas = []

            for categoria, info in dados:
                # Transformando os preços em floats
                if categoria == 'Total / Mês':
                    info = info.replace('.', '')
                    info = info.replace(',', '.')
                    info = float(info)

                # Transformando o nº de dormitórios em ints
                elif categoria == 'Dormitórios':
                    info = int(info)

                lista_tuplas.append((categoria, info))

            aps_dados_limpos.append(dict(lista_tuplas))

        df = pd.DataFrame(aps_dados_limpos)
        # Preço limite dos aps = R$ 3000
        return df[df['Total / Mês'] <= 3000]

    #Dados limpos
    df_final = Limpar_Dados(aps_dados)

    # Salvando Dataset em csv
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'dados')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'dados_imoveis.csv')

    df_final.to_csv(output_path, index=False)

Scraper()