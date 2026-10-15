"""Cliente HTTP que tenta de novo quando o site falha temporariamente."""
import logging
import random
import time

import httpx

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; imobiliario-universitario/1.0; "
    "+https://github.com/imarcososhiro/imobiliario_universitario)"
)
TENTATIVAS = 4
ESPERA_BASE_S = 2.0
# Respostas do servidor que costumam ser passageiras e valem uma nova tentativa
STATUS_TEMPORARIOS = {429, 500, 502, 503, 504}


class PaginaIndisponivel(Exception):
    """A página não existe mais (ex.: o imóvel saiu do site entre a listagem e o download)."""


class FalhaDeDownload(Exception):
    """A página não pôde ser baixada nem depois de todas as tentativas."""


def criar_cliente(**opcoes) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(20.0),
        follow_redirects=True,
        **opcoes,
    )


def baixar(cliente: httpx.Client, url: str) -> str:
    """Baixa uma página e devolve o HTML.

    Em falhas temporárias (timeout, conexão, HTTP 5xx/429) espera 2 s, 4 s, 8 s...
    e tenta de novo (backoff exponencial). A variação aleatória na espera evita
    que downloads em paralelo tentem de novo todos ao mesmo tempo.
    """
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = cliente.get(url)
        except httpx.TransportError as erro:
            motivo = type(erro).__name__
        else:
            # Imóvel retirado do site: a Cardinali redireciona para /404.php
            if resposta.status_code == 404 or resposta.url.path.startswith("/404"):
                raise PaginaIndisponivel(url)
            if resposta.status_code not in STATUS_TEMPORARIOS:
                resposta.raise_for_status()
                # Como os navegadores, lê "ISO-8859-1" como windows-1252 (que tem “aspas” e travessão)
                if (resposta.encoding or "").lower() in ("iso-8859-1", "latin-1"):
                    resposta.encoding = "cp1252"
                return resposta.text
            motivo = f"HTTP {resposta.status_code}"

        if tentativa == TENTATIVAS:
            raise FalhaDeDownload(f"{motivo} após {TENTATIVAS} tentativas: {url}")
        espera = ESPERA_BASE_S * 2 ** (tentativa - 1) * random.uniform(0.8, 1.2)
        log.warning("%s em %s (tentativa %d/%d); tentando de novo em %.1f s",
                    motivo, url, tentativa, TENTATIVAS, espera)
        time.sleep(espera)
