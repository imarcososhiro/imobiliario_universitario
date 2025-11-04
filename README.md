# **(WIP) Web Scraper e Web App - Análise de dados de imóveis de perfil universitário**  
  
  
Esse projeto pretende fazer uma coleta de dados de apartamentos nas regiões próximas às faculdades USP e UFSCar, na cidade de São Carlos - SP, para analisar os bairros mais baratos e com maior oferta para um ou mais estudantes morarem. Por enquanto, a plotagem de mapa interativo está em desenvolvimento, mas o sistema já faz a raspagem, armazenamento e limpeza dos dados, e realiza o plot de mapa com análises teste.

⚠️ Disclaimer: O projeto é para fins educacionais e acadêmicos somente. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.

# **● Funcionamento do sistema**
1. Usando Selenium, faz uma raspagem de dados simples dos imóveis de perfil universitário: apartamentos, kitchnets e studios em bairros próximos às faculdades, com faixa de preço até R$ 3000.
2. Trata e armazena os dados em cache com Pandas e Folium.
3. Separa os dados por bairro e tira as seguintes operações para cada um: média de preço, contagem de imóveis, valor mínimo e máximo.  
4. Cria um Web app do Streamlit, faz um mapa geral por meio do Folium e o exibe no app.
5. O usuário escolhe via menus interativos as análises e filtros que ele quer ver no mapa.
6. O programa faz as operações necessárias e mostra o mapa atualizado no Streamlit, conforme os filtros selecionados.

# **● Estrutura do projeto**
📂 imobiliario_universitario  
├── 📄 app.py  
└── 📂 scripts  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 analise_formatacao.py  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 📄  coord_bairros.py  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 📄  mapa.py  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 tabulacao_de_dados.py  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 📄 web_scraping.py  
  
---
  
### ***Sumário:***  
`app.py` - *Arquivo principal recebe e aplica os filtros solicitados pelo usuário, e plota o mapa interativo*  
  
`analise_formatacao.py` - *Contém a função que calcula as análises (média de valores, oferta, etc)*  
  
`coord_bairros.py` - *Contém a função que retorna a coordenada do bairro pelo seu nome*  
  
`mapa.py` - *Contém a função que cria o mapa*  
  
`tabulacao_de_dados.py` - *Contém a função que limpa e tabula os dados coletados pelo web scraping*  
  
`web_scraping.py` - *Contém a função que faz o Scraping*  

# **● Filtros**  
  
### - *Valor dos imóveis*  
R$ 600.00&nbsp;&nbsp; **`O---•-----------•-O`**&nbsp;&nbsp; R$ 3000.00
  
---
  
  ### - *Nº de dormitórios*  
-  [x] 1  
-  [ ] 2
-  [ ] 3  
-  [ ] 4
  
---
  
### - *Tipo de análise*  
🔘 Média de valor total  
⚪ Oferta de imóveis  
⚪ Valor máximo  
⚪ Valor mínimo  
  
# **● Tecnologias utilizadas**
🟩 PyCharm  
└── 🐍 Python   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Selenium  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Pandas  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── Folium  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── Streamlit  


# **● 🚨 Observações**
- As funções do sistema ainda não acontecem para todos os bairros. Esse é um estudo a ser realizado no final no projeto. Por enquanto, seleciono de 1 a 2 para testes.
- Conselhos e dicas de implementação são bem-vindos! Esse é meu primeiro projeto de programação no meu primeiro ano de estudo de Python 🤝 
