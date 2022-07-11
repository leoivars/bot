from escalas import *
def determinar_escala(costo_trade,costo_estrategia,escala_estrategia,moneda_contra_disponible):
    '''
    Determina una escala a tradear en funcion del dinero disponible y los parametros de la estrategia utilizada.
    costo_trade = la cantidad de moneda contra que se utiliza para un trade
    costo_estrategia = cantidad de trades que se supone necesita tener disponibles para poder seguir recomprando en caso de baja
    escala_estrategia = la escala en que ha sido evaluado el costo_estrategia
    moneda_contra_disponible = total asset disponible del par para tradear
    '''

    trades_disponibles = int(moneda_contra_disponible/costo_trade)
    
    disponible = trades_disponibles / costo_estrategia 

    if disponible > 3:
        return zoom(escala_estrategia,2)

    if disponible > 2:
        return zoom(escala_estrategia,1)

    if disponible > 1:
        return escala_estrategia

    if disponible > 0.75:
        return zoom_out(escala_estrategia,2)

    if disponible > 0.5:
        return zoom_out(escala_estrategia,3)
    
    return zoom_out(escala_estrategia,4)
