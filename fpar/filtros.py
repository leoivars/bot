from indicadores2 import Indicadores
from logger import Logger

def filtro_parte_baja_rango(ind:Indicadores,log:Logger,escala,cvelas,porcentaje_bajo=.3):
    minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
    maximo_compra =  minimo + (maximo - minimo) *  porcentaje_bajo 
    precio = ind.precio_mas_actualizado()
    ret = precio < maximo_compra
    log.log( f'parte_baja_rango {escala} min {minimo} px {precio} [max_compra {maximo_compra}] maximo {maximo} {ret}'  )
    return ret 

def filtro_zona_volumen(ind:Indicadores,log:Logger,escala,periodos):
    ret = False
    maximos=ind.lista_picos_maximos_ema(escala,periodos,200,'close',15,15) 
    if len(maximos)>0:
       fin = -maximos[0][0]
       pos_pico, r_vol_pico, r_vol, vol_ema = ind.zona_de_alto_volumen(escala,-1,fin) 
       log.log(f'pos {pos_pico} volpico {r_vol_pico}, vol {r_vol}, vol_ema {vol_ema}')

       #hay un pico a menos de 25,
       # el volumen pico es mayor a 2
       # el volumen pico es mayor el que volumen promedio de las ultimas velas
       # el volumen de la ultima vela cerrada esta por debajo del promedio (ma)
       ret = pos_pico < 25 and r_vol_pico > 2 and r_vol_pico > r_vol and r_vol < 2 and vol_ema < 1 
    
    return ret

def filtro_pendientes_emas_positivas(ind:Indicadores,log:Logger,escala,periodos,cpendientes=4):
    ret = ind.pendientes_positivas_ema(escala,periodos,cpendientes)
    log.log(f'filtro_pendientes_emas_positivas {ret}')
    return ret

