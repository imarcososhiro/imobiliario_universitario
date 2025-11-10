from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

'''
Melhoras a serem feitas:
- Abrir mais de uma aba por vez
- Implementar Expected conditions
- Rodar em segundo plano
- Parar de carregar imagens
'''

# Settings pra fazer o scraper rodar em segundo plano

chrome_options = Options()
chrome_options.page_load_strategy = 'eager'
chrome_options.add_argument("--headless")
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
    botao_pesquisa = espera.until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/section/div/div[1]/div[1]/button')))
    botao_pesquisa.click()

    print('✔️  Filtrando apartamentos')
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
    cidade = navegador.find_element(By.XPATH, '//*[@id="pesquisa_imoveis"]/div[3]/div[3]/div')
    cidade_tag_select = cidade.find_element(By.TAG_NAME, 'select')
    cidade_select = Select(cidade_tag_select)
    cidade_select.select_by_value('190')

    # Filtrar por tipo (Apartamento, Kitchnet, Studio, com/sem condomínio) - mudar para select depois, pra evitar achar pelo xpath
    navegador.find_element(By.XPATH, '//*[@id="pesquisa_imoveis"]/div[3]/div[4]/div/button').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-1"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-2"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-7"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-8"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-9"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-10"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-11"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-12"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-13"]').click()
    navegador.find_element(By.XPATH, '//*[@id="bs-select-2-15"]').click()

    # Filtrar pelos bairros - add o resto depois
    bairro = navegador.find_element(By.XPATH, '//*[@id="pesquisa_imoveis"]/div[3]/div[5]/div')
    bairro_tag_select = bairro.find_element(By.TAG_NAME, 'select')
    bairro_select = Select(bairro_tag_select)
    #bairro_select.select_by_value('5704') # Centro 1 - só pra teste, tirar dps
    bairro_select.select_by_value('16743') # Centro 2
    bairro_select.select_by_value('16859')  # Jardim Lutfalla
    bairro_select.select_by_value('4171')  # Cidade Jardim
    bairro_select.select_by_value('4146')  # Vila Monteiro (Gleba I)
    bairro_select.select_by_value('1615')  # Vila Costa do Sol

    # Confirmar filtro
    navegador.find_element(By.XPATH, '//*[@id="filtro"]/div/div/div[3]/div[2]/button').click()

    #===========================================================================================================#

    # Pt. 2 - Scrapping
    lista_links_aps = []

    # Função que adiciona o link dos apartamentos da vitrine à lista lista_links_aps
    def Pegando_links_aps():
        nonlocal lista_links_aps

        links_gerais = navegador.find_elements(By.TAG_NAME, 'a')
        container = navegador.find_elements(By.CLASS_NAME, 'container')
        links_aps = container[1].find_elements(By.TAG_NAME, 'a')
        for site in links_aps:
            link = site.get_attribute('href')
            if link in lista_links_aps or 'javascript' in link or 'pag=' in link:
                continue
            lista_links_aps.append(link)

    # Função que extrai todos os links de vitrines
    def Pegando_links_vitrines():
        lista_links_vitrines = []

        while True:
            pagina_div = navegador.find_element(By.CLASS_NAME, 'pagination')
            pagina_ul = pagina_div.find_element(By.TAG_NAME, 'ul')
            paginas = pagina_ul.find_elements(By.TAG_NAME, 'li')
            links_paginas = pagina_ul.find_elements(By.TAG_NAME, 'a')

            for links in links_paginas:
                link = links.get_attribute('href')
                if link in lista_links_vitrines or 'javascript' in link:
                    continue
                lista_links_vitrines.append(link)

            if paginas[-1].get_attribute('class') == 'disabled':
                break

            navegador.get(links_paginas[-2].get_attribute('href'))
        return lista_links_vitrines

    aps_dados = []  # Lista pra guardar os dados dos aps

    # Função que extrai os dados dos apartamentos
    def Extrair_dados_aps(bairro, link):
        nonlocal aps_dados

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

    # Extração dos links de vitrines de apartamentos (páginas que listam os aps)
    print('✔️  Extraindo links das vitrines de aps')
    lista_vitrines = Pegando_links_vitrines()
    print('✔️  Extraindo links dos apartamentos de cada vitrine\n')
    for vit in lista_vitrines:
        navegador.get(vit)
        Pegando_links_aps()

    print('\nOBS: Nem todos os apartamentos coletados serão listados no mapa, pois, o site só conta com filtro de\nvalor de Aluguel e, consequentemente, alguns imóveis ultrapassam o valor de R$ 3000 quando somado o Aluguel ao Condomínio e IPTU.')

    print(f'\nQuantidade de apartamentos coletados: {len(lista_links_aps)}')
    print(f'Quantidade de vitrines coletadas: {len(lista_vitrines)}\n')

    c = 1
    for link in lista_links_aps:
        navegador.get(link)
        bairro = link.split('/')[-2].replace('-',' ')
        Extrair_dados_aps(bairro, str(link))
        if len(aps_dados)%10 == 0:
            print(f'Aps extraídos: {len(aps_dados)}')

    print(f'Aps extraídos: {len(aps_dados)}')
    print('\nVarredura completa! ✅\n')

    navegador.quit()
    return aps_dados
