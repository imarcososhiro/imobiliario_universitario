"""Imóveis para alugar em São Carlos no site da Cardinali (www.cardinali.com.br).

O site é renderizado no servidor, então não precisa de navegador: basta baixar o HTML.
1. As páginas de listagem (/alugar/Sao-Carlos/Apartamento?pag=N) trazem os links dos imóveis.
2. A página de cada imóvel traz os valores, as características e um JSON-LD (schema.org).
"""
import json
import logging
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scraper.conversao import normalizar_texto, para_inteiro, para_numero
from scraper.download import baixar
from scraper.modelo import Imovel

log = logging.getLogger(__name__)

FONTE = "cardinali"
SITE = "https://www.cardinali.com.br"
CIDADE = "Sao-Carlos"
CATEGORIAS = ("Apartamento", "Casa")
MAX_PAGINAS = 100  # trava de segurança caso a paginação do site mude

RE_LINK_IMOVEL = re.compile(r"^(https?://[^/]+)?/(alugar|comprar)/.+/\d+$")

# Rótulo da linha no quadro de valores (normalizado) -> campo do Imovel.
# Rótulos exatos, para não confundir "Total / Mês" com o "Total" da venda.
ROTULOS_VALORES = {
    "aluguel": "aluguel",
    "por: aluguel": "aluguel",
    "de: aluguel": "aluguel_anterior",
    "c. bonificacao": "aluguel_bonificado",
    "condominio": "condominio",
    "iptu": "iptu",
    "total / mes": "total_mensal",
}

# Classe CSS do item no quadro de características -> (campo do Imovel, conversor)
CARACTERISTICAS = {
    "tipo-prop": ("finalidade", str),
    "dorm-ico-imo": ("dormitorios", para_inteiro),
    "suites-ico-imo": ("suites", para_inteiro),
    "banh-ico-imo": ("banheiros", para_inteiro),
    "gar-ico-imo": ("vagas", para_inteiro),
    "a-util-ico-imo": ("area_util_m2", para_numero),
    "a-const-ico-imo": ("area_construida_m2", para_numero),
    "a-total-ico-imo": ("area_total_m2", para_numero),
}


class ErroDeExtracao(Exception):
    """O HTML não está no formato esperado (provavelmente o site mudou)."""


def url_listagem(categoria: str, pagina: int) -> str:
    return f"{SITE}/alugar/{CIDADE}/{categoria}?pag={pagina}"


def normalizar_url_imovel(href: str) -> str:
    """Deixa o link absoluto e sempre na versão de aluguel.

    Imóveis que estão à venda e para alugar às vezes aparecem na listagem de
    aluguel com link /comprar/...; a página /alugar/ do mesmo código também existe.
    """
    caminho = urlsplit(urljoin(SITE, href)).path
    return SITE + re.sub(r"^/comprar/", "/alugar/", caminho)


def extrair_listagem(html: str) -> tuple[list[str], bool, int | None]:
    """Lê uma página de listagem.

    Devolve (links dos imóveis, se existe próxima página, total anunciado no título).
    """
    soup = BeautifulSoup(html, "lxml")

    urls = []
    for card in soup.select("div.card-imo"):
        link = card.find("a", href=RE_LINK_IMOVEL)
        if link:
            url = normalizar_url_imovel(link["href"])
            if url not in urls:
                urls.append(url)

    # O último link da paginação é o "»"; na última página ele vira "javascript:void(0)"
    paginacao = soup.select(".pagination a[href]")
    tem_proxima = bool(paginacao) and not paginacao[-1]["href"].lower().startswith("javascript")

    titulo = soup.find("h1")
    achado = re.search(r"(\d[\d.]*)\s*im", titulo.get_text(" ", strip=True)) if titulo else None
    total = int(achado.group(1).replace(".", "")) if achado else None

    return urls, tem_proxima, total


def listar_urls(cliente) -> tuple[list[str], int]:
    """Percorre as listagens de cada categoria. Devolve (links dos imóveis, total anunciado)."""
    urls: dict[str, None] = {}  # dict guarda a ordem de chegada e ignora repetidos
    anunciados = 0
    for categoria in CATEGORIAS:
        for pagina in range(1, MAX_PAGINAS + 1):
            links, tem_proxima, total = extrair_listagem(baixar(cliente, url_listagem(categoria, pagina)))
            if pagina == 1:
                if not links or total is None:
                    raise ErroDeExtracao(f"listagem de {categoria} sem imóveis ou sem total: o site mudou?")
                total_categoria = total
            novos = [url for url in links if url not in urls]
            urls.update(dict.fromkeys(novos))
            # Páginas além da última repetem a última, então "nada novo" também encerra
            if not tem_proxima or not novos:
                break
        anunciados += total_categoria
        log.info("%s: %d páginas de listagem, %d imóveis anunciados", categoria, pagina, total_categoria)
    return list(urls), anunciados


def partes_da_url(url: str) -> tuple[str, str, str, int]:
    """Lê (tipo, subtipo, bairro, código) de /alugar/<cidade>/<tipo>/<subtipo>/<bairro>/<código>."""
    partes = urlsplit(url).path.strip("/").split("/")
    if len(partes) != 6 or not partes[-1].isdigit():
        raise ErroDeExtracao(f"URL fora do padrão esperado: {url}")
    _, _, tipo, subtipo, bairro, codigo = partes
    return tipo, subtipo, bairro, int(codigo)


def extrair_imovel(html: str, url: str, coletado_em: str | None = None) -> Imovel:
    """Lê a página de um imóvel. Levanta ErroDeExtracao se o formato não for o esperado."""
    tipo, subtipo, bairro, codigo = partes_da_url(url)
    caminho = urlsplit(url).path.rstrip("/")
    caminho_bairro = caminho.rsplit("/", 1)[0]
    caminho_subtipo = caminho_bairro.rsplit("/", 1)[0]

    soup = BeautifulSoup(html, "lxml")
    imovel = Imovel(
        codigo=codigo,
        fonte=FONTE,
        url=url,
        tipo=tipo,
        # Os links logo abaixo do título trazem os nomes com acento, ex.: "Vila Monteiro (Gleba I)"
        subtipo=_texto_do_link(soup, caminho_subtipo, padrao=subtipo),
        bairro=_texto_do_link(soup, caminho_bairro, padrao=bairro),
        coletado_em=coletado_em,
    )
    _ler_valores(soup, imovel)
    _ler_caracteristicas(soup, imovel)
    _ler_json_ld(soup, imovel)

    if imovel.aluguel is None and imovel.aluguel_bonificado is None:
        # Aluguel "Consulte-nos": o "Total / Mês" do site seria só condomínio + IPTU
        imovel.total_mensal = None
    return imovel


def _texto_do_link(soup: BeautifulSoup, href: str, padrao: str) -> str:
    link = soup.find("a", href=href)
    texto = link.get_text(" ", strip=True) if link else ""
    return texto or padrao.replace("-", " ")


def _ler_valores(soup: BeautifulSoup, imovel: Imovel) -> None:
    bloco = soup.find(id="valores_imovel")
    if bloco is None:
        raise ErroDeExtracao("quadro de valores (#valores_imovel) não encontrado")

    selo = bloco.select_one(".badge")
    imovel.situacao = selo.get_text(" ", strip=True) if selo else None

    reconhecidos = 0
    for linha in bloco.select(".row"):
        colunas = linha.find_all("div", recursive=False)
        if len(colunas) != 2:
            continue
        campo = ROTULOS_VALORES.get(normalizar_texto(colunas[0].get_text(" ", strip=True)))
        if campo and getattr(imovel, campo) is None:
            setattr(imovel, campo, para_numero(colunas[1].get_text(" ", strip=True)))
            reconhecidos += 1
    if reconhecidos == 0:
        raise ErroDeExtracao("nenhum valor reconhecido no quadro de valores")


def _ler_caracteristicas(soup: BeautifulSoup, imovel: Imovel) -> None:
    codigo = soup.select_one(".card-imo-radius .codigo-imo .fw-bold")
    if codigo is None:
        raise ErroDeExtracao("quadro de características não encontrado")
    if para_inteiro(codigo.get_text()) != imovel.codigo:
        raise ErroDeExtracao(f"código na página ({codigo.get_text(strip=True)}) difere do da URL")

    for classe, (campo, converter) in CARACTERISTICAS.items():
        valor = soup.select_one(f".card-imo-radius .{classe} .fw-bold")
        if valor is not None:
            setattr(imovel, campo, converter(valor.get_text(" ", strip=True)))


def _ler_json_ld(soup: BeautifulSoup, imovel: Imovel) -> None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(script.string or "", strict=False)
        except json.JSONDecodeError:
            continue
        if isinstance(dados, dict) and dados.get("@type") == "Product":
            imovel.titulo = dados.get("name")
            imagens = dados.get("image") or []
            if isinstance(imagens, str):
                imagens = [imagens]
            imovel.foto_url = imagens[0] if imagens else None
            break

    if imovel.titulo is None:
        titulo = soup.find("h1")
        imovel.titulo = titulo.get_text(" ", strip=True) if titulo else None
