"""Métricas simples para comparar imóveis: o que um estudante olha ao escolher onde morar."""
import pandas as pd

from app.bairros import RODOVIARIA, UFSCAR, USP, buscar_coords, distancia_km

# Áreas fora disso são erro de cadastro no site (ex.: 1 m², 50.000 m²)
AREA_MINIMA_M2 = 12
AREA_MAXIMA_M2 = 1000

# De onde a distância pode ser medida: os dois campi e a rodoviária. Muita gente da UFSCar mora
# no centro e vai de ônibus, e é da rodoviária que saem as linhas para o campus.
LUGARES = {"USP": USP, "UFSCar": UFSCAR, "Rodoviária": RODOVIARIA}
COLUNAS_DISTANCIA = {"USP": "distancia_usp_km", "UFSCar": "distancia_ufscar_km",
                     "Rodoviária": "distancia_rodoviaria_km"}
# Para frases como "1,2 km da USP"
DO_LUGAR = {"USP": "da USP", "UFSCar": "da UFSCar", "Rodoviária": "da rodoviária"}
MINIMO_IMOVEIS_BAIRRO = 3  # com menos imóveis que isso, o preço típico de um bairro é pouco confiável


def adicionar_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta o preço por quarto, a área e a distância do bairro a cada lugar (campi e rodoviária)."""
    df = df.copy()
    # Preço por quarto: o total dividido pelos quartos. Numa república em que cada um tem o seu
    # quarto, é quanto cada pessoa paga
    df["custo_por_dormitorio"] = df["total_mensal"] / df["dormitorios"].where(df["dormitorios"] >= 1)

    # Casas costumam vir só com área construída; apartamentos, com área útil
    area = df["area_util_m2"].fillna(df["area_construida_m2"])
    df["area_m2"] = area.where(area.between(AREA_MINIMA_M2, AREA_MAXIMA_M2))

    # A localização de cada imóvel é a do bairro: o site não informa o endereço
    coordenadas = df["bairro"].map(buscar_coords)
    for lugar, ponto in LUGARES.items():
        df[COLUNAS_DISTANCIA[lugar]] = coordenadas.map(
            lambda coords: distancia_km(coords, ponto) if coords else None).astype(float)
    return df


def medir_distancia(df: pd.DataFrame, lugar: str) -> pd.DataFrame:
    """Copia em `distancia_km` a distância até o lugar escolhido ("USP", "UFSCar" ou "Rodoviária")."""
    return df.assign(distancia_km=df[COLUNAS_DISTANCIA[lugar]])


def resumo_por_bairro(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por bairro, com o preço típico (a mediana, que um anúncio fora da curva não distorce)."""
    return (
        df.groupby("bairro")
        .agg(
            imoveis=("total_mensal", "size"),
            custo_por_dormitorio=("custo_por_dormitorio", "median"),
            total_mensal=("total_mensal", "median"),
            mais_barato=("custo_por_dormitorio", "min"),
            distancia_km=("distancia_km", "first"),
        )
        .reset_index()
    )
