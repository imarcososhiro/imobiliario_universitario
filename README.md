# <h1 align="center">**🗺️ Dashboard Interativo e Web Scraper: Análise imobiliária no contexto universitário de São Carlos - SP**</h1> 

<p align="center">
  <a href="https://imobiliariouniversitario.streamlit.app/" target="_blank">
    <img 
      alt="status" 
      src="https://img.shields.io/badge/Acessar%20Site%20do%20Projeto-darkgreen?style=for-the-badge"
      width="300"
    >
  </a>
</p>

**Se um aviso assim aparecer, clique no botão azul e espere o site carregar**

<img width="1015" height="489" alt="Pagina" src="https://github.com/user-attachments/assets/d157527a-6d22-4c69-ba91-39a52e976e56" />  

---

## **Rodando localmente**
#### ***• No seu terminal***
```bash
git clone https://github.com/imarcososhiro/imobiliario_universitario
cd imobiliario_universitario
pip install -r requirements.txt
streamlit run Home.py
  ```
#### ***• Para atualizar o banco de dados manualmente, rode o script ```web_scraping.py```, na pasta scripts (ele roda em segundo plano)***

## **Descrição**  
Este projeto propõe fazer uma raspagem de dados de apartamentos nas regiões próximas à USP e UFSCar, na cidade de São Carlos/SP, para exibí-los por meio de um mapa interativo. Assim, pode-se analisar os bairros com melhor valor e oferta para um ou mais estudantes morarem, permitindo filtrar os imóveis por bairro, nº de dormitórios, e faixa de preço.  
  
⚠️ **Disclaimer:** Esse projeto é puramente para fins educacionais e acadêmicos. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.  
  
<p align="center">
  <a href="https://imobiliariouniversitario.streamlit.app/" target="_blank">
     <img width="717" height="569" alt="Screenshot_3" src="https://github.com/user-attachments/assets/3a6b7c3a-c674-4cc8-9482-d7290400615c" />
  </a>
</p> 

**Observação:** Ainda falta adicionar dados de mais bairros ao sistema, porém o programa já funciona para boa parte dos bairros da região.  
  
## **Funcionalidades**

<img alt="status" src="https://img.shields.io/badge/Projeto%20em%20Desenvolvimento-blue?style=for-the-badge">  

✔️ `Dados` - Extrai, diariamente e automaticamente, dados de imóveis para locação com perfil universitário: **Apartamentos, Kitchnets e Studios em bairros próximos à USP e UFSCar, com valor total de até R$ 3000.** 
  
✔️ `Mapa` - Exibe as métricas de cada bairro (quantidade de imóveis disponíveis, valor médio, mínimo e máximo) em um **mapa interativo clusterizado.**  
  
✔️ `Filtros` - Permite a filtragem do perfil de imóvel desejado por nº de dormitórios e faixa de preço.  

✔️ `Tabela` - Conforme o filtro aplicado, exibe em uma tabela os detalhes de todos os imóveis por bairro (Link do anúncio, valor do aluguel, condomínio, IPTU, etc.).  
  
<img width="1015" height="489" alt="Analise imobiliaria filtro2" src="https://github.com/user-attachments/assets/ed904d32-580b-412e-8c34-0dd4768a0ddf" />  


  
🟡 `Gráficos` - Segunda página com análises gráficas dos dados.
  

## **Lógica de operação**
1. Utilizando a biblioteca Selenium, foi feito um Web Scraper que faz uma raspagem e a limpeza de dados dos imóveis do site da imobiliária mais famosa da cidade, guardando-os em um arquivo CSV.  
2. Com o Github Actions, esse Scraper é executado automaticamente todos os dias, para atualização das informações no repositório.  
3. Utilizando a biblioteca Folium e Pandas, é feita a criação do mapa clusterizado e o cálculo das métricas de cada bairro, conforme os dados do CSV coletado.  
4. No Web App gerado pela biblioteca Streamlit, é feita a exibição do mapa e do banco de dados, a criação das sessões de filtros, e a personalização do layout.  
5. A cada filtro aplicado, todas as métricas e exibições são refeitas e reexibidas conforme a solicitação.  

## **Estrutura do projeto**
### **Descrição simples dos principais 📄 arquivos do sistema**
```bash
📂 imobiliario_universitario  
├── 📄 Home.py
│
├── 📂 .streamlit  
│    └── 📄 config.toml  
├── 📂 dados  
│    └── 📄 dados_imoveis.csv  
├── 📂 pages  
│    └── 📄 Gráficos.py  
└── 📂 scripts  
     ├── 📄 __init__.py  
     ├── 📄 analises.py  
     ├── 📄 coord_bairros.py  
     ├── 📄 mapa.py   
     └── 📄 web_scraping.py  
```
  
`Home.py` - *Arquivo principal. Recebe e aplica os filtros solicitados pelo usuário, plota o mapa interativo e a tabela de detalhamento dos imóveis*  

`.streamlit/config.toml` - *Arquivo que contém as settings de personalização do App Streamlit (cores, fontes, tamanhos, etc.)*

`dados/dados_imoveis.csv` - *Banco de dados gerado pelo Web Scraper*

`pages/Gráficos.py` - *Segunda página do projeto (Em desenvolvimento)*

`scripts/__init__.py` - *Script para o Home.py identificar que há arquivos .py na pasta scripts*

`scripts/analises.py` - *Contém a função que calcula as métricas (média de valores, valor mín e max, oferta, etc.)*  
  
`scripts/coord_bairros.py` - *Contém a função que retorna a coordenada do bairro pelo seu nome*  
  
`scripts/mapa.py` - *Contém a função que cria e clusteriza o mapa*  
  
`scripts/web_scraping.py` - *Contém a função que faz o Scraping de dados e os exporta em CSV*  
  

## **Tecnologias Utilizadas**
  
![Git](https://img.shields.io/badge/Git-F05033?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-000?style=for-the-badge&logo=github&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-77B829?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

## **Desenvolvedor**
  
<div style="display: flex; gap: 20px;">

  <div style="text-align: center;">
    <a href="https://www.linkedin.com/in/imarcososhiro/">
      <img src="https://avatars.githubusercontent.com/u/218446372?v=4" width="150" style="border-radius: 5px;"/>
    </a>
    <br>
    <a href="https://www.linkedin.com/in/imarcososhiro/">
      <strong>Marcos Oshiro</strong>
    </a>
</div>


