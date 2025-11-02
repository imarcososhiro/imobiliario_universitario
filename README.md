# (WIP) Scraper de dados - Análise imobiliário no contexto universitário na cidade de São Carlos/SP 
Disclaimer: O projeto é para fins educacionais e acadêmicos somente. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.

Esse projeto tem o intuito de realizar uma coleta de dados simples dos imóveis da cidade de São Carlos nos bairros das regiões próximas às faculdades USP e UFSCar, como: nome do bairro, valor mensal completo do imóvel (aluguel + condomínio + IPTU, etc) e nº de dormitórios, para analisar as regiões com mais oferta e mais baratas para morar. Por enquanto, o sistema utiliza a biblioteca Selenium para fazer a raspagem de dados no site da imobiliária mais famosa da cidade, e a biblioteca Pandas para a criação e manipulação de DataFrames. Porém, o objetivo é integrar a biblioteca Folium e a API do Google Maps para a criação de um mapa geográfico interativo que possa ilustrar pelo sistema de mapa coroplético as análises feitas. 

# Classificações planejadas:
- Média de aluguel por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios
- Maior e menor valor de imóvel por bairro, podendo filtrar pelo número de dormitórios
- Quantidade de imóveis por bairro, podendo filtrar por faixa de preço e pelo número de dormitórios
