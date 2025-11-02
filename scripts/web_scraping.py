from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import time

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico)

def Scraper():
    # Pt. 1 - Filtrando apartamentos

    navegador.get('https://www.cardinali.com.br/pesquisa-de-imoveis/')
    navegador.maximize_window()
    botao_pesquisa = navegador.find_element(By.XPATH, '/html/body/main/section/div/div[1]/div[1]/button').click()
    time.sleep(2)

    # Selecionar Locação
    operacao = navegador.find_element(By.TAG_NAME, 'select')
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

    # Filtrar por tipo (Apartamento, Kitchnet, Studio, com/sem condomínio)
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

    # Filtrar pelos bairros
    #navegador.find_element(By.XPATH, '//*[@id="pesquisa_imoveis"]/div[3]/div[5]/div/button/div/div/div').click()
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1033"]').click() # Centro 1 - tirar dps
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1034"]').click() # Centro 2
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1045"]').click() # Cidade Jardim
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1046"]').click() # Cidade Universitária
    navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1107"]').click() # Jardim Lutfalla
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1184"]').click() # Parque Arnold Schdmith
    #navegador.find_element(By.XPATH, '//*[@id="bs-select-3-1275"]').click() # Vila Costa do Sol

    # Confirmar filtro
    navegador.find_element(By.XPATH, '//*[@id="filtro"]/div/div/div[3]/div[2]/button').click()
    #===========================================================================================================#

    # Pt. 2 - Scrapping

    aps_dados = [] # Lista pra guardar os dados dos aps

    # Função que extrai os dados dos aps da página atual
    def Extrair_dados_aps():
        nonlocal aps_dados, contador_paginas

        apartamentos_agrupados = navegador.find_element(By.XPATH, '/html/body/main/section/div/div[2]')
        apartamentos = apartamentos_agrupados.find_elements(By.XPATH, './div')  # ./div para percorrer as divs filhas

        c = 0
        for ap in apartamentos:
            c += 1
            bairro = ap.find_element(By.CLASS_NAME, 'card-bairro-cidade-texto').text
            link_detalhes = ap.find_element(By.TAG_NAME, 'a').get_attribute('href')  # Pega o link da aba específica daquele imóvel
            navegador.execute_script(
                f"window.open('{link_detalhes}');")  # Abre o link por meio de um script JS que também tive que pesquisar no GPT, porque não manjo
            aba_atual = navegador.window_handles[0]
            aba_nova = navegador.window_handles[-1]
            navegador.switch_to.window(aba_nova)
            valores_agrupados = navegador.find_element(By.ID, 'valores_imovel')
            valores = valores_agrupados.find_elements(By.XPATH, './div')
            especificacoes = []
            especificacoes.append(('Bairro', bairro))
            for valor in valores:
                if 'Imóvel' in valor.text or 'ITBI' in valor.text or 'Consulte-nos' in valor.text: # Ignorando linhas sem dados relevantes
                    continue
                else:
                    categoria, valor = map(str, valor.text.split('\n'))
                    especificacoes.append((categoria, valor))
            dormitorios = navegador.find_element(By.XPATH, '/html/body/main/section[2]/div/div[1]/div[5]/div/div[3]/div/div').text
            especificacoes.append(('Dormitórios', dormitorios))
            aps_dados.append(especificacoes)
            navegador.close()
            navegador.switch_to.window(aba_atual)

        print(f'\nPágina {contador_paginas} completa ✅')
        print(f'Número de apartamentos extraidos no total: {len(aps_dados)}')
        contador_paginas += 1


    #Extraindo links das páginas 2,3, 4... e iterando a extração de dados sobre cada uma delas
    pagina_div = navegador.find_element(By.CLASS_NAME, 'pagination')
    pagina_ul = pagina_div.find_element(By.TAG_NAME, 'ul')
    paginas = pagina_ul.find_elements(By.TAG_NAME, 'li')

    lista_links = []

    for aps in paginas:
        if aps.get_attribute('class') == 'disabled' or aps.get_attribute('class') == 'active': # pra não pegar o link da página atual, nem da seta de página anterior
            continue
        link = aps.find_element(By.TAG_NAME, 'a').get_attribute('href')
        if link in lista_links: # correçãozinha aqui. isso é porque a ultima opção da section de páginas é de "próxima página", o que faz puxar o link da página 2 de novo
            continue
        else:
            lista_links.append(link)

    contador_paginas = 1

    # Extração de dados da página 1
    Extrair_dados_aps()

    # Extração de dados das demais páginas
    for links in lista_links:
        navegador.execute_script(f"window.open('{links}');")
        navegador.close()
        navegador.switch_to.window(navegador.window_handles[-1])
        Extrair_dados_aps()

    print('\nVarredura completa! ✅\n')

    return aps_dados