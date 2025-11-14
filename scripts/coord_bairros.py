# Script pra guardar as coordenadas dos bairros coletados manualmente
# Também contém a função Buscar_coords, usada em outros scripts, que procura o nome do bairro no dicionário de coordenadas

coordenadas_bairros = {
    'Centro': (-22.016570299078424, -47.89118675813608),
    'Cidade Jardim': (-21.99828963135949, -47.89442350979536),
    'Jardim Lutfalla': (-22.004692816173417, -47.89355504374654),
    'Vila Costa do Sol': (-22.002575046600796, -47.883635416847206),
    'Vila Monteiro (Gleba I)': (-22.02544671109399, -47.88954201742408),
    'Vila Monteiro Gleba I' : (-22.02544671109399, -47.88954201742408),
    'Jardim Paulistano' : (-21.993222867008416, -47.89849479634273),
    'Jardim Paraiso' : (-22.006906553055877, -47.90270021132936),
    'Jardim Macarengo' : (-22.008449826110827, -47.88854555838885),
    'Cidade Universitária' : (-22.006500883741783, -47.894678489649564),
    'Parque Arnold Schimidt' : (-22.000281473620426, -47.89698636408029),
    'Jardim Santa Paula' : (-22.00063071829572, -47.90076881950781),
    'Jardim Bandeirantes' : (-22.001797596845424, -47.90801814923515),
    'Jardim Centenario' : (-21.999624460524412, -47.90450384190019),
    'Jardim Nova Santa Paula' : (-21.996137148890007, -47.89854244601391),
    'Tijuco Preto' : (-22.001641638176103, -47.889351202497096),
    'Jardim Bethania' : (-22.013502077630495, -47.881355638279906),
    'Vila Elizabeth' : (-22.006493291459726, -47.88385035851929),
    'Jardim São Carlos' : (-22.01960124676203, -47.89357660672348),
    'Parque Santa Monica' : (-22.013020474086815, -47.90606012674151),
    'Parque Santa Monica II' : (-22.017071638471595, -47.90994438029053),
    'Jardim Alvorada' : (-22.006910925986677, -47.90861677353405),
    'Vila Celina' : (-21.99398982087837, -47.88826008794782),
    'Vila Marina' : (-21.993967410368935, -47.88961913416678),
    'Vila Marigo' : (-21.99267758044676, -47.886141835407784),
    'Jardim Hikari' : (-21.993226689444505, -47.90191680110434),
    'Jardim Hikare' : (-21.994221493799696, -47.90153056303471),
    'Parque Industrial' : (-21.988975087881347, -47.900043415689886),
    'Parque Delta' : (-21.99147351723397, -47.8958359968184),
    'Monjolinho' : (-21.991390132383316, -47.89258473077294),
    'Jardim Jockei Club A' : (-21.98151618729711, -47.89960540640717),
    'Jardim Jockey Clube' : (-21.97515484587098, -47.899587429888925),
    'Jardim Jockei Club' : (-21.975221776805196, -47.90297964168885),
    'Parque Espraiado' : (-21.989495647280744, -47.87466921288066)
}

def Buscar_coords(nome_bairro):
    return coordenadas_bairros[nome_bairro]
