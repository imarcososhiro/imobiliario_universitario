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

 <h3 align="center"> Se um aviso como esse abaixo aparecer, clique no botão azul e espere o site carregar  <br><br/>
  <img width="500" height="489" alt="Pagina" src="https://github.com/user-attachments/assets/d157527a-6d22-4c69-ba91-39a52e976e56" />  

---

## **Rodando localmente**
#### ***• No seu terminal***
```bash
git clone https://github.com/imarcososhiro/imobiliario_universitario
cd imobiliario_universitario
pip install -r requirements.txt
streamlit run Home.py
  ```
#### ***• Para atualizar o banco de dados manualmente (leva poucos minutos)***
```bash
pip install -r requirements-scraper.txt
python -m scraper
  ```
#### ***• Para rodar os testes (usam páginas salvas, sem acessar o site)***
```bash
pip install -r requirements-dev.txt
python -m pytest
  ```

## **Descrição**  
Este projeto propõe fazer uma raspagem de dados de apartamentos nas regiões próximas à USP e UFSCar, na cidade de São Carlos/SP, para exibí-los por meio de um mapa interativo. Assim, pode-se analisar os bairros com melhor valor e oferta de imóveis para um ou mais estudantes morarem, permitindo filtrar pelo tipo de imóvel, bairro, nº de dormitórios, e faixa de preço.  
  
⚠️ **Disclaimer:** Esse projeto é puramente para fins educacionais e acadêmicos. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.  
  
<p align="center">
  <a href="https://imobiliariouniversitario.streamlit.app/" target="_blank">
     
  <img width="712" height="569" alt="Screenshot_5" src="https://github.com/user-attachments/assets/1e057fdf-c471-4498-8b49-e7268802fb82" />

  </a>
</p> 

**Observação:** Ainda falta adicionar dados de mais bairros ao sistema, porém o programa já funciona para boa parte dos bairros da região.  
  
## **Funcionalidades**

<img alt="status" src="https://img.shields.io/badge/Projeto%20em%20Desenvolvimento-blue?style=for-the-badge">  

✔️ `Dados` - Extrai, diariamente e automaticamente, dados de imóveis para locação com perfil universitário: **apartamentos e casas em bairros próximos à USP e UFSCar, com valor total de até R$ 8000, pensando em desde quem procura morar em condomínios (sozinho ou grupo), até aqueles que procuram novas casas para suas Repúblicas.** 
  
✔️ `Mapa` - Exibe as métricas de cada bairro (quantidade de imóveis disponíveis, valor médio, mínimo e máximo) em um **mapa interativo clusterizado.**  
  
✔️ `Filtros` - Permite a filtragem do perfil de imóvel desejado pelo seu tipo, bairro, nº de dormitórios e faixa de preço.  

✔️ `Tabela` - Conforme o filtro aplicado, exibe em uma tabela os detalhes de todos os imóveis por bairro (Link do anúncio, valor do aluguel, condomínio, nº de dormitórios, etc.).  
  
<img width="1033" height="431" alt="Screenshot_4" src="https://github.com/user-attachments/assets/9475e134-3a95-466f-b2a9-fc132ddfd75f" />


  
🟡 `Gráficos` - Segunda página com análises gráficas dos dados.
  

## **Lógica de operação**
1. Utilizando as bibliotecas httpx e BeautifulSoup, foi feito um Web Scraper que percorre as listagens de aluguel de São Carlos no site da imobiliária mais famosa da cidade, lê a página de cada imóvel (valores, características e dados estruturados JSON-LD) e guarda tudo num arquivo CSV. Como o site é renderizado no servidor, não é preciso abrir um navegador.  
2. Com o Github Actions, esse Scraper é executado automaticamente todos os dias. Antes de gravar, ele confere se o resultado faz sentido (taxa de falhas e queda brusca na quantidade de imóveis): se algo parecer quebrado, o CSV anterior é mantido.  
3. Utilizando a biblioteca Folium e Pandas, é feita a criação do mapa clusterizado e o cálculo das métricas de cada bairro, conforme os dados do CSV coletado.  
4. No Web App gerado pela biblioteca Streamlit, é feita a exibição do mapa e do banco de dados, a criação das sessões de filtros, e a personalização do layout.  
5. A cada filtro aplicado, todas as métricas e exibições são refeitas e reexibidas conforme a solicitação.  

## **Estrutura do projeto**
### **Descrição simples dos principais 📄 arquivos do sistema**
```bash
📂 imobiliario_universitario  
├── 📄 Home.py
├── 📄 requirements.txt
├── 📄 requirements-scraper.txt
├── 📄 requirements-dev.txt
│
├── 📂 .github/workflows  
│    ├── 📄 main.yml  
│    └── 📄 testes.yml  
├── 📂 .streamlit  
│    └── 📄 config.toml  
├── 📂 app  
│    ├── 📄 analises.py  
│    ├── 📄 coord_bairros.py  
│    ├── 📄 dados.py  
│    └── 📄 mapa.py   
├── 📂 assets  
├── 📂 dados  
│    └── 📄 imoveis.csv  
├── 📂 pages  
│    └── 📄 Gráficos.py  
├── 📂 scraper  
│    ├── 📄 __main__.py  
│    ├── 📄 cardinali.py  
│    ├── 📄 coleta.py  
│    ├── 📄 conversao.py  
│    ├── 📄 download.py  
│    └── 📄 modelo.py  
└── 📂 tests  
     ├── 📂 fixtures  
     └── 📄 test_*.py  
```
  
`Home.py` - *Arquivo principal. Recebe e aplica os filtros solicitados pelo usuário, plota o mapa interativo e a tabela de detalhamento dos imóveis*  

`requirements.txt` / `requirements-scraper.txt` / `requirements-dev.txt` - *Dependências do dashboard (usadas pelo Streamlit Cloud), do scraper (usadas pelo GitHub Actions) e de desenvolvimento (testes), separadas para cada ambiente instalar só o que precisa*

`.github/workflows/main.yml` - *Agendamento diário do scraper no GitHub Actions e commit do CSV atualizado*

`.github/workflows/testes.yml` - *Roda os testes automaticamente em cada pull request*

`.streamlit/config.toml` - *Arquivo que contém as settings de personalização do App Streamlit (cores, fontes, tamanhos, etc.)*

`app/analises.py` - *Contém a função que calcula as métricas (média de valores, valor mín e max, oferta, etc.)*  
  
`app/coord_bairros.py` - *Contém a função que retorna a coordenada do bairro pelo seu nome*  
  
`app/dados.py` - *Lê o CSV do scraper e o deixa no formato do dashboard (recorte da região universitária, teto de R$ 8000)*  
  
`app/mapa.py` - *Contém a função que cria e clusteriza o mapa*  

`assets/` - *Imagens usadas no dashboard (logos e ícones do mapa)*

`dados/imoveis.csv` - *Banco de dados gerado pelo Web Scraper (veja o dicionário de dados abaixo)*

`pages/Gráficos.py` - *Segunda página do projeto (Em desenvolvimento)*
  
`scraper/cardinali.py` - *Lê as páginas de listagem e de cada imóvel do site da Cardinali*  

`scraper/coleta.py` - *Orquestra a coleta (`python -m scraper`), confere o resultado e grava o CSV*  

`scraper/download.py` - *Baixa as páginas, tentando de novo quando o site falha temporariamente*  

`scraper/modelo.py` - *Formato comum dos imóveis, igual para qualquer imobiliária*  

`tests/` - *Testes automatizados com páginas reais salvas em `tests/fixtures`. Para salvar uma página nova: `python -m tests.salvar_fixture <url> <nome>`*  

### **Dicionário de dados (`dados/imoveis.csv`)**

| Coluna | Descrição |
|---|---|
| `codigo` | Código do imóvel no site (identifica o mesmo imóvel ao longo dos dias) |
| `fonte` | Imobiliária de origem |
| `url` | Link do anúncio |
| `tipo` / `subtipo` | Ex.: Apartamento / Kitchnet; Casa / Sobrado |
| `bairro` | Bairro como escrito no site |
| `titulo` | Título do anúncio |
| `finalidade` | Residencial, Comercial ou ambos |
| `situacao` | Ex.: DISPONÍVEL |
| `aluguel` | Aluguel atual, sem desconto |
| `aluguel_anterior` | Preço "DE:" quando o imóvel está em promoção |
| `aluguel_bonificado` | Aluguel com desconto por pagar em dia |
| `condominio` / `iptu` | Valores mensais |
| `total_mensal` | Total por mês informado pelo site (vazio quando o aluguel é "Consulte-nos") |
| `dormitorios` / `suites` / `banheiros` / `vagas` | Características |
| `area_util_m2` / `area_construida_m2` / `area_total_m2` | Áreas em m² |
| `foto_url` | Primeira foto do anúncio |
| `coletado_em` | Data da coleta |
  

## **Tecnologias Utilizadas**
  
![Git](https://img.shields.io/badge/Git-F05033?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-000?style=for-the-badge&logo=github&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-1F2937?style=for-the-badge)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4B8BBE?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
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


