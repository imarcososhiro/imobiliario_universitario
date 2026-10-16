"""Imóveis para alugar em São Carlos no site da Roca Imóveis (roca.com.br).

O site é feito em Next.js e tem uma busca própria (/api/solr/search/) que responde em JSON,
com os mesmos dados que aparecem nas páginas. Então não precisa de navegador nem de ler HTML:
1. O sitemap (indicado no robots.txt) lista todos os imóveis, com links como
   /imovel/locacao/apartamentos/sao-carlos/jardim-paraiso/61376
2. A busca recebe os códigos em lotes e devolve os dados de cada imóvel.

São uns 12 pedidos por dia, em vez de baixar ~2.100 páginas de ~430 KB cada.
A busca também traz o endereço completo, que o projeto não guarda (fica no nível do bairro).
"""
import json
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import quote
from xml.etree import ElementTree

from scraper.download import baixar
from scraper.modelo import Imovel

log = logging.getLogger(__name__)

FONTE = "roca"
SITE = "https://roca.com.br"
URL_SITEMAP = f"{SITE}/sitemaps/propertys.xml"
URL_BUSCA = f"{SITE}/api/solr/search/"
CIDADE = "sao-carlos"
# Categoria no link -> tipo do imóvel (os mesmos tipos da Cardinali; comerciais e terrenos ficam de fora)
TIPOS = {"apartamentos": "Apartamento", "casas": "Casa"}
POR_PEDIDO = 200  # códigos por pedido à busca (todos de uma vez deixariam o link comprido demais)

RE_LINK = re.compile(rf"^{re.escape(SITE)}/imovel/(?:locacao|venda-e-locacao)/(?P<categoria>[a-z-]+)/"
                     rf"(?P<cidade>[a-z-]+)/[^/]+/(?P<codigo>\d+)$")
NAMESPACE_SITEMAP = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

# Características (campo prop_char_<número> da busca) -> campo do Imovel. Os números vêm da
# tabela de características do site: 5 Dormitórios, 6 Sendo dormitórios suítes, 176 Total de
# banheiros, 12 Garagens, 95 Área útil, 1 Área construída, 2 Área total
CONTAGENS = {5: "dormitorios", 6: "suites", 176: "banheiros", 12: "vagas"}
AREAS = {95: "area_util_m2", 1: "area_construida_m2", 2: "area_total_m2"}


class ErroDeExtracao(Exception):
    """A resposta do site não está no formato esperado (provavelmente o site mudou).

    O texto recebido vai junto em `html`, para ser salvo e investigado (como na Cardinali).
    """

    def __init__(self, mensagem: str, html: str | None = None):
        super().__init__(mensagem)
        self.html = html


@dataclass
class ColetaEmLote:
    imoveis: list[Imovel] = field(default_factory=list)
    anunciados: int = 0                    # imóveis de São Carlos para alugar no sitemap
    falhas: list[tuple[str, str]] = field(default_factory=list)  # (link, motivo)
    indisponiveis: int = 0                 # estavam no sitemap, mas a busca não os devolveu
    nao_alugam_para_estudantes: int = 0    # o site marca alguns imóveis assim; ficam de fora


def listar_imoveis(xml: str) -> dict[int, str]:
    """Os apartamentos e casas para alugar em São Carlos que estão no sitemap: código -> link."""
    imoveis = {}
    for loc in ElementTree.fromstring(xml).iter(f"{NAMESPACE_SITEMAP}loc"):
        achado = RE_LINK.match((loc.text or "").strip())
        if achado and achado["cidade"] == CIDADE and achado["categoria"] in TIPOS:
            imoveis[int(achado["codigo"])] = achado.group(0)
    return imoveis


def url_busca(codigos: list[int]) -> str:
    """A busca recebe um JSON no próprio link: {"idtsPropertys": [códigos], "numRows": quantos}."""
    consulta = json.dumps({"idtsPropertys": codigos, "numRows": len(codigos)}, separators=(",", ":"))
    return URL_BUSCA + quote(consulta)


def _valor(doc: dict, campo: str) -> float | None:
    """Valores em reais: zero ou vazio viram None (o site usa 0 para "não tem")."""
    valor = doc.get(campo)
    return float(valor) if valor else None


def _foto(doc: dict) -> str | None:
    fotos = json.loads(doc.get("jsonPhotos") or "[]")
    return next((foto["urlPhoto"] for foto in fotos
                 if not foto.get("flgNotShowSite") and str(foto.get("urlPhoto", "")).startswith("https://")), None)


def imovel_da_busca(doc: dict, url: str, coletado_em: str | None = None) -> Imovel:
    """Converte um imóvel da busca do site para o formato comum (scraper/modelo.py)."""
    aluguel = None if doc.get("flgHideValLocationSite") else _valor(doc, "valLocation")
    condominio, iptu = _valor(doc, "valCondominium"), _valor(doc, "valMonthIptu")
    bairro = doc["namDistrict"].strip()
    imovel = Imovel(
        codigo=int(doc["idtProperty"]),
        fonte=FONTE,
        url=url,
        tipo=TIPOS[RE_LINK.match(url)["categoria"]],
        subtipo=doc["namSubCategory"],
        bairro=bairro.title() if bairro.isupper() else bairro,  # o site às vezes escreve "CENTRO"
        titulo=doc.get("desTitleSite") or None,
        # Casas de subtipo "Comercial" são para negócio: o dashboard deixa de fora, como na Cardinali
        finalidade="Comercial" if doc["namSubCategory"] == "Comercial" else "Residencial",
        situacao="RESERVADO" if doc.get("flgReservedLocation") else "DISPONÍVEL",
        aluguel=aluguel,
        condominio=condominio,
        iptu=iptu,
        # Como na Cardinali: aluguel + condomínio + IPTU. Sem aluguel ("consulte"), sem total
        total_mensal=round(aluguel + (condominio or 0) + (iptu or 0), 2) if aluguel else None,
        foto_url=_foto(doc),
        coletado_em=coletado_em,
    )
    for numero, campo in CONTAGENS.items():
        valor = doc.get(f"prop_char_{numero}")
        setattr(imovel, campo, int(valor) if valor not in (None, "") else None)
    for numero, campo in AREAS.items():
        valor = doc.get(f"prop_char_{numero}")
        setattr(imovel, campo, float(valor) if valor else None)
    return imovel


def baixar_imoveis(cliente, hoje: str) -> ColetaEmLote:
    """Lista os imóveis pelo sitemap e busca os dados deles em lotes."""
    sitemap = baixar(cliente, URL_SITEMAP)
    links = listar_imoveis(sitemap)
    if not links:
        raise ErroDeExtracao("sitemap da Roca sem imóveis de São Carlos para alugar: o site mudou?", html=sitemap)
    log.info("Roca: %d imóveis de São Carlos para alugar no sitemap", len(links))

    resultado = ColetaEmLote(anunciados=len(links))
    codigos = list(links)
    devolvidos = 0
    for inicio in range(0, len(codigos), POR_PEDIDO):
        resposta = baixar(cliente, url_busca(codigos[inicio:inicio + POR_PEDIDO]))
        try:
            docs = json.loads(resposta)["response"]["docs"]
        except (ValueError, KeyError, TypeError) as erro:
            raise ErroDeExtracao(f"resposta da busca da Roca fora do formato esperado ({erro!r})",
                                 html=resposta) from erro
        devolvidos += len(docs)
        for doc in docs:
            url = links.get(doc.get("idtProperty"), f"{SITE}/imovel/{doc.get('idtProperty')}")
            if not doc.get("flgShowSite", 1):
                resultado.indisponiveis += 1
                continue
            if doc.get("flgNotRentedForStudents"):
                resultado.nao_alugam_para_estudantes += 1
                continue
            try:
                resultado.imoveis.append(imovel_da_busca(doc, url, coletado_em=hoje))
            except (KeyError, TypeError, ValueError, AttributeError) as erro:
                # Como na Cardinali: o erro é registrado e entra na taxa de falhas
                resultado.falhas.append((url, f"{type(erro).__name__}: {erro}"))
                log.warning("Falha em %s: %s", url, erro)
    resultado.indisponiveis += len(links) - devolvidos
    log.info("Roca: %d imóveis lidos, %d não alugam para estudantes", len(resultado.imoveis),
             resultado.nao_alugam_para_estudantes)
    return resultado
