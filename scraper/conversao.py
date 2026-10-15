"""Conversão dos textos do site ("1.667,50", "37.00 m²", "Consulte-nos") em valores."""
import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Remove acentos, deixa minúsculo e junta espaços: "C. Bonificação " -> "c. bonificacao"."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def para_numero(texto: str | None) -> float | None:
    """Converte "1.667,50", "37.00 m²" ou "R$ 950" em float. Texto sem número vira None."""
    if not texto:
        return None
    achado = re.search(r"\d[\d.,]*", texto)
    if not achado:
        return None
    numero = achado.group().rstrip(".,")
    if "," in numero and "." in numero:
        # O separador que aparece por último é o decimal: "1.667,50" ou "1,667.50"
        if numero.rfind(",") > numero.rfind("."):
            numero = numero.replace(".", "").replace(",", ".")
        else:
            numero = numero.replace(",", "")
    elif "," in numero:
        numero = numero.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", numero):
        numero = numero.replace(".", "")  # "1.200" é mil e duzentos, não 1,2
    return float(numero)


def para_inteiro(texto: str | None) -> int | None:
    numero = para_numero(texto)
    return None if numero is None else int(numero)
