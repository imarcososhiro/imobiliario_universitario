"""Bairros de São Carlos no OpenStreetMap, baixados pela Overpass API.

No OSM, a maioria dos bairros (loteamentos) de São Carlos é um polígono: um caminho
fechado ("way") ou uma relação "multipolygon" formada por vários caminhos. Alguns,
como o Centro, existem só como um ponto ("node"). Para esses, os endereços do OSM
marcados com o bairro (tag addr:suburb) ajudam a desenhar um contorno. Alguns
condomínios estão marcados como área residencial (landuse=residential) em vez de bairro.
As ruas servem para ajustar os contornos calculados aos quarteirões.
"""
import logging
import re
import time
from typing import NamedTuple

import httpx
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, polygonize, unary_union
from shapely.validation import make_valid

log = logging.getLogger(__name__)

# A Overpass recusa (HTTP 406) User-Agents que imitam navegador: aqui o projeto se identifica
USER_AGENT = "imobiliario-universitario/1.0 (+https://github.com/imarcososhiro/imobiliario_universitario)"
RODADAS = 4
ESPERA_BASE_S = 30
# O servidor principal costuma ficar lotado; os outros são espelhos públicos
SERVIDORES = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
CIDADE = 'area["name"="São Carlos"]["boundary"="administrative"]["admin_level"="8"]->.cidade;'
CONSULTA_BAIRROS = f"""
[out:json][timeout:180];
{CIDADE}
(
  way(area.cidade)["place"~"^(suburb|neighbourhood|quarter)$"];
  relation(area.cidade)["place"~"^(suburb|neighbourhood|quarter)$"];
  node(area.cidade)["place"~"^(suburb|neighbourhood|quarter|village|hamlet)$"];
  way(area.cidade)["landuse"="residential"]["name"][!"place"];
  relation(area.cidade)["landuse"="residential"]["name"][!"place"];
);
out geom;
nwr(area.cidade)["addr:suburb"][!"place"];
out center tags;
"""
# Ruas por onde passam carros: elas dividem a cidade em quarteirões
CONSULTA_RUAS = f"""
[out:json][timeout:180];
{CIDADE}
way(area.cidade)["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"];
out geom;
"""
# Marcados como bairro no OSM, mas não são: quadras de condomínio e a própria cidade
IGNORAR = re.compile(r"^(Quadra \w+|São Carlos)$")


def baixar(consulta: str = CONSULTA_BAIRROS) -> dict:
    """Resposta da Overpass em JSON. Tenta cada servidor; se todos falharem, espera e repete."""
    for rodada in range(1, RODADAS + 1):
        for servidor in SERVIDORES:
            try:
                resposta = httpx.post(servidor, data={"data": consulta},
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


def ler_ruas(dados: dict) -> list[LineString]:
    return [LineString(_coordenadas(elemento["geometry"])) for elemento in dados["elements"]
            if elemento["type"] == "way" and len(elemento.get("geometry", [])) >= 2]


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


class ElementosOSM(NamedTuple):
    poligonos: dict[str, BaseGeometry]     # bairros desenhados (place=suburb, neighbourhood...)
    pontos: dict[str, Point]               # bairros que são só um ponto
    enderecos: dict[str, list[Point]]      # endereços marcados com o bairro (addr:suburb)
    residenciais: dict[str, BaseGeometry]  # áreas residenciais com nome (landuse=residential)


def ler_elementos(dados: dict) -> ElementosOSM:
    """Separa a resposta da Overpass em polígonos, pontos, endereços e áreas residenciais, pelo nome."""
    elementos = ElementosOSM({}, {}, {}, {})
    for elemento in dados["elements"]:
        tags = elemento.get("tags", {})
        nome = tags.get("name", "").strip()
        tem_forma = "geometry" in elemento or "members" in elemento
        if "place" in tags:
            if not nome or IGNORAR.match(nome):
                continue
            if elemento["type"] == "node":
                elementos.pontos[nome] = Point(elemento["lon"], elemento["lat"])
                continue
            destino = elementos.poligonos
        elif tags.get("landuse") == "residential" and nome and tem_forma:
            destino = elementos.residenciais
        elif tags.get("addr:suburb"):
            posicao = elemento.get("center") or elemento
            if "lat" in posicao:
                elementos.enderecos.setdefault(tags["addr:suburb"].strip(), []).append(
                    Point(posicao["lon"], posicao["lat"]))
            continue
        else:
            continue

        if elemento["type"] == "way":
            geometria = poligono_do_caminho(elemento)
        else:
            geometria = poligono_da_relacao(elemento)
        if geometria is None or geometria.is_empty or geometria.area == 0:
            continue
        # O mesmo bairro às vezes está dividido em mais de um elemento
        destino[nome] = unary_union([destino[nome], geometria]) if nome in destino else geometria
    return elementos
