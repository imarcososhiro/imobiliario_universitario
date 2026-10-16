"""Métricas simples para comparar imóveis: o que um estudante olha ao escolher onde morar."""
import pandas as pd

from app.bairros import UFSCAR, USP, buscar_coords, distancia_km

# Áreas fora disso são erro de cadastro no site (ex.: 1 m², 50.000 m²)
AREA_MINIMA_M2 = 12
AREA_MAXIMA_M2 = 1000

CAMPI = {"USP": USP, "UFSCar": UFSCAR}
MINIMO_IMOVEIS_BAIRRO = 3  # com menos imóveis que isso, o preço típico de um bairro é pouco confiável


def adicionar_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta o preço por pessoa, a área e a distância do bairro a cada campus."""
    df = df.copy()
    # Preço por pessoa: o total dividido pelos quartos, como numa república em que cada um tem o seu
    df["custo_por_dormitorio"] = df["total_mensal"] / df["dormitorios"].where(df["dormitorios"] >= 1)

    # Casas costumam vir só com área construída; apartamentos, com área útil
    area = df["area_util_m2"].fillna(df["area_construida_m2"])
    df["area_m2"] = area.where(area.between(AREA_MINIMA_M2, AREA_MAXIMA_M2))

    # A localização de cada imóvel é a do bairro: o site não informa o endereço
    coordenadas = df["bairro"].map(buscar_coords)
    for campus, ponto in CAMPI.items():
        df[f"distancia_{campus.lower()}_km"] = coordenadas.map(
            lambda coords: distancia_km(coords, ponto) if coords else None).astype(float)
    return df


def escolher_campus(df: pd.DataFrame, campus: str) -> pd.DataFrame:
    """Copia em `distancia_km` a distância até o campus escolhido ("USP" ou "UFSCar")."""
    return df.assign(distancia_km=df[f"distancia_{campus.lower()}_km"])


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
