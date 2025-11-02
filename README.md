# (WIP) Web Scraper - Análise de dados imobiliários no contexto universitário da cidade de São Carlos/SP 
Esse projeto tem o intuito de realizar uma coleta de dados dos imóveis da cidade de São Carlos, nas regiões próximas às faculdades USP e UFSCar, para analisar os bairros mais baratos e com maior oferta para um estudante, ou um grupo de estudantes, morar. Por enquanto, o sistema faz a raspagem dos dados no site da imobiliária mais famosa da cidade, realiza seu tratamento, e os guarda num DataFrame. Porém, o objetivo final é plotar um mapa geográfico interativo que possa filtrar e ilustrar os dados coletados, por sistema coroplético.

⚠️ Disclaimer: O projeto é para fins educacionais e acadêmicos somente. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.

# Funcionamento do programa
1. Faz uma raspagem de dados básicos dos imóveis (bairro, valor total mensal, nº de dormitórios) de perfil universitário: Apartamentos/Kitchnets/Studios em bairros próximos às faculdades, com faixa de preço até R$ 3000, usando Selenium.
2. Trata e armazena todas as informações em um DataFrame, usando Pandas.
3. (WIP) Utiliza a API do Google Maps, junto ao Folium, para mapear e ilustrar todos os dados coletados.
4. (WIP) Faz um mapa geográfico interativo que classifica as análises quantitativas por cor para melhor visualização.   

# Estrutura do projeto
📂 imobiliario_universitario  
├── 📄 main.py  # Arquivo principal que roda tudo  
└── 📂 scripts  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 tabulacao_de_dados.py  # Contém a função que limpa e tabula os dados coletados  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 📄 web_scraping.py  # Contém a função que faz o Scrap  

# Classificações e filtros planejados
- Média de aluguel por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios.
- Maior e menor valor de imóvel por bairro, podendo filtrar pelo número de dormitórios.
- Quantidade de imóveis por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios.

# Tecnologias utilizadas
└── Python 🐍  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Selenium  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Pandas  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Folium (Planejado)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Requests (Planejado)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── API Google Maps (Planejado)  

# 🚨 Observações
- A raspagem ainda não acontece para todos os bairros. Esse é um estudo a ser realizado no final no projeto, por enquanto seleciono de 1 a 3 para testes.
- A criação do arquivo main.py, que por enquanto tem somente 4 linhas, é puramente para melhorar a organização do código, em scripts.
- Conselhos e dicas de implementação são bem-vindos! Esse é meu primeiro projeto de programação, no meu primeiro ano de estudo de Python.  
