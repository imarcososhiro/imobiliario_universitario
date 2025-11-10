# Script pra guardar as coordenadas dos bairros coletados manualmente
# Também contém a função Buscar_coords, usada em outros scripts, que procura o nome do bairro no dicionário de coordenadas

coordenadas_bairros = {
    'Centro': (-22.011108751067262, -47.891135023577114),
    'Cidade Jardim': (-21.99828963135949, -47.89442350979536),
    'Jardim Lutfalla': (-22.004692816173417, -47.89355504374654),
    'Jardim Macarengo': (-22.00801536715194, -47.88837433633512),
    'Vila Costa do Sol': (-22.002575046600796, -47.883635416847206),
    'Vila Monteiro (Gleba I)': (-22.02544671109399, -47.88954201742408),
    'Vila Monteiro Gleba I' : (-22.02544671109399, -47.88954201742408)

}

def Buscar_coords(nome_bairro):
    return coordenadas_bairros[nome_bairro]
