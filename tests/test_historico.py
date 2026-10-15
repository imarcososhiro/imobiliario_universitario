"""Testes do histórico: snapshots Parquet, backfill a partir do git e consultas DuckDB."""
import csv
import os
import subprocess
from datetime import date

import duckdb
import pytest

from historico import consultas
from historico.backfill import NomesDoSite, imovel_do_formato_antigo, reconstruir
from historico.snapshot import salvar_snapshot
from scraper.coleta import salvar_csv
from scraper.modelo import COLUNAS, Imovel

SITE = "https://www.cardinali.com.br"


def imovel(codigo, total, dia, bairro="Centro", **outros):
    return Imovel(codigo=codigo, fonte="cardinali", url=f"{SITE}/alugar/Sao-Carlos/Apartamento/Padrao/Centro/{codigo}",
                  tipo="Apartamento", subtipo="Padrão", bairro=bairro, total_mensal=total,
                  coletado_em=dia, **outros)


def salvar_dia(pasta, imoveis, tmp_path):
    csv_temporario = tmp_path / "coleta.csv"
    salvar_csv(imoveis, csv_temporario)
    return salvar_snapshot(csv_temporario, pasta)


# --- snapshot -----------------------------------------------------------------------------

def test_snapshot_tem_esquema_fixo(tmp_path):
    # condomínio vazio em todos os imóveis do dia: mesmo assim a coluna continua numérica
    destino = salvar_dia(tmp_path / "snapshots", [imovel(1, 1000.0, "2026-10-15"),
                                                  imovel(2, None, "2026-10-15")], tmp_path)
    assert destino == tmp_path / "snapshots" / "2026" / "2026-10-15.parquet"

    tipos = {nome: tipo for nome, tipo, *_ in duckdb.sql(f"DESCRIBE SELECT * FROM '{destino}'").fetchall()}
    assert list(tipos) == COLUNAS
    assert (tipos["codigo"], tipos["condominio"], tipos["coletado_em"]) == ("BIGINT", "DOUBLE", "DATE")


def test_snapshot_recusa_mais_de_uma_data(tmp_path):
    with pytest.raises(ValueError, match="única data"):
        salvar_dia(tmp_path, [imovel(1, 1000.0, "2026-10-14"), imovel(2, 900.0, "2026-10-15")], tmp_path)


def test_snapshot_recusa_imovel_repetido(tmp_path):
    with pytest.raises(ValueError, match="repetidos"):
        salvar_dia(tmp_path, [imovel(1, 1000.0, "2026-10-15"), imovel(1, 900.0, "2026-10-15")], tmp_path)


# --- backfill -----------------------------------------------------------------------------

CABECALHO_ANTIGO = ("Bairro,Tipo,Link,Aluguel Cheio,Aluguel com Bonificação,Condomínio,IPTU,"
                    "Total / Mês,Dormitórios,Banheiros,Garagens,Suítes")
PARAISO = f"{SITE}/alugar/Sao-Carlos/Apartamento/Padrao/Jardim-Paraiso/100"
VILA_MONTEIRO = f"{SITE}/alugar/Sao-Carlos/Casa/Padrao/Vila-Monteiro-Gleba-I/200"
CENTRO_VENDA = f"{SITE}/comprar/Sao-Carlos/Apartamento/Padrao/Centro/300"


def linha_antiga(texto):
    return next(csv.DictReader([CABECALHO_ANTIGO, texto]))


def test_converte_linha_do_formato_antigo():
    linha = linha_antiga(f'Jardim Paraiso,Apartamento,{PARAISO},"1.275,00","1.020,00",,"40,00",1060.0,1.0,1,,')
    convertido = imovel_do_formato_antigo(linha, date(2026, 1, 10), NomesDoSite())
    assert (convertido.codigo, convertido.tipo, convertido.subtipo) == (100, "Apartamento", "Padrao")
    assert (convertido.aluguel, convertido.aluguel_bonificado, convertido.iptu) == (1275.0, 1020.0, 40.0)
    assert (convertido.condominio, convertido.total_mensal, convertido.dormitorios) == (None, 1060.0, 1)
    assert convertido.coletado_em == "2026-01-10"


def test_formato_antigo_consulte_nos_fica_sem_total():
    linha = linha_antiga(f'Vila Monteiro Gleba I,Casa,{VILA_MONTEIRO},Consulte-nos,,,"160,00",160.0,2.0,2,1,')
    assert imovel_do_formato_antigo(linha, date(2026, 1, 10), NomesDoSite()).total_mensal is None


def test_formato_antigo_link_de_venda_vira_aluguel():
    linha = linha_antiga(f'Centro,Apartamento,{CENTRO_VENDA},"2.000,00",,"463,90","80,00",2543.9,2.0,1,1,1')
    assert imovel_do_formato_antigo(linha, date(2026, 1, 10), NomesDoSite()).url.startswith(f"{SITE}/alugar/")


def test_nomes_aprendidos_do_formato_atual():
    nomes = NomesDoSite()
    nomes.aprender(PARAISO, "Padrão", "Jardim Paraíso")
    assert (nomes.bairro("Jardim-Paraiso"), nomes.subtipo("Padrao")) == ("Jardim Paraíso", "Padrão")
    assert nomes.bairro("Bairro-Desconhecido") == "Bairro Desconhecido"


@pytest.fixture
def repo_com_historico(tmp_path):
    """Repositório git com versões do CSV nos formatos antigo e atual, em datas controladas."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*argumentos, quando=None):
        ambiente = {**os.environ, "GIT_AUTHOR_NAME": "teste", "GIT_AUTHOR_EMAIL": "teste@exemplo.com",
                    "GIT_COMMITTER_NAME": "teste", "GIT_COMMITTER_EMAIL": "teste@exemplo.com"}
        if quando:
            ambiente |= {"GIT_AUTHOR_DATE": quando, "GIT_COMMITTER_DATE": quando}
        subprocess.run(["git", "-c", "commit.gpgsign=false", *argumentos], cwd=repo, env=ambiente,
                       check=True, capture_output=True)

    def commitar(caminho, conteudo, quando):
        arquivo = repo / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(conteudo, encoding="utf-8")
        git("add", caminho)
        git("commit", "-q", "-m", f"versão de {quando}", quando=quando)

    git("init", "-q")
    commitar("dados.csv",  # formato mais antigo de todos, sem Tipo nem Banheiros
             "Bairro,Link,Aluguel Cheio,Aluguel com Bonificação,Condomínio,IPTU,Total / Mês,Dormitórios\n"
             f'Centro,{CENTRO_VENDA},"2.000,00",,"463,90","80,00",2543.9,2\n',
             "2025-11-11T02:19:57-03:00")
    commitar("dados/dados_imoveis.csv",
             f"{CABECALHO_ANTIGO}\n"
             f'Jardim Paraiso,Apartamento,{PARAISO},"1.275,00","1.020,00",,"40,00",1060.0,1.0,1,,\n'
             f'Vila Monteiro Gleba I,Casa,{VILA_MONTEIRO},Consulte-nos,,,"160,00",160.0,2.0,2,1,\n',
             "2025-11-12T23:50:00Z")  # 20h50 em Brasília, dia 12
    commitar("dados/dados_imoveis.csv",  # mesmo dia em Brasília (23h30): esta versão é a que vale
             f"{CABECALHO_ANTIGO}\n"
             f'Jardim Paraiso,Apartamento,{PARAISO},"1.275,00","1.000,00",,"40,00",1040.0,1.0,1,,\n'
             f'Centro,Apartamento,{CENTRO_VENDA},"2.000,00",,"463,90","80,00",2543.9,2.0,1,1,1\n',
             "2025-11-13T02:30:00Z")
    atual = repo / "atual.csv"
    salvar_csv([Imovel(codigo=100, fonte="cardinali", url=PARAISO, tipo="Apartamento", subtipo="Padrão",
                       bairro="Jardim Paraíso", total_mensal=1040.0, coletado_em="2025-11-14")], atual)
    commitar("dados/imoveis.csv", atual.read_text(encoding="utf-8"), "2025-11-14T21:00:00Z")
    return repo


def test_backfill_cria_um_snapshot_por_dia(repo_com_historico, tmp_path):
    pasta = tmp_path / "snapshots"
    criados = reconstruir(repo_com_historico, pasta)
    assert [arquivo.stem for arquivo in criados] == ["2025-11-11", "2025-11-12", "2025-11-14"]

    dia_12 = duckdb.sql(f"SELECT codigo, bairro, subtipo, total_mensal, url FROM '{criados[1]}' ORDER BY codigo").fetchall()
    # Só a última versão do dia 12; nomes com acento aprendidos do formato atual; /comprar/ vira /alugar/
    assert dia_12 == [
        (100, "Jardim Paraíso", "Padrão", 1040.0, PARAISO),
        (300, "Centro", "Padrão", 2543.9, CENTRO_VENDA.replace("/comprar/", "/alugar/")),
    ]


# --- consultas ----------------------------------------------------------------------------

@pytest.fixture
def historico_pequeno(tmp_path):
    """Três dias: o imóvel 1 baixa de preço, o 2 sai do site, o 3 aparece e depois sobe de preço."""
    pasta = tmp_path / "snapshots"
    salvar_dia(pasta, [imovel(1, 1000.0, "2026-01-01"), imovel(2, 2000.0, "2026-01-01", bairro="Jardim Paraíso")], tmp_path)
    salvar_dia(pasta, [imovel(1, 900.0, "2026-01-02"), imovel(3, 1500.0, "2026-01-02")], tmp_path)
    salvar_dia(pasta, [imovel(1, 900.0, "2026-01-05"), imovel(3, 1600.0, "2026-01-05")], tmp_path)
    return consultas.conectar(pasta)


def test_resumo_por_imovel(historico_pequeno):
    resumo = consultas.resumo_por_imovel(historico_pequeno).set_index("codigo")
    assert resumo.loc[1, ["dias_com_anuncio", "primeiro_total", "ultimo_total", "ainda_anunciado"]].tolist() == [3, 1000.0, 900.0, True]
    assert resumo.loc[2, "ultima_vez"].date() == date(2026, 1, 1)
    assert not resumo.loc[2, "ainda_anunciado"]
    assert resumo.loc[3, "primeira_vez"].date() == date(2026, 1, 2)


def test_mudancas_de_preco(historico_pequeno):
    mudancas = consultas.mudancas_de_preco(historico_pequeno)
    assert mudancas[["codigo", "total_anterior", "total_novo", "variacao_pct"]].values.tolist() == [
        [1, 1000.0, 900.0, -10.0],
        [3, 1500.0, 1600.0, 6.7],
    ]


def test_novidades_de_um_dia(historico_pequeno):
    dia_2 = consultas.novidades(historico_pequeno, date(2026, 1, 2))
    assert dia_2["novos"]["codigo"].tolist() == [3]
    assert dia_2["sairam"]["codigo"].tolist() == [2]
    assert dia_2["mudaram_de_preco"]["codigo"].tolist() == [1]

    ultimo_dia = consultas.novidades(historico_pequeno)  # sem data: o dia mais recente
    assert (ultimo_dia["novos"].empty, ultimo_dia["sairam"].empty) == (True, True)
    assert ultimo_dia["mudaram_de_preco"]["codigo"].tolist() == [3]


def test_serie_por_bairro(historico_pequeno):
    serie = consultas.serie_por_bairro(historico_pequeno)
    primeiro_dia = serie[serie["coletado_em"] == "2026-01-01"].set_index("bairro")
    assert primeiro_dia.loc["Centro", "mediana_total"] == 1000.0
    assert primeiro_dia.loc["Jardim Paraíso", "imoveis"] == 1
