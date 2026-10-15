"""Métricas de custo-benefício: o que um estudante compara ao escolher onde morar."""
import pandas as pd

from app.bairros import UFSCAR, USP, buscar_coords, distancia_km

# Áreas fora disso são erro de cadastro no site (ex.: 1 m², 50.000 m²)
AREA_MINIMA_M2 = 12
AREA_MAXIMA_M2 = 1000

CAMPI = {"USP": USP, "UFSCar": UFSCAR}
MINIMO_IMOVEIS_BAIRRO = 3  # com menos imóveis que isso, a mediana de um bairro é pouco confiável
QUALQUER_CAMPUS = "Tanto faz"

# Critérios do índice: coluna -> rótulo. Em todos, quanto menor o valor, melhor.
CRITERIOS = {
    "custo_por_dormitorio": "Custo por dormitório",
    "preco_m2": "Preço por m²",
    "distancia_km": "Distância ao campus",
}
PESOS_PADRAO = {criterio: 1.0 for criterio in CRITERIOS}


def adicionar_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta custo por dormitório, área, preço por m² e a distância do bairro a cada campus."""
    df = df.copy()
    df["custo_por_dormitorio"] = df["total_mensal"] / df["dormitorios"].where(df["dormitorios"] >= 1)

    # Casas costumam vir só com área construída; apartamentos, com área útil
    area = df["area_util_m2"].fillna(df["area_construida_m2"])
    df["area_m2"] = area.where(area.between(AREA_MINIMA_M2, AREA_MAXIMA_M2))
    df["preco_m2"] = df["total_mensal"] / df["area_m2"]

    # A localização de cada imóvel é a do bairro: o site não informa o endereço
    coordenadas = df["bairro"].map(buscar_coords)
    for campus, ponto in CAMPI.items():
        df[f"distancia_{campus.lower()}_km"] = coordenadas.map(
            lambda coords: distancia_km(coords, ponto) if coords else None).astype(float)
    return df


def escolher_campus(df: pd.DataFrame, campus: str) -> pd.DataFrame:
    """Copia em `distancia_km` a distância até o campus escolhido (ou até o mais perto)."""
    df = df.copy()
    if campus in CAMPI:
        df["distancia_km"] = df[f"distancia_{campus.lower()}_km"]
    else:
        df["distancia_km"] = df[[f"distancia_{nome.lower()}_km" for nome in CAMPI]].min(axis=1)
    return df


def notas_por_criterio(df: pd.DataFrame) -> pd.DataFrame:
    """Nota de 0 a 1 em cada critério: 1 para o melhor imóvel da lista, 0 para o pior.

    Usa a posição no ranking (e não o valor), para um imóvel caríssimo não achatar a
    nota de todos os outros. Empates recebem a mesma nota.
    """
    notas = {}
    for criterio in CRITERIOS:
        valores = df[criterio]
        quantidade = valores.count()
        if quantidade > 1:
            notas[criterio] = 1 - (valores.rank(method="average") - 1) / (quantidade - 1)
        else:  # um imóvel só (ou nenhum) com esse dado: não há com quem comparar
            notas[criterio] = pd.Series(1.0, index=df.index).where(valores.notna())
    return pd.DataFrame(notas, index=df.index)


def indice_custo_beneficio(df: pd.DataFrame, pesos: dict[str, float] = PESOS_PADRAO) -> pd.Series:
    """Índice de 0 a 100 (maior = melhor), comparando os imóveis da lista entre si.

    É a média das notas de cada critério, ponderada pelos pesos. Se um imóvel não tem
    algum dado (ex.: área), o índice usa só os critérios que ele tem.
    """
    if not any(pesos.values()):
        pesos = PESOS_PADRAO
    notas = notas_por_criterio(df)
    peso = pd.Series(pesos)[notas.columns]
    soma_ponderada = (notas * peso).sum(axis=1, min_count=1)
    peso_disponivel = notas.notna().mul(peso).sum(axis=1)
    return (100 * soma_ponderada / peso_disponivel.where(peso_disponivel > 0)).round()


def resumo_por_bairro(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por bairro, com medianas (menos sensíveis a um anúncio fora da curva que a média)."""
    return (
        df.groupby("bairro")
        .agg(
            imoveis=("total_mensal", "size"),
            total_mensal=("total_mensal", "median"),
            custo_por_dormitorio=("custo_por_dormitorio", "median"),
            preco_m2=("preco_m2", "median"),
            distancia_km=("distancia_km", "first"),
            indice=("indice", "median"),
            minimo=("total_mensal", "min"),
            maximo=("total_mensal", "max"),
        )
        .reset_index()
    )
