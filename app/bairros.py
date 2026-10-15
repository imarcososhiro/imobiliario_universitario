# Contornos dos bairros (dados/geo/bairros.geojson, gerado por `python -m geo.gerar`)
# e nomes padrão (dados/geo/aliases_bairros.csv)
import json
import math
from geo.lugares import RODOVIARIA, UFSCAR, USP
from geo.nomes import PASTA_GEO, carregar_aliases, nome_padrao, normalizar

CAMINHO_GEOJSON = PASTA_GEO / 'bairros.geojson'

# Região universitária: bairros que chegam a até 2,2 km da USP ou da UFSCar. Medir pela
# borda (e não pelo meio do bairro) evita que um bairro grande fique de fora por pouco;
# o raio reproduz a lista de bairros que o projeto usava antes do mapa com contornos
RAIO_REGIAO_KM = 2.2

aliases = carregar_aliases()
with open(CAMINHO_GEOJSON, encoding='utf-8') as arquivo:
    contornos = {normalizar(feature['properties']['bairro']): feature for feature in json.load(arquivo)['features']}
# Nomes padrão da tabela de aliases, inclusive de bairros que ainda não têm contorno
nomes_da_tabela = {normalizar(nome): nome for nome in aliases.values()}

# O site escreve o mesmo bairro de jeitos diferentes ("Jardim Hikari", "Jardim Hikare");
# retorna o nome usado no mapa, pra cada bairro virar uma área só
def Nome_padrao(nome_no_site):
    nome = nome_padrao(nome_no_site, aliases)
    contorno = contornos.get(normalizar(nome))
    if contorno:
        return contorno['properties']['bairro']
    return nomes_da_tabela.get(normalizar(nome), nome)

# Feature GeoJSON do bairro (contorno + propriedades), ou None se ele não estiver no mapa
def Buscar_contorno(bairro):
    return contornos.get(normalizar(bairro))

# Um ponto dentro do bairro (latitude, longitude), ou None
def Buscar_coords(bairro):
    contorno = Buscar_contorno(bairro)
    return (contorno['properties']['lat'], contorno['properties']['lon']) if contorno else None

# Distância em linha reta entre dois pontos (latitude, longitude), em km (fórmula de haversine)
def Distancia_km(ponto_a, ponto_b):
    lat_a, lon_a, lat_b, lon_b = map(math.radians, (*ponto_a, *ponto_b))
    h = math.sin((lat_b - lat_a) / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))

# A distância da borda até o campus é calculada pelo gerador do mapa (python -m geo.gerar)
def Na_regiao_universitaria(bairro):
    contorno = Buscar_contorno(bairro)
    return contorno is not None and contorno['properties']['distancia_campus_km'] <= RAIO_REGIAO_KM
