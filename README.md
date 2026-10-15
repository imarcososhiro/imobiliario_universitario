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
#### ***• Para explorar o histórico diário (fica no branch `data`)***
```bash
git fetch origin data
git worktree add historico-data data
python -m historico.consultas historico-data/snapshots
  ```

## **Descrição**  
Este projeto propõe fazer uma raspagem de dados de apartamentos nas regiões próximas à USP e UFSCar, na cidade de São Carlos/SP, para exibí-los por meio de um mapa interativo. Assim, pode-se analisar os bairros com melhor valor e oferta de imóveis para um ou mais estudantes morarem, permitindo filtrar pelo tipo de imóvel, bairro, nº de dormitórios, e faixa de preço.  
  
⚠️ **Disclaimer:** Esse projeto é puramente para fins educacionais e acadêmicos. Os dados foram coletados de forma pública, sem violar nenhum termo de uso do site. Nenhum dado pessoal foi armazenado.  
  
<p align="center">
  <a href="https://imobiliariouniversitario.streamlit.app/" target="_blank">
     
  <img width="712" height="569" alt="Screenshot_5" src="https://github.com/user-attachments/assets/1e057fdf-c471-4498-8b49-e7268802fb82" />

  </a>
</p> 

**Observação:** A coleta cobre todos os aluguéis de São Carlos na imobiliária; o painel abre focado na região universitária, e um filtro mostra a cidade toda.  
  
## **Funcionalidades**

<img alt="status" src="https://img.shields.io/badge/Projeto%20em%20Desenvolvimento-blue?style=for-the-badge">  

✔️ `Dados` - Extrai, diariamente e automaticamente, dados de imóveis para locação com perfil universitário: **apartamentos e casas em bairros próximos à USP e UFSCar, com valor total de até R$ 8000, pensando em desde quem procura morar em condomínios (sozinho ou grupo), até aqueles que procuram novas casas para suas Repúblicas.** 
  
✔️ `Custo-benefício` - Para cada imóvel: **custo por dormitório** (quanto cada morador pagaria dividindo o imóvel), **preço por m²**, **distância** até a USP ou a UFSCar e um **índice de custo-benefício** de 0 a 100 com pesos ajustáveis (veja [Métricas de custo-benefício](#métricas-de-custo-benefício)).  

✔️ `Mapa` - Pinta a área de cada bairro pela métrica escolhida (índice, custo por dormitório, aluguel total, preço por m² ou oferta), com os contornos vindos do OpenStreetMap. Clicar num bairro mostra os imóveis dele.  
  
✔️ `Filtros` - Campus onde você estuda, área (região universitária ou cidade toda), tipo, nº de dormitórios, faixa de preço e imóveis reservados.  

✔️ `Imóveis` - Cartões com foto, valores e índice de cada imóvel, ordenáveis (melhor custo-benefício, mais barato por dormitório, mais perto, novidades primeiro...), e a tabela completa com link para o anúncio.  

✔️ `Novidades` - Selos **Novo** (o imóvel apareceu no site nos últimos 7 dias) e **Baixou de preço** (o total por mês caiu nos últimos 7 dias, com o valor antigo riscado) nos cartões, e uma linha com quantos imóveis novos apareceram na semana (veja [Histórico no dashboard](#histórico-no-dashboard)).  

✔️ `Gráficos` - Segunda página: custo por dormitório em cada bairro, a relação entre distância e preço e a **tendência dos aluguéis** semana a semana (custo por dormitório ou aluguel total), com a opção de comparar um bairro com a região.
  

## **Lógica de operação**
1. Utilizando as bibliotecas httpx e BeautifulSoup, foi feito um Web Scraper que percorre as listagens de aluguel de São Carlos no site da imobiliária mais famosa da cidade, lê a página de cada imóvel (valores, características e dados estruturados JSON-LD) e guarda tudo num arquivo CSV. Como o site é renderizado no servidor, não é preciso abrir um navegador.  
2. Com o Github Actions, esse Scraper é executado automaticamente todos os dias. Antes de gravar, ele confere se o resultado faz sentido (taxa de falhas e queda brusca na quantidade de imóveis): se algo parecer quebrado, o CSV anterior é mantido.  
3. A coleta de cada dia também é guardada como um arquivo Parquet no branch `data`, formando um histórico desde nov/2025 (os meses anteriores à mudança foram reconstruídos a partir das versões do CSV no git). Com DuckDB, dá para consultar todos os dias de uma vez em SQL: imóveis novos, que saíram do site, mudanças de preço e evolução por bairro.  
4. Utilizando a biblioteca Folium e Pandas, é feita a criação do mapa e o cálculo das métricas de cada bairro, conforme os dados do CSV coletado. Os contornos dos bairros vêm do OpenStreetMap (veja [Mapa dos bairros](#mapa-dos-bairros)).  
5. No Web App gerado pela biblioteca Streamlit, é feita a exibição do mapa e do banco de dados, a criação das sessões de filtros, e a personalização do layout. O dashboard também baixa o histórico do branch `data` para mostrar as novidades e a tendência dos preços (veja [Histórico no dashboard](#histórico-no-dashboard)).  
6. A cada filtro aplicado, todas as métricas e exibições são refeitas e reexibidas conforme a solicitação.  

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
│    ├── 📄 bairros.py  
│    ├── 📄 dados.py  
│    ├── 📄 formatacao.py  
│    ├── 📄 historico.py  
│    ├── 📄 interface.py  
│    ├── 📄 mapa.py   
│    └── 📄 metricas.py  
├── 📂 assets  
├── 📂 dados  
│    ├── 📄 imoveis.csv  
│    └── 📂 geo  
│         ├── 📄 bairros.geojson  
│         ├── 📄 aliases_bairros.csv  
│         ├── 📄 pontos_manuais.csv  
│         └── 📄 desenhos_manuais.geojson  
├── 📂 geo  
│    ├── 📄 gerar.py  
│    ├── 📄 nomes.py  
│    └── 📄 osm.py  
├── 📂 historico  
│    ├── 📄 backfill.py  
│    ├── 📄 consultas.py  
│    └── 📄 snapshot.py  
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
  
`Home.py` - *Página principal: indicadores, mapa, ranking dos bairros e os imóveis*  

`pages/Gráficos.py` - *Segunda página, com os gráficos*  

`requirements.txt` / `requirements-scraper.txt` / `requirements-dev.txt` - *Dependências do dashboard (usadas pelo Streamlit Cloud), do scraper (usadas pelo GitHub Actions) e de desenvolvimento (testes), separadas para cada ambiente instalar só o que precisa*

`.github/workflows/main.yml` - *Agendamento diário do scraper no GitHub Actions e commit do CSV atualizado*

`.github/workflows/testes.yml` - *Roda os testes automaticamente em cada pull request*

`.streamlit/config.toml` - *Arquivo que contém as settings de personalização do App Streamlit (cores, fontes, tamanhos, etc.)*

`app/bairros.py` - *Lê os contornos dos bairros, unifica os nomes e define a região universitária (bairros que chegam a até 2,2 km da USP ou da UFSCar)*  
  
`app/dados.py` - *Lê o CSV do scraper (só imóveis residenciais com total de até R$ 8000) e aplica os filtros*  

`app/metricas.py` - *Calcula custo por dormitório, preço por m², distância ao campus, índice de custo-benefício e o resumo por bairro*  

`app/formatacao.py` - *Escreve os números no formato brasileiro (R$ 1.234, 2,3 km)*  

`app/historico.py` - *Baixa o histórico do branch `data`, marca os imóveis novos e os que baixaram de preço e calcula a tendência semanal*  

`app/interface.py` - *Peças da interface usadas pelas duas páginas: barra lateral, indicadores, ranking e cartões*  
  
`app/mapa.py` - *Cria o mapa e pinta cada bairro conforme a métrica escolhida*  

`dados/geo/` - *Contornos dos bairros e as correções manuais (veja [Mapa dos bairros](#mapa-dos-bairros))*  

`geo/` - *Gera o `dados/geo/bairros.geojson` a partir do OpenStreetMap (`python -m geo.gerar`)*  

`assets/` - *Imagens usadas no dashboard (logos e ícones do mapa)*

`dados/imoveis.csv` - *Banco de dados gerado pelo Web Scraper (veja o dicionário de dados abaixo)*

`pages/Gráficos.py` - *Segunda página do projeto (Em desenvolvimento)*
  
`scraper/cardinali.py` - *Lê as páginas de listagem e de cada imóvel do site da Cardinali*  

`scraper/coleta.py` - *Orquestra a coleta (`python -m scraper`), confere o resultado e grava o CSV*  

`scraper/download.py` - *Baixa as páginas, tentando de novo quando o site falha temporariamente*  

`scraper/modelo.py` - *Formato comum dos imóveis, igual para qualquer imobiliária*  

`historico/snapshot.py` - *Converte a coleta do dia num arquivo Parquet com esquema fixo (`snapshots/AAAA/AAAA-MM-DD.parquet` no branch `data`)*  

`historico/backfill.py` - *Reconstrói o histórico a partir das versões do CSV guardadas no git, convertendo o formato antigo*  

`historico/consultas.py` - *Consultas em SQL (DuckDB) sobre todos os dias: resumo por imóvel, mudanças de preço, novidades do dia, série por bairro e a última observação de cada imóvel por semana (usadas também pelo dashboard)*  

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
  

## **Métricas de custo-benefício**

| Métrica | Como é calculada | Por que importa |
|---|---|---|
| Custo por dormitório | total por mês (aluguel + condomínio + IPTU) ÷ nº de dormitórios | É o que cada morador pagaria dividindo o imóvel: compara de forma justa uma kitnet e uma casa de república |
| Preço por m² | total por mês ÷ área útil (ou construída, quando o site só informa essa) | Mostra quanto espaço o dinheiro compra |
| Distância | em linha reta, do bairro até o campus escolhido | O site não informa o endereço dos imóveis, então todos os imóveis de um bairro têm a mesma distância |
| Índice custo-benefício | média ponderada das três notas acima, de 0 a 100 | Em cada critério, o melhor imóvel da tela ganha nota 100 e o pior, 0 (pela posição no ranking, para um anúncio fora da curva não achatar os outros). Os pesos são ajustáveis na barra lateral |

O índice compara os imóveis **que estão na tela** entre si, por isso muda quando os filtros mudam. No mapa e no ranking, cada bairro mostra a **mediana** dos seus imóveis, e o ranking só inclui bairros com pelo menos 3 imóveis. Imóveis só comerciais ficam de fora, e os reservados aparecem apenas se o filtro pedir.

## **Histórico no dashboard**

O histórico fica no branch `data` (um Parquet por dia), mas o Streamlit Cloud só tem o branch `main`. Por isso o dashboard **baixa o branch `data` inteiro como um `.tar.gz`** direto do GitHub (`codeload.github.com/.../tar.gz/refs/heads/data`, poucos MB, um pedido só), extrai os Parquet numa pasta temporária e consulta tudo com DuckDB, reaproveitando `historico/consultas.py`. O resultado fica em cache por 3 horas (`st.cache_data`), então o download acontece poucas vezes por dia, e não a cada visita.

Se o download falhar (GitHub fora do ar, sem internet), **o dashboard continua funcionando**: só não mostra os selos nem a tendência, e avisa que o histórico não pôde ser carregado.

| O que aparece | Regra |
|---|---|
| Selo **Novo** | O imóvel foi visto pela primeira vez nos últimos 7 dias |
| Selo **Baixou de preço** | A última mudança do total por mês foi uma queda, nos últimos 7 dias, e o preço de hoje ainda é o da queda. O valor de antes aparece riscado |
| **N imóveis novos esta semana** | Quantos imóveis com o selo Novo passam pelos filtros escolhidos |
| **Tendência** | Mediana por semana (de segunda a domingo), contando cada imóvel uma vez por semana, com os mesmos filtros da barra lateral. Semanas com menos de 3 imóveis ficam de fora |

**Cuidado com 15/10/2026:** até 14/10/2026 a coleta cobria só ~30 bairros da região universitária; a partir de 15/10 cobre a cidade toda. Nesse dia, ~480 imóveis aparecem "pela primeira vez" sem serem novos de verdade, então ninguém que apareceu nesse dia (nem no primeiro dia do histórico) ganha o selo Novo. No gráfico de tendência, uma linha pontilhada marca essa semana, porque parte da mudança nela vem da cobertura maior.

Para testar sem internet, a variável de ambiente `HISTORICO_URL` troca o endereço do histórico (os testes apontam para um `.tar.gz` sintético, `file:///...`).

## **Mapa dos bairros**

São Carlos não tem bairros oficializados em lei (por isso não aparece na malha de bairros do IBGE). Os contornos vêm do [OpenStreetMap](https://www.openstreetmap.org/), onde a maioria dos bairros (loteamentos) da cidade está desenhada. O arquivo `dados/geo/bairros.geojson` é gerado por `python -m geo.gerar` e diz de onde veio cada contorno (`origem`):

| `origem` | O que é |
|---|---|
| `osm` | Contorno desenhado no OpenStreetMap |
| `enderecos` | O bairro só tem um ponto no OSM; o contorno envolve os endereços do OSM marcados com esse bairro (é o caso do Centro) |
| `aproximado` | Sem endereços suficientes: a área em volta do ponto do bairro (até 700 m) que nenhum bairro vizinho ocupa |

Os contornos calculados (`enderecos` e `aproximado`) são **ajustados às quadras**: o gerador monta os quarteirões a partir das ruas do OSM e troca cada contorno pela união das quadras que ele cobre em mais da metade, para que as bordas sigam as ruas. Alguns condomínios estão no OSM só como área residencial (`landuse=residential`); eles entram no mapa quando têm imóveis e nenhum outro contorno.

A **região universitária** são os bairros que chegam a até 2,2 km da USP ou da UFSCar, medindo pela borda do bairro (campo `distancia_campus_km` do GeoJSON).
| `manual` | Desenhado à mão em `dados/geo/desenhos_manuais.geojson` |

**Como corrigir um bairro** (depois, rode `python -m geo.gerar` de novo):
- *O site escreve o nome diferente do mapa* (ex.: "Jardim Hikari" e "Jardim Hikare"): adicione uma linha em `dados/geo/aliases_bairros.csv`.
- *O ponto do bairro está no lugar errado*: ajuste em `dados/geo/pontos_manuais.csv` (latitude e longitude, que dá para copiar do Google Maps). Esses pontos valem mais que os do OSM.
- *O contorno está ruim ou não existe*: desenhe o bairro no [geojson.io](https://geojson.io), dê a ele a propriedade `"bairro": "Nome do Bairro"` e cole a feature em `dados/geo/desenhos_manuais.geojson`.

No fim, o gerador lista os bairros com imóveis que ficaram sem contorno: os imóveis deles continuam na tabela, só não aparecem no mapa.

## **Tecnologias Utilizadas**
  
![Git](https://img.shields.io/badge/Git-F05033?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-000?style=for-the-badge&logo=github&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-1F2937?style=for-the-badge)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4B8BBE?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![Folium](https://img.shields.io/badge/Folium-77B829?style=for-the-badge)
![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-7EBC6F?style=for-the-badge&logo=openstreetmap&logoColor=white)
![Shapely](https://img.shields.io/badge/Shapely-3F7CAC?style=for-the-badge)
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


