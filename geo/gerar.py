"""Gera dados/geo/bairros.geojson, com o contorno de cada bairro para o mapa do dashboard.

Uso: python -m geo.gerar [--osm resposta_da_overpass.json]

1. Baixa do OpenStreetMap os polígonos e pontos dos bairros de São Carlos.
2. Junta as grafias diferentes do mesmo bairro (dados/geo/aliases_bairros.csv).
3. Os desenhos de dados/geo/desenhos_manuais.geojson substituem o que veio do OSM, e os
   pontos de dados/geo/pontos_manuais.csv (coletados à mão) valem mais que os do OSM.
4. Bairros com imóveis que no OSM não têm polígono ganham um contorno calculado:
   - "enderecos": em volta dos endereços do OSM marcados com o bairro (ex.: Centro);
   - "aproximado": sem endereços suficientes, a área em volta do ponto do bairro
     que nenhum outro bairro ocupa.
"""
import argparse
import csv
import json
import logging
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

import shapely
from shapely.geometry import MultiPoint, Point, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geo import osm
from geo.nomes import PASTA_GEO, carregar_aliases, nome_padrao, normalizar

log = logging.getLogger(__name__)

CAMINHO_GEOJSON = PASTA_GEO / "bairros.geojson"
CAMINHO_DESENHOS = PASTA_GEO / "desenhos_manuais.geojson"
CAMINHO_PONTOS = PASTA_GEO / "pontos_manuais.csv"
CAMINHO_IMOVEIS = PASTA_GEO.parent / "imoveis.csv"
RAIO_APROXIMACAO_M = 700    # um bairro aproximado não passa deste raio em volta do ponto
MIN_ENDERECOS = 15          # menos endereços que isso não desenham um contorno confiável
MAX_DESVIO_ENDERECOS_M = 400  # o miolo dos endereços tem que estar perto do ponto do bairro
TOLERANCIA_GRAUS = 0.00002  # simplificação do contorno (~2 m), para o arquivo ficar leve


class Projecao:
    """Converte graus em metros perto de São Carlos (projeção equirretangular local).

    Um raio em metros só faz sentido num plano; na escala de uma cidade a distorção é desprezível.
    """

    def __init__(self, latitude_referencia: float):
        self.metros_por_grau_lon = 111_320 * math.cos(math.radians(latitude_referencia))
        self.metros_por_grau_lat = 110_540

    def para_metros(self, geometria: BaseGeometry) -> BaseGeometry:
        return shapely.transform(geometria, lambda xy: xy * [self.metros_por_grau_lon, self.metros_por_grau_lat])

    def para_graus(self, geometria: BaseGeometry) -> BaseGeometry:
        return shapely.transform(geometria, lambda xy: xy / [self.metros_por_grau_lon, self.metros_por_grau_lat])


def _parte_principal(area: BaseGeometry, referencia: Point) -> BaseGeometry | None:
    """O pedaço que contém o ponto de referência; se nenhum contiver, o maior."""
    partes = [parte for parte in getattr(area, "geoms", [area]) if parte.geom_type == "Polygon" and not parte.is_empty]
    if not partes:
        return None
    return next((parte for parte in partes if parte.contains(referencia)), max(partes, key=lambda p: p.area))


def contorno_por_enderecos(enderecos: list[Point], ponto_do_bairro: Point | None,
                           ocupado: BaseGeometry) -> BaseGeometry | None:
    """Contorno em volta dos endereços do OSM marcados com o bairro.

    Descarta endereços muito longe do miolo (provavelmente marcados errado) e recusa a
    nuvem inteira se o miolo estiver longe do ponto oficial do bairro.
    """
    if len(enderecos) < MIN_ENDERECOS:
        return None
    projecao = Projecao(enderecos[0].y)
    pontos = [projecao.para_metros(ponto) for ponto in enderecos]
    miolo = Point(statistics.median(p.x for p in pontos), statistics.median(p.y for p in pontos))
    if ponto_do_bairro and miolo.distance(projecao.para_metros(ponto_do_bairro)) > MAX_DESVIO_ENDERECOS_M:
        return None
    distancias = [ponto.distance(miolo) for ponto in pontos]
    limite = min(2000, 2.5 * statistics.median(distancias))
    pontos = [ponto for ponto, distancia in zip(pontos, distancias) if distancia <= limite]
    if len(pontos) < MIN_ENDERECOS:
        return None
    # Contorno côncavo acompanha a nuvem de pontos melhor que o convexo; a margem pega os lotes da borda
    contorno = shapely.concave_hull(MultiPoint(pontos), ratio=0.3).buffer(60)
    principal = _parte_principal(contorno.difference(projecao.para_metros(ocupado)), miolo)
    return projecao.para_graus(principal) if principal else None


def aproximar(pontos: dict[str, Point], vizinhos: list[Point], ocupado: BaseGeometry,
              raio_m: float = RAIO_APROXIMACAO_M) -> dict[str, BaseGeometry]:
    """Contorno aproximado para cada bairro que só tem um ponto.

    Cada ponto fica com a área mais perto dele do que de qualquer outro bairro (célula de
    Voronoi), limitada a um raio e sem invadir a área já ocupada por outros bairros.
    """
    if not pontos:
        return {}
    projecao = Projecao(next(iter(pontos.values())).y)
    sementes = [projecao.para_metros(ponto) for ponto in [*pontos.values(), *vizinhos]]
    if len(sementes) == 1:
        celulas = [sementes[0].buffer(raio_m)]  # sem vizinhos, a "célula" é o plano todo
    else:
        celulas = shapely.voronoi_polygons(MultiPoint(sementes), ordered=True).geoms
    ocupado = projecao.para_metros(ocupado)

    resultado = {}
    for nome, semente, celula in zip(pontos, sementes, celulas):
        principal = _parte_principal(celula.intersection(semente.buffer(raio_m)).difference(ocupado), semente)
        if principal:
            resultado[nome] = projecao.para_graus(principal)
    return resultado


def gerar(dados_osm: dict, aliases: dict[str, str], desenhos: dict[str, BaseGeometry],
          pontos_manuais: dict[str, Point], nomes_no_site: Counter) -> tuple[list[dict], list[str]]:
    """Monta as features do GeoJSON. Devolve também os bairros com imóveis que ficaram sem contorno."""
    poligonos, pontos, enderecos = osm.ler_elementos(dados_osm)

    def chave(nome: str) -> str:
        return normalizar(nome_padrao(nome, aliases))

    # Todas as grafias vistas de cada bairro (site e OSM), com o nº de imóveis no site
    grafias: dict[str, Counter] = {}
    for nome in [*nomes_no_site, *poligonos, *pontos, *desenhos]:
        grafias.setdefault(chave(nome), Counter())[nome_padrao(nome, aliases)] += nomes_no_site[nome]

    def nome_exibido(k: str) -> str:
        # A grafia com mais acentos costuma ser a correta ("Jardim São Carlos", não "Jardim Sao Carlos");
        # no empate, a mais usada no site
        return max(grafias[k], key=lambda nome: (sum(not letra.isascii() for letra in nome), grafias[k][nome]))

    geometrias: dict[str, BaseGeometry] = {}
    origem: dict[str, str] = {}
    for nome, geometria in poligonos.items():
        k = chave(nome)
        geometrias[k] = unary_union([geometrias[k], geometria]) if k in geometrias else geometria
        origem[k] = "osm"
    for nome, geometria in desenhos.items():
        k = chave(nome)
        geometrias[k], origem[k] = geometria, "manual"

    pontos_por_chave = {chave(nome): ponto for nome, ponto in [*pontos.items(), *pontos_manuais.items()]}
    enderecos_por_chave: dict[str, list[Point]] = {}
    for nome, lista in enderecos.items():
        enderecos_por_chave.setdefault(chave(nome), []).extend(lista)
    faltando = sorted({chave(nome) for nome in nomes_no_site} - geometrias.keys())

    for k in faltando:
        geometria = contorno_por_enderecos(enderecos_por_chave.get(k, []), pontos_por_chave.get(k),
                                           unary_union(list(geometrias.values())))
        if geometria:
            geometrias[k], origem[k] = geometria, "enderecos"

    so_ponto = {k: pontos_por_chave[k] for k in faltando if k not in geometrias and k in pontos_por_chave}
    vizinhos = [geometria.representative_point() for geometria in geometrias.values()]
    for k, geometria in aproximar(so_ponto, vizinhos, unary_union(list(geometrias.values()))).items():
        geometrias[k], origem[k] = geometria, "aproximado"

    features = []
    for k in sorted(geometrias):
        geometria = shapely.set_precision(geometrias[k].simplify(TOLERANCIA_GRAUS), 1e-6)
        ponto = geometria.representative_point()  # sempre dentro do contorno, bom para rótulos
        features.append({
            "type": "Feature",
            "properties": {"bairro": nome_exibido(k), "origem": origem[k],
                           "lat": round(ponto.y, 5), "lon": round(ponto.x, 5)},
            "geometry": mapping(geometria),
        })
    sem_contorno = Counter({nome_exibido(k): grafias[k].total() for k in faltando if k not in geometrias})
    return features, [f"{nome} ({imoveis})" for nome, imoveis in sem_contorno.most_common()]


def carregar_desenhos(caminho: Path = CAMINHO_DESENHOS) -> dict[str, BaseGeometry]:
    if not caminho.exists():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return {feature["properties"]["bairro"]: osm.apenas_area(shape(feature["geometry"]))
            for feature in dados["features"]}


def carregar_pontos_manuais(caminho: Path = CAMINHO_PONTOS) -> dict[str, Point]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return {linha["bairro"]: Point(float(linha["lon"]), float(linha["lat"])) for linha in csv.DictReader(arquivo)}


def salvar_geojson(features: list[dict], caminho: Path = CAMINHO_GEOJSON) -> None:
    """Uma feature por linha: o diff no git mostra exatamente quais bairros mudaram."""
    linhas = ",\n".join(json.dumps(feature, ensure_ascii=False, separators=(",", ":")) for feature in features)
    caminho.write_text('{"type":"FeatureCollection","features":[\n' + linhas + "\n]}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Gera o GeoJSON dos bairros de São Carlos.")
    parser.add_argument("--osm", type=Path, help="resposta da Overpass já salva (senão, baixa)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)-7s %(message)s")

    dados_osm = json.loads(args.osm.read_text(encoding="utf-8")) if args.osm else osm.baixar()
    with open(CAMINHO_IMOVEIS, encoding="utf-8", newline="") as arquivo:
        nomes_no_site = Counter(linha["bairro"] for linha in csv.DictReader(arquivo))

    features, sem_contorno = gerar(dados_osm, carregar_aliases(), carregar_desenhos(),
                                   carregar_pontos_manuais(), nomes_no_site)
    salvar_geojson(features)
    origens = Counter(feature["properties"]["origem"] for feature in features)
    log.info("%d bairros gravados em %s (%s)", len(features), CAMINHO_GEOJSON,
             ", ".join(f"{quantidade} {origem}" for origem, quantidade in origens.items()))
    if sem_contorno:
        log.warning("Bairros com imóveis e sem contorno (adicione um alias ou um desenho manual): %s",
                    ", ".join(sem_contorno))


if __name__ == "__main__":
    main()
