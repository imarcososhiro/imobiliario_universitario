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


def metros_quadrados(valor) -> str:
    return SEM_DADO if _vazio(valor) else f"{numero(valor)} m²"


def data(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")
