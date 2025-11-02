# (WIP) Scraper de dados - Análise imobiliário no contexto universitário da cidade de São Carlos/SP 
Esse projeto tem o intuito de realizar uma coleta de dados dos imóveis da cidade de São Carlos, nas regiões próximas às faculdades USP e UFSCar, para analisar os bairros mais baratos e com maior oferta para um estudante morar. Por enquanto, o sistema faz a raspagem dos dados no site da imobiliária mais famosa da cidade, realiza seu tratamento, e os guarda num DataFrame. Porém, o objetivo final é plotar um mapa geográfico interativo que possa filtrar e ilustrar os dados coletados pelo sistema coroplético. 

⚠️ Disclaimer: O projeto é para fins educacionais e acadêmicos somente. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.

# Estrutura do projeto
|   .gitattributes
|   estrutura.txt
|   main.py
|   README.md
|   
+---.idea
|   |   .gitignore
|   |   imobiliario_universitario.iml
|   |   misc.xml
|   |   modules.xml
|   |   vcs.xml
|   |   workspace.xml
|   |   
|   \---inspectionProfiles
|           profiles_settings.xml
|           
\---scripts
    |   tabulaþÒo_de_dados.py
    |   web_scraping.py
    |   
    +---.idea
    |   |   .gitignore
    |   |   misc.xml
    |   |   modules.xml
    |   |   scripts.iml
    |   |   vcs.xml
    |   |   workspace.xml
    |   |   
    |   \---inspectionProfiles
    |           profiles_settings.xml
    |           
    \---__pycache__
            tabulaþÒo_de_dados.cpython-313.pyc
            web_scraping.cpython-313.pyc
            

# 🔎 Classificações e filtros planejados
- Média de aluguel por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios.
- Maior e menor valor de imóvel por bairro, podendo filtrar pelo número de dormitórios.
- Quantidade de imóveis por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios.

# 💻 Tecnologias utilizadas
- Python 
- Selenium
- Pandas
- Folium (Planejado)
- Requests (Planejado)
- API Google Maps (Planejado)
