"""Nomes de bairros: o site e o OpenStreetMap escrevem o mesmo bairro de jeitos diferentes.

A tabela dados/geo/aliases_bairros.csv diz, para cada grafia conhecida, qual é o nome
padrão do bairro. Este módulo não depende de nada além da biblioteca padrão, para
poder ser usado tanto pelo gerador do mapa quanto pelo dashboard.
"""
import csv
import re
import unicodedata
from pathlib import Path

PASTA_GEO = Path(__file__).resolve().parent.parent / "dados" / "geo"
CAMINHO_ALIASES = PASTA_GEO / "aliases_bairros.csv"


def normalizar(nome: str) -> str:
    """Chave de comparação: sem acento, maiúscula ou pontuação.

    "Vila Monteiro (Gleba I)" e "Vila Monteiro Gleba I" viram "vila monteiro gleba i".
    """
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


def carregar_aliases(caminho: Path = CAMINHO_ALIASES) -> dict[str, str]:
    """Lê a tabela grafia -> bairro. As chaves já vêm normalizadas."""
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return {normalizar(linha["grafia"]): linha["bairro"] for linha in csv.DictReader(arquivo)}


def nome_padrao(nome: str, aliases: dict[str, str]) -> str:
    """Nome padrão do bairro; se a grafia não estiver na tabela, o próprio nome."""
    return aliases.get(normalizar(nome), nome)
