from indicadores2 import Indicadores
from logger import Logger

def filtro_parte_baja_rango(ind:Indicadores,log:Logger,escala,cvelas,porcentaje_bajo=.3):
    minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
    maximo_compra = minimo + (maximo - minimo) *  porcentaje_bajo
    precio = ind.precio_mas_actualizado()
    ret = precio < maximo_compra
    log.log( f'parte_baja_rango {escala} min {minimo} px {precio} [max_compra {maximo_compra}] maximo {maximo} {ret}'  )
    return ret 