"""Contornos dos bairros (dados/geo/bairros.geojson, gerado por `python -m geo.gerar`)
e nomes padrão (dados/geo/aliases_bairros.csv)."""
import json
import math

from geo import nomes
from geo.lugares import RODOVIARIA, UFSCAR, USP  # noqa: F401 (usados pelas métricas)

CAMINHO_GEOJSON = nomes.PASTA_GEO / "bairros.geojson"

aliases = nomes.carregar_aliases()
with open(CAMINHO_GEOJSON, encoding="utf-8") as arquivo:
    contornos = {nomes.normalizar(feature["properties"]["bairro"]): feature for feature in json.load(arquivo)["features"]}
# Nomes padrão da tabela de aliases, inclusive de bairros que ainda não têm contorno
nomes_da_tabela = {nomes.normalizar(nome): nome for nome in aliases.values()}


def padronizar_bairro(nome_no_site: str) -> str:
    """Nome do bairro como está no mapa.

    O site escreve o mesmo bairro de jeitos diferentes ("Jardim Hikari", "Jardim Hikare"):
    padronizar faz cada bairro virar uma área só.
    """
    nome = nomes.nome_padrao(nome_no_site, aliases)
    contorno = contornos.get(nomes.normalizar(nome))
    if contorno:
        return contorno["properties"]["bairro"]
    return nomes_da_tabela.get(nomes.normalizar(nome), nome)


def buscar_contorno(bairro: str) -> dict | None:
    """Feature GeoJSON do bairro (contorno + propriedades), ou None se ele não estiver no mapa."""
    return contornos.get(nomes.normalizar(bairro))


def buscar_coords(bairro: str) -> tuple[float, float] | None:
    """Um ponto dentro do bairro (latitude, longitude), ou None."""
    contorno = buscar_contorno(bairro)
    return (contorno["properties"]["lat"], contorno["properties"]["lon"]) if contorno else None


def distancia_km(ponto_a: tuple[float, float], ponto_b: tuple[float, float]) -> float:
    """Distância em linha reta entre dois pontos (latitude, longitude), pela fórmula de haversine."""
    lat_a, lon_a, lat_b, lon_b = map(math.radians, (*ponto_a, *ponto_b))
    h = math.sin((lat_b - lat_a) / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))
