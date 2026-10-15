"""Bairros de São Carlos no OpenStreetMap, baixados pela Overpass API.

No OSM, a maioria dos bairros (loteamentos) de São Carlos é um polígono: um caminho
fechado ("way") ou uma relação "multipolygon" formada por vários caminhos. Alguns,
como o Centro, existem só como um ponto ("node"). Para esses, os endereços do OSM
marcados com o bairro (tag addr:suburb) ajudam a desenhar um contorno.
"""
import logging
import re
import time

import httpx
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, polygonize, unary_union
from shapely.validation import make_valid

log = logging.getLogger(__name__)

# A Overpass recusa (HTTP 406) User-Agents que imitam navegador: aqui o projeto se identifica
USER_AGENT = "imobiliario-universitario/1.0 (+https://github.com/imarcososhiro/imobiliario_universitario)"
RODADAS = 3
ESPERA_BASE_S = 30
# O servidor principal costuma ficar lotado; os outros são espelhos públicos
SERVIDORES = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
CONSULTA = """
[out:json][timeout:180];
area["name"="São Carlos"]["boundary"="administrative"]["admin_level"="8"]->.cidade;
(
  way(area.cidade)["place"~"^(suburb|neighbourhood|quarter)$"];
  relation(area.cidade)["place"~"^(suburb|neighbourhood|quarter)$"];
  node(area.cidade)["place"~"^(suburb|neighbourhood|quarter)$"];
);
out geom;
nwr(area.cidade)["addr:suburb"][!"place"];
out center tags;
"""
# Marcados como bairro no OSM, mas não são: quadras de condomínio e a própria cidade
IGNORAR = re.compile(r"^(Quadra \w+|São Carlos)$")


def baixar() -> dict:
    """Resposta da Overpass em JSON. Tenta cada servidor; se todos falharem, espera e repete."""
    for rodada in range(1, RODADAS + 1):
        for servidor in SERVIDORES:
            try:
                resposta = httpx.post(servidor, data={"data": CONSULTA},
                                      headers={"User-Agent": USER_AGENT}, timeout=240)
                resposta.raise_for_status()
                return resposta.json()
            except (httpx.HTTPError, ValueError) as erro:
                log.warning("Overpass em %s falhou: %s", servidor, erro)
        if rodada < RODADAS:
            espera = ESPERA_BASE_S * 2 ** (rodada - 1)
            log.info("Todos os servidores falharam; nova rodada em %d s", espera)
            time.sleep(espera)
    raise RuntimeError("nenhum servidor da Overpass respondeu; tente de novo mais tarde")


def _coordenadas(geometria: list[dict]) -> list[tuple[float, float]]:
    return [(ponto["lon"], ponto["lat"]) for ponto in geometria]


def apenas_area(geometria: BaseGeometry) -> BaseGeometry | None:
    """Corrige polígonos inválidos (ex.: borda que se cruza) e descarta pedaços sem área."""
    geometria = make_valid(geometria)
    if geometria.geom_type in ("Polygon", "MultiPolygon"):
        return geometria
    partes = [parte for parte in getattr(geometria, "geoms", []) if parte.geom_type in ("Polygon", "MultiPolygon")]
    return unary_union(partes) if partes else None


def poligono_do_caminho(caminho: dict) -> BaseGeometry | None:
    coordenadas = _coordenadas(caminho.get("geometry", []))
    if len(coordenadas) < 4 or coordenadas[0] != coordenadas[-1]:
        return None  # caminho aberto: uma rua ou divisa, não uma área
    return apenas_area(Polygon(coordenadas))


def poligono_da_relacao(relacao: dict) -> BaseGeometry | None:
    """Monta o polígono de uma relação juntando os caminhos de borda (outer) e de buraco (inner)."""
    def aneis(papel: str) -> list[Polygon]:
        linhas = [LineString(_coordenadas(membro["geometry"])) for membro in relacao.get("members", [])
                  if membro["type"] == "way" and membro.get("geometry")
                  and (membro.get("role") or "outer") == papel]
        return list(polygonize(linemerge(linhas))) if linhas else []

    bordas = aneis("outer")
    if not bordas:
        return None
    geometria = unary_union(bordas)
    buracos = aneis("inner")
    if buracos:
        geometria = geometria.difference(unary_union(buracos))
    return apenas_area(geometria)


def ler_elementos(dados: dict) -> tuple[dict[str, BaseGeometry], dict[str, Point], dict[str, list[Point]]]:
    """Separa a resposta da Overpass em polígonos, pontos e endereços, pelo nome do bairro."""
    poligonos: dict[str, BaseGeometry] = {}
    pontos: dict[str, Point] = {}
    enderecos: dict[str, list[Point]] = {}
    for elemento in dados["elements"]:
        tags = elemento.get("tags", {})
        if "place" not in tags and tags.get("addr:suburb"):
            posicao = elemento.get("center") or elemento
            if "lat" in posicao:
                enderecos.setdefault(tags["addr:suburb"].strip(), []).append(Point(posicao["lon"], posicao["lat"]))
            continue
        nome = tags.get("name", "").strip()
        if not nome or IGNORAR.match(nome):
            continue
        if elemento["type"] == "node":
            pontos[nome] = Point(elemento["lon"], elemento["lat"])
            continue
        if elemento["type"] == "way":
            geometria = poligono_do_caminho(elemento)
        else:
            geometria = poligono_da_relacao(elemento)
        if geometria is None or geometria.is_empty or geometria.area == 0:
            continue
        # O mesmo bairro às vezes está dividido em mais de um elemento
        poligonos[nome] = unary_union([poligonos[nome], geometria]) if nome in poligonos else geometria
    return poligonos, pontos, enderecos
