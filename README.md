# Histórico de imóveis (branch `data`)

Este branch guarda só dados: um retrato diário dos imóveis para alugar em São Carlos,
coletados pelo scraper do projeto [imobiliario_universitario](https://github.com/imarcososhiro/imobiliario_universitario).
O código fica no branch `main`; este branch não tem histórico em comum com ele.

## Organização

```
snapshots/
├── 2025/
│   ├── 2025-11-11.parquet
│   └── ...
└── 2026/
    └── 2026-10-15.parquet
```

- Um arquivo [Parquet](https://parquet.apache.org/) por dia de coleta, com uma linha por imóvel.
- As colunas são as mesmas do `dados/imoveis.csv` do `main` (veja o dicionário de dados no README de lá).
- Se a coleta rodar mais de uma vez no mesmo dia, vale a última.

## Como ler

Com [DuckDB](https://duckdb.org/), dá para consultar todos os dias de uma vez, direto nos arquivos:

```python
import duckdb

duckdb.sql("""
    SELECT coletado_em, count(*) AS imoveis, median(total_mensal) AS mediana
    FROM 'snapshots/**/*.parquet'
    GROUP BY coletado_em
    ORDER BY coletado_em
""")
```

No `main`, `python -m historico.consultas historico-data/snapshots` mostra um resumo
(imóveis novos, que saíram, mudanças de preço) e `historico/consultas.py` tem as consultas prontas.

## De onde vêm os dados

- **Até 15/10/2026**: reconstruídos com `python -m historico.backfill` a partir das versões do CSV
  que o GitHub Actions commitou no `main`. As versões antigas (scraper com Selenium) foram convertidas
  para o formato atual; campos que o scraper antigo não coletava (área, título, foto...) ficam vazios.
- **Depois**: o workflow diário do `main` grava o snapshot do dia aqui logo após a coleta.

## Cuidados ao analisar

- **Cobertura**: até 14/10/2026 a coleta cobria só ~30 bairros da região universitária, com total de até
  R$ 8000. A partir de 15/10/2026 cobre a cidade toda. Por isso aparecem ~480 imóveis "novos" nesse dia.
- **Dias faltando**: quando a coleta falhou, ou (antes de 15/10/2026) quando o CSV não mudou de um dia
  para o outro, não há arquivo daquele dia.
- **Nomes de bairro**: são os do site, que às vezes escreve o mesmo bairro de jeitos diferentes
  (ex.: "Vila Monteiro (Gleba I)" e "Vila Monteiro Gleba I").
