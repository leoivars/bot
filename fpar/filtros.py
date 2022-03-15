from indicadores2 import Indicadores
from logger import Logger


def filtro_parte_baja_rango(ind:Indicadores,log:Logger,escala,cvelas,porcentaje_bajo=.3):
    minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
    maximo_compra =  minimo + (maximo - minimo) *  porcentaje_bajo 
    precio = ind.precio(escala)
    ret = precio < maximo_compra
    log.log( f'parte_baja_rango {escala} min {minimo} px {precio} [max_compra {maximo_compra}] maximo {maximo} {ret}'  )
    return ret 

def filtro_parte_alta_rango(ind:Indicadores,log:Logger,escala,cvelas,porcentaje_bajo=.75):
    minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
    maximo_compra =  minimo + (maximo - minimo) *  porcentaje_bajo 
    precio = ind.precio(escala)
    ret = precio > maximo_compra
    log.log( f'filtro_parte_alta_rango {escala} min {minimo} px {precio} [max_compra {maximo_compra}] maximo {maximo} {ret}'  )
    return ret 

def filtro_precio_mayor_maximo(ind:Indicadores,log:Logger,escala,cvelas,vela_ini):
    maximo = ind.maximo_x_vol(escala,cvelas,3,vela_ini)   #3 velas
    if maximo is None:
        ret = False
        precio = None
    else:
        precio = ind.precio(escala)
        ret = precio > maximo
    log.log( f'filtro_precio_mayor_maximo {escala} cvel {cvelas} ini {vela_ini} maximo {maximo} px {precio} {ret}' )
    return ret

def filtro_precio_mayor_minimo(ind:Indicadores,log:Logger,escala,cvelas,vela_ini):
    minimo = ind.minimo_x_vol(escala,cvelas,3,vela_ini)
    if minimo is None:
        ret = False
        precio = None
    else:    
        precio = ind.precio(escala)
        ret = precio > minimo
    log.log( f'filtro_precio_mayor_minimo {escala} cvel {cvelas} ini {vela_ini} minimo {minimo} px {precio} {ret}' )
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
       ret = pos_pico < 7 and r_vol_pico > 2 #and r_vol_pico > r_vol and r_vol > vol_ema 
    
    return ret

def filtro_picos_volumen(ind:Indicadores,log:Logger,escala,periodos,max_pos_ultimo_pico=17,min_cant_picos=3):
    ret = False
    maximos=ind.lista_picos_maximos_ema(escala,periodos,200,'close',15,15) 
    if len(maximos)>0:
       fin = -maximos[0][0]
       lista_picos = ind.picos_de_alto_volumen(escala,fin) 
       cantidad_picos = len(lista_picos)
       if cantidad_picos >0:
           pos_ultimo=lista_picos[0][0]
           log.log(f'picos_de_alto_volumen parametro_fin {fin}  pos {pos_ultimo} {lista_picos}')
           ret = pos_ultimo < max_pos_ultimo_pico and cantidad_picos >=min_cant_picos
    
    return ret

def filtro_velas_de_impulso(ind:Indicadores,log:Logger,escala,periodos,max_pos_ultimo_impulso=17,min_cant_impulsos=3):
    ret = False
    maximos=ind.lista_picos_maximos_ema(escala,periodos,300,'close',4,4) 
    if len(maximos)>0:
       fin = -maximos[0][0]
       lista_velas_impulso = ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
       xvol_impulso = ind.xvolumen_de_impulso(escala,sentido=-1,vela_fin=fin) 
       log.log(f'lista_velas_impulso {lista_velas_impulso}')
       log.log(f'xvol_impulso {xvol_impulso}')
       cantidad_velas = len(lista_velas_impulso)
       if cantidad_velas >0:
           pos_ultimo=lista_velas_impulso[0][0]
           cvelas_x_10 = 0                          #contador de velas de impulso > a 10x
           for vi in lista_velas_impulso:
               if vi[1]>10:
                   cvelas_x_10 += 1
           ret =cvelas_x_10 > 0 and pos_ultimo < max_pos_ultimo_impulso and cantidad_velas >=min_cant_impulsos
           log.log(f'velas_de_impulso {ret} {cantidad_velas} parametro_fin {fin}  pos {pos_ultimo}')
    
    return ret

def filtro_xvolumen_de_impulso(ind:Indicadores,log:Logger,escala,periodos,sentido=-1,xmin_impulso=50):
    '''  desde que empezó a bajar, suma todo el volumen de las velas segun el sentido( -1 bajista, 1 alcista, 0 todo) y lo compara con el volumen promedio
         convirtiendolo en x veces mas. 
         Si ese volumen comparado es mayor al parametrizado(xmin_impulso): retorna True
    '''
    ret = False
    maximos=ind.lista_picos_maximos_ema(escala,periodos,300,'close',6,6) 
    if len(maximos)>0:
       fin = -maximos[0][0]
       lista_velas_impulso = ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
       xvol_impulso = ind.xvolumen_de_impulso(escala,sentido,vela_fin=fin) 
       log.log(f'velas {-fin} lista_velas_impulso {lista_velas_impulso} ')
       log.log(f'xvol_impulso {xvol_impulso}')
       ret = xvol_impulso >= xmin_impulso
       log.log(f'filtro_xvolumen_de_impulso {ret}')

    return ret

def filtro_xvolumen_total(ind:Indicadores,log:Logger,escala,periodos, xmin_impulso=50):
    '''  desde que empezó a bajar, suma todo el volumen todas las velas y lo compara con el volumen promedio
         convirtiendolo en x veces mas. 
         Si ese volumen comparado es mayor al parametrizado(xmin_impulso): retorna True
    '''
    ret = False
    maximos=ind.lista_picos_maximos_ema(escala,periodos,300,'close',6,6) 
    if len(maximos)>0:
       fin = -maximos[0][0]
       lista_velas_impulso = ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
       xvol_impulso = ind.xvolumen_de_impulso(escala,sentido=-1,vela_fin=fin) 
       log.log(f'velas {-fin} lista_velas_impulso {lista_velas_impulso} ')
       log.log(f'xvol_impulso {xvol_impulso}')
       ret = xvol_impulso >= xmin_impulso
       log.log(f'filtro_xvolumen_de_impulso {ret}')

    return ret




def filtro_pico_minimo_ema(ind:Indicadores,log:Logger,escala,periodos):
    ret=False
    minimos = ind.lista_picos_minimos_ema(escala,periodos,10,'close',5,1)
    if len(minimos)>0:
        pos = minimos[0][0]
        if pos <=3:
            ret = True
    log.log(f'filtro_pico_minimo_ema {minimos} {ret}')        
    return ret    

def filtro_pico_minimo_ema_low(ind:Indicadores,log:Logger,escala,periodos):
    ret=False
    minimos = ind.lista_picos_minimos_ema(escala,periodos,4,'low',5,1)
    if len(minimos)>0:
        pos = minimos[0][0]
        if pos <=3:
            ret = True
    log.log(f'filtro_pico_minimo_ema_low {minimos} {ret}')        
    return ret    


def filtro_pendientes_emas_positivas(ind:Indicadores,log:Logger,escala,periodos,cpendientes=4):
    ret = ind.pendientes_positivas_ema(escala,periodos,cpendientes)
    log.log(f'filtro_pendientes_emas_positivas {ret}')
    return ret

def filtro_dos_emas_positivas(ind:Indicadores,log:Logger,escala,ema1_per,ema2_per):
    ret = False
    if ind.pendiente_positiva_ema(escala,ema1_per):
        log.log('filtro_dos_emas_positivas ema1_ok')
        ret = ind.pendiente_positiva_ema(escala,ema2_per)
        
    log.log(f'filtro_dos_emas_positivas {ret}')

    return ret 

def filtro_tres_emas_positivas(ind:Indicadores,log:Logger,escala,ema1_per,ema2_per,ema3_per):
    ret = False
    if ind.pendiente_positiva_ema(escala,ema1_per):
        log.log(f'filtro_tres_emas_positivas ema {ema1_per} ok')
        if ind.pendiente_positiva_ema(escala,ema2_per):
            log.log(f'filtro_tres_emas_positivas ema {ema2_per} ok')
            ret = ind.pendiente_positiva_ema(escala,ema3_per)
        
    log.log(f'filtro_tres_emas_positivas {ret}')

    return ret 


def filtro_de_rsi_minimo_cercano(ind:Indicadores,log:Logger,escala,rsi_inferior,pos_rsi_inferior=(2,15),max_rsi=55):
    rsi_min,rsi_min_pos,_,rsi= ind.rsi_minimo_y_pos(escala,  pos_rsi_inferior[1]    )
    resultado_filtro=  rsi_min < rsi_inferior and pos_rsi_inferior[0] <= rsi_min_pos <= pos_rsi_inferior[1]  and rsi<max_rsi
    log.log(f'{resultado_filtro} <-- filtro_de_rsi_minimo_cercano: ')
    log.log(f'    busco {rsi_inferior}, actual {rsi_min}')
    log.log(f'    rango de cercanía {pos_rsi_inferior}, actual {rsi_min_pos}')
    log.log(f'    rsi maximo {max_rsi}, actual {rsi}')
    return resultado_filtro


def filtro_ema_rapida_lenta(ind:Indicadores,log:Logger,escala,rapida,lenta,diferencia):
    filtro_ok,dif,pl,pr = ind.ema_rapida_mayor_lenta2( escala, rapida,lenta,diferencia_porcentual_minima=0.09 ) 
    log.log(f'    {escala} diferencia% {dif}, pend rapida {pr} pend lenta {pl}')
    log.log(f'{filtro_ok} <--ok_filtro_ema_rapida_lenta: {filtro_ok}')
    return filtro_ok    

