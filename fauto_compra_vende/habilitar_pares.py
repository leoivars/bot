from indicadores2 import Indicadores
from mercado import Mercado
from logger import Logger
from time import time
from variables_globales import VariablesEstado
from acceso_db import Acceso_DB
import time

def habilitar_deshabilitar_pares(g:VariablesEstado,db:Acceso_DB,mercado,log):
    ''' Controla la cantidad de pares que tienen trades en este momento y lo compara con 
        g.maxima_cantidad_de_pares_con_trades que establece la cantidad máxima de pares con trades. 
        Si la cantidad es menor, habilita todos pares que sean habilitable (habilitable=1 en la tabla pares).
        El objetivo es mantener todos los paras habilitados hasta lograr un máximo de pares con trades. Una vez que se logra,
        solo quedarán habilitados los pares con trades.
    '''
    pares_con_trades = db.trades_cantidad_de_pares_con_trades()
    if pares_con_trades  < g.maxima_cantidad_de_pares_con_trades:
        if db.get_count_habilitados() < g.max_pares_activos_config:
            habilitar_pares(g,db,mercado,log,pares_con_trades) 
    #else:
    #    db.deshabilitar_pares_sin_trades()

def habilitar_deshabilitar_pares_periodicamente(g:VariablesEstado,conn,mercado):
    log = Logger('habilitar_deshabilitar.log')
    db:Acceso_DB = Acceso_DB(log,conn.pool)
    while g.trabajando:
        habilitar_deshabilitar_pares(g,db,mercado,log)
        time.sleep(300)     

def habilitar_pares(g:VariablesEstado,db:Acceso_DB,mercado:Mercado,log,pares_con_trades):
    pares=db.get_habilitables()
    c_habilitados=pares_con_trades
    for p in pares:
        moneda = p['moneda']
        moneda_contra = p['moneda_contra']
        par = moneda + moneda_contra
        log.log(f'{par}:')
        ind:Indicadores = Indicadores(par,log,g,mercado)
        
        actualizar_volumen_precio(moneda,moneda_contra,ind,db)          # ya que estamos actualizamos volumen y precio
        
        if hay_precios_minimos_como_para_habilitar(ind,g,log)  or\
            (el_precio_no_esta_cerca_del_maximo(ind,log) and  para_alcista_como_para_habilitar(ind,g,log) ):         #habilito pares con tendencia alcista que no esten cerca de su maximo 
            db.habilitar(1,moneda,moneda_contra)
            c_habilitados += 1
            log.log(f'{par} habilitando total {c_habilitados}') 
        else:            
            mercado.desuscribir_todas_las_escalas(par)                  #solo desuscribo cuando no habilito, para recuperar recursos
                                                                            
        time.sleep(30)
        if c_habilitados + pares_con_trades >= g.max_pares_activos_config:
            break

def actualizar_volumen_precio(moneda,moneda_contra,ind:Indicadores,db:Acceso_DB):
    px = ind.precio_mas_actualizado()
    vol = ind.volumen_suma('1d',15)
    db.par_persistir_volumen_precio(moneda,moneda_contra,vol,px)

def hay_precios_minimos_como_para_habilitar(ind:Indicadores,g:VariablesEstado,log):
        ret = True
        escalas=['1d','4h'] 
        for e in escalas:
            pxmin = ind.minimo_x_vol(e,75,3) 
            precio = ind.precio_mas_actualizado()
            px_cerca=precio_cerca(pxmin,precio,g.escala_entorno[e])
            log.log(f'{ind.par} min {pxmin} < {precio} px {px_cerca} ')

            if not px_cerca:
                ret =False
                break
        return ret  

def para_alcista_como_para_habilitar(ind:Indicadores,g:VariablesEstado,log): 
    if not ind.ema_rapida_mayor_lenta('4h',9,20,0.1):
        log.log(f'{ind.par} bajista 4h ')
        return False
    if hay_rsis_sobrevendidos(ind,log):
        return False
    else:
        return True    
        
def hay_rsis_sobrevendidos(ind:Indicadores,log): 
    ret = False
    escalas=['1d','4h'] 
    for e in escalas:
        rsi = ind.rsi(e)
        if rsi > 69.5:
            ret = True
            log.log(f'{ind.par} rsi {e} {rsi} sobrevendido')
    return ret

def el_precio_no_esta_cerca_del_maximo(ind:Indicadores,log):
    ret = False
    px_max=ind.maximo_x_vol('1d',300,5)     #300 dias hacia atrás para controlar el máximo
    px = ind.precio_mas_actualizado() 
    print (px_max,px)
    if px_max>0:
        pmaximo = px/px_max
        if pmaximo > 0.7:
            log.log(f'{ind.par} px {px} max {px_max} muy cerca {pmaximo} ')
        else:
            ret = True 

    return ret          


def precio_cerca(pxmin,precio,porcentaje=0.30):
    return precio < pxmin   or  (precio - pxmin) / precio *100 < porcentaje       






