# Contornos dos bairros (dados/geo/bairros.geojson, gerado por `python -m geo.gerar`)
# e nomes padrão (dados/geo/aliases_bairros.csv)
import json
import math
from geo.nomes import PASTA_GEO, carregar_aliases, nome_padrao, normalizar

CAMINHO_GEOJSON = PASTA_GEO / 'bairros.geojson'

USP = (-22.006213906979283, -47.89752552863632)
UFSCAR = (-21.982364333434838, -47.87966644394043)
RODOVIARIA = (-22.00521597624045, -47.88955145780041)
RAIO_REGIAO_KM = 2.5 # Região universitária: bairros a até 2,5 km da USP ou da UFSCar

aliases = carregar_aliases()
with open(CAMINHO_GEOJSON, encoding='utf-8') as arquivo:
    contornos = {normalizar(feature['properties']['bairro']): feature for feature in json.load(arquivo)['features']}

# O site escreve o mesmo bairro de jeitos diferentes ("Jardim Hikari", "Jardim Hikare");
# retorna o nome usado no mapa, pra cada bairro virar uma área só
def Nome_padrao(nome_no_site):
    nome = nome_padrao(nome_no_site, aliases)
    contorno = contornos.get(normalizar(nome))
    return contorno['properties']['bairro'] if contorno else nome

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

def Na_regiao_universitaria(bairro):
    coords = Buscar_coords(bairro)
    return coords is not None and min(Distancia_km(coords, USP), Distancia_km(coords, UFSCAR)) <= RAIO_REGIAO_KM
