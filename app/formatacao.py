"""Números no formato brasileiro: "R$ 1.234", "2,3 km", "37 m²"."""
import math
from datetime import date

SEM_DADO = "—"


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def numero(valor, casas: int = 0) -> str:
    """1234.5 -> "1.234,5" (ponto separa milhar e vírgula separa decimal)."""
    if _vazio(valor):
        return SEM_DADO
    texto = f"{valor:,.{casas}f}"  # formato americano: 1,234.5
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def reais(valor, casas: int = 0) -> str:
    return SEM_DADO if _vazio(valor) else f"R$ {numero(valor, casas)}"


def km(valor) -> str:
    return SEM_DADO if _vazio(valor) else f"{numero(valor, 1)} km"


def minutos_a_pe(distancia_km) -> str:
    """Tempo aproximado de caminhada: 1,2 km -> "~20 min a pé".

    A distância é em linha reta e as ruas fazem curvas, então soma 30% ao caminho e
    anda a 4,8 km/h (80 m por minuto), arredondando para múltiplos de 5 minutos.
    """
    if _vazio(distancia_km):
        return SEM_DADO
    minutos = distancia_km * 1000 * 1.3 / 80
    return f"~{max(5, 5 * round(minutos / 5))} min a pé"


def metros_quadrados(valor) -> str:
    return SEM_DADO if _vazio(valor) else f"{numero(valor)} m²"


def data(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")
