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

**Observação:** A coleta cobre todos os aluguéis de casas e apartamentos de São Carlos nas imobiliárias Cardinali e Roca; o painel abre mostrando os imóveis a até 3 km da USP, e os filtros mudam o campus e a distância (até a cidade toda).  
  
## **Funcionalidades**

<img alt="status" src="https://img.shields.io/badge/Projeto%20em%20Desenvolvimento-blue?style=for-the-badge">  

✔️ `Dados` - Extrai, diariamente e automaticamente, dados de imóveis para locação com perfil universitário: **apartamentos e casas em bairros próximos à USP e UFSCar, com valor total de até R$ 8000, pensando em desde quem procura morar em condomínios (sozinho ou grupo), até aqueles que procuram novas casas para suas Repúblicas.** 
  
✔️ `Preço por pessoa` - Para cada imóvel: o **preço por pessoa** (quanto cada um pagaria dividindo o imóvel), a **distância** até a USP ou a UFSCar e o **tempo a pé** (veja [Métricas](#métricas)).  

✔️ `Mapa` - Pinta a área de cada bairro pelo preço típico por pessoa, em 5 faixas, com os contornos vindos do OpenStreetMap, os campi e a rodoviária, e um círculo com a distância escolhida. Clicar num bairro mostra os imóveis dele. Ao lado, os bairros mais em conta.  
  
✔️ `Imobiliárias` - Junta os anúncios da **Cardinali** e da **Roca** num lugar só, com o nome da imobiliária em cada cartão e o selo **"Também na Roca?"** quando outra imobiliária parece anunciar o mesmo imóvel (veja [Várias imobiliárias](#várias-imobiliárias)).  

✔️ `Filtros` - No topo da página, como perguntas: onde você estuda, quantos quartos, tipo, imobiliária, até quanto por pessoa e quão perto do campus. Imóveis reservados ficam de fora.  

✔️ `Imóveis` - Cartões com foto, preço por pessoa, total, tempo a pé e quartos (o cartão inteiro leva ao anúncio), ordenáveis (mais barato por pessoa, mais perto, novidades primeiro...), e a tabela completa. No celular, os cartões ficam deitados para caberem mais na tela.  

✔️ `Novidades` - Selos **Novo** (o imóvel apareceu no site nos últimos 7 dias) e **Baixou de preço** (o total por mês caiu nos últimos 7 dias, com o valor antigo riscado) nos cartões, e no topo quantos imóveis novos e quedas de preço houve na semana (veja [Histórico no dashboard](#histórico-no-dashboard)).  



## **Lógica de operação**
1. Utilizando as bibliotecas httpx e BeautifulSoup, foi feito um Web Scraper que percorre as listagens de aluguel de São Carlos no site da Cardinali, a imobiliária mais famosa da cidade, lê a página de cada imóvel (valores, características e dados estruturados JSON-LD) e guarda tudo num arquivo CSV. Como o site é renderizado no servidor, não é preciso abrir um navegador. Na Roca, o scraper lê o sitemap e pede os dados à busca do próprio site, que responde em JSON (veja [Várias imobiliárias](#várias-imobiliárias)).  
2. Com o Github Actions, esse Scraper é executado automaticamente todos os dias. Antes de gravar, ele confere se o resultado faz sentido (taxa de falhas e queda brusca na quantidade de imóveis): se algo parecer quebrado, o CSV anterior é mantido.  
3. A coleta de cada dia também é guardada como um arquivo Parquet no branch `data`, formando um histórico desde nov/2025 (os meses anteriores à mudança foram reconstruídos a partir das versões do CSV no git). Com DuckDB, dá para consultar todos os dias de uma vez em SQL: imóveis novos, que saíram do site, mudanças de preço e evolução por bairro.  
4. Utilizando a biblioteca Folium e Pandas, é feita a criação do mapa e o cálculo das métricas de cada bairro, conforme os dados do CSV coletado. Os contornos dos bairros vêm do OpenStreetMap (veja [Mapa dos bairros](#mapa-dos-bairros)).  
5. No Web App gerado pela biblioteca Streamlit, é feita a exibição do mapa e do banco de dados, a criação das sessões de filtros, e a personalização do layout. O dashboard também baixa o histórico do branch `data` para mostrar as novidades (veja [Histórico no dashboard](#histórico-no-dashboard)).  
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
├── 📂 scraper  
│    ├── 📄 __main__.py  
│    ├── 📄 alertas.py  
│    ├── 📄 cardinali.py  
│    ├── 📄 coleta.py  
│    ├── 📄 conversao.py  
│    ├── 📄 download.py  
│    ├── 📄 modelo.py  
│    └── 📄 roca.py  
└── 📂 tests  
     ├── 📂 fixtures  
     └── 📄 test_*.py  
```
  
`Home.py` - *A página do dashboard: filtros, números, mapa, bairros mais em conta e os imóveis*  

`requirements.txt` / `requirements-scraper.txt` / `requirements-dev.txt` - *Dependências do dashboard (usadas pelo Streamlit Cloud), do scraper (usadas pelo GitHub Actions) e de desenvolvimento (testes), separadas para cada ambiente instalar só o que precisa*

`.github/workflows/main.yml` - *Agendamento diário do scraper no GitHub Actions, commit do CSV atualizado e os avisos quando algo quebra (veja [Operação](#operação))*

`.github/workflows/testes.yml` - *Roda os testes automaticamente em cada pull request*

`.streamlit/config.toml` - *Arquivo que contém as settings de personalização do App Streamlit (cores, fontes, tamanhos, etc.)*

`app/bairros.py` - *Lê os contornos dos bairros, unifica os nomes e mede distâncias*  
  
`app/dados.py` - *Lê o CSV do scraper (só imóveis residenciais com total de até R$ 8000) e aplica os filtros*  

`app/metricas.py` - *Calcula o preço por pessoa, a área, a distância a cada campus e o resumo por bairro*  

`app/formatacao.py` - *Escreve os números no formato brasileiro (R$ 1.234, 2,3 km)*  

`app/historico.py` - *Baixa o histórico do branch `data` e marca os imóveis novos e os que baixaram de preço*  

`app/interface.py` - *Peças da página: filtros, números do resumo, bairros mais em conta, cartões e tabela (com o CSS dos cartões)*  
  
`app/mapa.py` - *Cria o mapa: bairros pintados pelo preço típico por pessoa, etiquetas dos campi e da rodoviária e o círculo da distância*  

`dados/geo/` - *Contornos dos bairros e as correções manuais (veja [Mapa dos bairros](#mapa-dos-bairros))*  

`geo/` - *Gera o `dados/geo/bairros.geojson` a partir do OpenStreetMap (`python -m geo.gerar`)*  

`assets/` - *Imagem usada quando nenhum imóvel passa pelos filtros*

`dados/imoveis.csv` - *Banco de dados gerado pelo Web Scraper (veja o dicionário de dados abaixo)*


`scraper/cardinali.py` - *Lê as páginas de listagem e de cada imóvel do site da Cardinali*  

`scraper/roca.py` - *Lê o sitemap da Roca e busca os dados dos imóveis em lotes, na busca em JSON do site*  

`scraper/coleta.py` - *Orquestra a coleta (`python -m scraper`), confere o resultado e grava o CSV*  

`scraper/download.py` - *Baixa as páginas, tentando de novo quando o site falha temporariamente*  

`scraper/modelo.py` - *Formato comum dos imóveis, igual para qualquer imobiliária*  

`scraper/alertas.py` - *Abre uma issue quando a coleta diária quebra e fecha quando ela volta (só usa a biblioteca padrão do Python)*  

`historico/snapshot.py` - *Converte a coleta do dia num arquivo Parquet com esquema fixo (`snapshots/AAAA/AAAA-MM-DD.parquet` no branch `data`)*  

`historico/backfill.py` - *Reconstrói o histórico a partir das versões do CSV guardadas no git, convertendo o formato antigo*  

`historico/consultas.py` - *Consultas em SQL (DuckDB) sobre todos os dias: resumo por imóvel, mudanças de preço, novidades do dia, série por bairro e a última observação de cada imóvel por semana (usadas também pelo dashboard)*  

`tests/` - *Testes automatizados com páginas reais salvas em `tests/fixtures`. Para salvar uma página nova: `python -m tests.salvar_fixture <url> <nome>`*  

### **Dicionário de dados (`dados/imoveis.csv`)**

| Coluna | Descrição |
|---|---|
| `codigo` | Código do imóvel no site (identifica o mesmo imóvel ao longo dos dias) |
| `fonte` | Imobiliária de origem (`cardinali` ou `roca`). O código só identifica o imóvel junto com a fonte |
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
  

## **Métricas**

Poucas e simples, para ninguém precisar pensar demais:

| Métrica | Como é calculada | Por que importa |
|---|---|---|
| Preço por pessoa | total por mês (aluguel + condomínio + IPTU) ÷ nº de quartos | É o que cada um pagaria dividindo o imóvel: compara de forma justa uma kitnet e uma casa de república |
| Preço típico | a mediana: metade dos imóveis custa menos, metade custa mais | Diferente da média, não se deixa levar por um anúncio caríssimo |
| Distância | em linha reta, do bairro até o campus escolhido | O site não informa o endereço dos imóveis, então todos os imóveis de um bairro têm a mesma distância |
| Tempo a pé | distância + 30% (as ruas fazem curvas), a 4,8 km/h, arredondado de 5 em 5 minutos | "~20 min a pé" é mais fácil de imaginar que "1,2 km" |

No mapa, cada bairro mostra o preço típico por pessoa, em **5 faixas com quantidades parecidas de bairros** (e não divididas por igual entre o mais barato e o mais caro): assim um bairro caríssimo não deixa todos os outros com a mesma cor. A lista de bairros mais em conta só inclui bairros com pelo menos 3 imóveis. Imóveis só comerciais e reservados ficam de fora.

## **Várias imobiliárias**

Cada imobiliária é um módulo em `scraper/` que converte os anúncios para o mesmo formato (`scraper/modelo.py`), com a coluna `fonte` dizendo de onde veio cada um. Assim o dashboard, o histórico e as métricas tratam todas do mesmo jeito.

| Imobiliária | Como é coletada | Pedidos por dia |
|---|---|---|
| [Cardinali](https://www.cardinali.com.br) | Listagens de aluguel e a página de cada imóvel (HTML renderizado no servidor) | ~1.000 |
| [Roca](https://roca.com.br) | O sitemap (indicado no `robots.txt`) lista os imóveis; a busca do próprio site (`/api/solr/search/`) devolve os dados em JSON, em lotes de 200 | ~8 |

Os dois `robots.txt` permitem a coleta. Da Roca entram as casas e apartamentos para alugar em São Carlos; ficam de fora os que o site marca como "não aluga para estudantes" e as casas de uso comercial. O endereço completo que a busca da Roca devolve **não é guardado**: o projeto fica no nível do bairro.

- **Tudo ou nada**: se uma imobiliária falhar, o CSV do dia não é gravado (e o [aviso por issue](#operação) dispara). Gravar só as outras faria os imóveis dela "saírem" do site por um dia no histórico.
- **Validação por imobiliária**: a queda de mais de 30% é medida em cada uma, para uma queda forte numa não ficar escondida no total.
- **Estreia**: no primeiro dia de uma imobiliária no histórico, os imóveis dela não ganham o selo **Novo** (eles aparecem "pela primeira vez" sem serem novos).
- **Possível duplicata**: o mesmo imóvel às vezes é anunciado pelas duas. Quando outra imobiliária tem um anúncio no mesmo bairro, com o mesmo nº de quartos, área até 3% e total até 5% diferentes, o cartão ganha o selo **"Também na Roca?"** (ou na Cardinali). O painel só avisa e nunca junta os anúncios: pode ser coincidência, e o preço pode ser diferente em cada uma.

**Para incluir outra imobiliária**: crie `scraper/<nome>.py` com `FONTE` e um jeito de coletar (`listar_urls` + `extrair_imovel`, página por página, como a Cardinali; ou `baixar_imoveis`, em lote, como a Roca), acrescente o módulo em `FONTES` (`scraper/coleta.py`) e o nome em `IMOBILIARIAS` (`app/dados.py`), e escreva os testes com fixtures salvas do site.

## **Histórico no dashboard**

O histórico fica no branch `data` (um Parquet por dia), mas o Streamlit Cloud só tem o branch `main`. Por isso o dashboard **baixa o branch `data` inteiro como um `.tar.gz`** direto do GitHub (`codeload.github.com/.../tar.gz/refs/heads/data`, poucos MB, um pedido só), extrai os Parquet numa pasta temporária e consulta tudo com DuckDB, reaproveitando `historico/consultas.py`. O resultado fica em cache por 3 horas (`st.cache_data`), então o download acontece poucas vezes por dia, e não a cada visita.

Se o download falhar (GitHub fora do ar, sem internet), **o dashboard continua funcionando**: só não mostra os selos nem os números de novidades, e avisa que o histórico não pôde ser carregado.

| O que aparece | Regra |
|---|---|
| Selo **Novo** | O imóvel foi visto pela primeira vez nos últimos 7 dias |
| Selo **Baixou de preço** | A última mudança do total por mês foi uma queda, nos últimos 7 dias, e o preço de hoje ainda é o da queda. O valor de antes aparece riscado |
| **Novos esta semana** e **Baixaram de preço** | Quantos imóveis com cada selo passam pelos filtros escolhidos |

**Cuidado com 15/10/2026:** até 14/10/2026 a coleta cobria só ~30 bairros da região universitária; a partir de 15/10 cobre a cidade toda. Nesse dia, ~480 imóveis aparecem "pela primeira vez" sem serem novos de verdade, então ninguém que apareceu nesse dia (nem no primeiro dia do histórico) ganha o selo Novo.

Para testar sem internet, a variável de ambiente `HISTORICO_URL` troca o endereço do histórico (os testes apontam para um `.tar.gz` sintético, `file:///...`).

## **Mapa dos bairros**

São Carlos não tem bairros oficializados em lei (por isso não aparece na malha de bairros do IBGE). Os contornos vêm do [OpenStreetMap](https://www.openstreetmap.org/), onde a maioria dos bairros (loteamentos) da cidade está desenhada. O arquivo `dados/geo/bairros.geojson` é gerado por `python -m geo.gerar` e diz de onde veio cada contorno (`origem`):

| `origem` | O que é |
|---|---|
| `osm` | Contorno desenhado no OpenStreetMap |
| `enderecos` | O bairro só tem um ponto no OSM; o contorno envolve os endereços do OSM marcados com esse bairro (é o caso do Centro) |
| `aproximado` | Sem endereços suficientes: a área em volta do ponto do bairro (até 700 m) que nenhum bairro vizinho ocupa |
| `manual` | Desenhado à mão em `dados/geo/desenhos_manuais.geojson` |

Os contornos calculados (`enderecos` e `aproximado`) são **ajustados às quadras**: o gerador monta os quarteirões a partir das ruas do OSM e troca cada contorno pela união das quadras que ele cobre em mais da metade, para que as bordas sigam as ruas. Alguns condomínios estão no OSM só como área residencial (`landuse=residential`); eles entram no mapa quando têm imóveis e nenhum outro contorno.

O gerador também guarda em cada bairro a distância da borda até o campus mais perto (`distancia_campus_km`). No mapa do dashboard, o fundo é o OpenStreetMap em tons de cinza (um filtro CSS nos tiles), para as cores dos bairros se destacarem.

**Como corrigir um bairro** (depois, rode `python -m geo.gerar` de novo):
- *O site escreve o nome diferente do mapa* (ex.: "Jardim Hikari" e "Jardim Hikare"): adicione uma linha em `dados/geo/aliases_bairros.csv`.
- *O ponto do bairro está no lugar errado*: ajuste em `dados/geo/pontos_manuais.csv` (latitude e longitude, que dá para copiar do Google Maps). Esses pontos valem mais que os do OSM.
- *O contorno está ruim ou não existe*: desenhe o bairro no [geojson.io](https://geojson.io), dê a ele a propriedade `"bairro": "Nome do Bairro"` e cole a feature em `dados/geo/desenhos_manuais.geojson`.

No fim, o gerador lista os bairros com imóveis que ficaram sem contorno: os imóveis deles continuam na tabela, só não aparecem no mapa.

## **Operação**

A coleta roda sozinha todo dia às 18h (horário de Brasília) no GitHub Actions. Para saber se ela está saudável sem precisar abrir o Actions:

- **Resumo da execução**: a página de cada execução mostra uma tabela com os imóveis anunciados e coletados, o que mudou desde a última coleta (novos, saíram, mudaram de preço), as falhas, as novas tentativas de download e a duração. Muitas novas tentativas, mesmo sem falhas, indicam que o site ou a conexão andam instáveis.
- **Se algo quebrar**:
  - o CSV anterior é mantido, então o dashboard continua mostrando a última coleta que deu certo;
  - uma **issue com o rótulo `coleta-quebrada`** é aberta (ou ganha um comentário, se já houver uma aberta), com o link da execução, a etapa que falhou e o fim do log. O GitHub avisa por e-mail quem acompanha o repositório;
  - o HTML das páginas que o scraper não conseguiu ler fica 14 dias no artefato **`paginas-com-falha`** da execução, junto de um `falhas.csv` (URL, motivo e arquivo de cada falha).
- **Quando voltar a funcionar**, a issue ganha um comentário e é fechada sozinha.

**Como investigar uma falha:** baixe o artefato `paginas-com-falha`, abra o HTML e veja o que mudou no site. Para transformar o caso em teste, salve a página como fixture (`python -m tests.salvar_fixture <url> <nome>`), escreva um teste que falha e ajuste o adaptador da imobiliária (`scraper/cardinali.py` ou `scraper/roca.py`). Para rodar a coleta na hora: aba Actions → *Atualizacao de banco de dados imobiliarios* → *Run workflow*. Localmente, `python -m scraper --falhas falhas` guarda o HTML das falhas na pasta `falhas/`.

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


