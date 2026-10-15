"""Formato comum dos imóveis coletados, igual para qualquer imobiliária."""
from dataclasses import dataclass, fields


@dataclass
class Imovel:
    codigo: int                 # código do imóvel no site (chave para acompanhar o histórico)
    fonte: str                  # imobiliária de origem, ex.: "cardinali"
    url: str
    tipo: str                   # Apartamento, Casa
    subtipo: str                # Padrão, Kitchnet, Sobrado...
    bairro: str
    titulo: str | None = None
    finalidade: str | None = None           # Residencial, Comercial...
    situacao: str | None = None             # DISPONÍVEL, RESERVADO...
    aluguel: float | None = None            # aluguel atual, sem bonificação
    aluguel_anterior: float | None = None   # preço "DE:" quando o imóvel está em promoção
    aluguel_bonificado: float | None = None  # aluguel com desconto por pagar em dia
    condominio: float | None = None
    iptu: float | None = None
    total_mensal: float | None = None       # total por mês informado pelo site
    dormitorios: int | None = None
    suites: int | None = None
    banheiros: int | None = None
    vagas: int | None = None
    area_util_m2: float | None = None
    area_construida_m2: float | None = None
    area_total_m2: float | None = None
    foto_url: str | None = None
    coletado_em: str | None = None          # data da coleta (AAAA-MM-DD)


COLUNAS = [campo.name for campo in fields(Imovel)]
