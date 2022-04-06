from asyncio.log import logger
from indicadores2 import Indicadores
from mercado import Mercado
from logger import Logger
from time import time
from variables_globales import Global_State
from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB
import time
from fpar.filtros import filtro_parte_baja_rango,filtro_xvolumen_de_impulso


def habilitar_deshabilitar_pares(g:Global_State,db:Acceso_DB,mercado,log):
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

def habilitar_deshabilitar_pares_periodicamente(g:Global_State,conn:Conexion_DB,mercado):
    log = Logger('habilitar_deshabilitar.log')
    fxdb=Acceso_DB_Funciones(log,conn.pool)        
    db = Acceso_DB(log,fxdb)   
    while g.trabajando:
        habilitar_deshabilitar_pares(g,db,mercado,log)
        time.sleep(300)     

def habilitar_pares(g:Global_State,db:Acceso_DB,mercado:Mercado,log:Logger,pares_con_trades):
    pares=db.get_habilitables()
    c_habilitados=pares_con_trades
    for p in pares:
        moneda = p['moneda']
        moneda_contra = p['moneda_contra']
        par = moneda + moneda_contra
        log.log(f'{par}:')
        ind:Indicadores = Indicadores(par,log,g,mercado)
        
        actualizar_volumen_precio(moneda,moneda_contra,ind,db)          # ya que estamos actualizamos volumen y precio
        
        if hay_parte_baja_y_volumen_impulso(ind,log,g,'1h',33):            #habilito pares en la parte baja del rango
            db.habilitar(1,moneda,moneda_contra)
            c_habilitados += 1
            log.log(f'{par} habilitando total {c_habilitados}') 
        else:            
            mercado.desuscribir_todas_las_escalas(par)                  #solo desuscribo cuando no habilito, para recuperar recursos
                                                                            
        time.sleep(30)
        if c_habilitados  >= g.max_pares_activos_config:
            break

def actualizar_volumen_precio(moneda,moneda_contra,ind:Indicadores,db:Acceso_DB):
    px = ind.precio_mas_actualizado()
    vol = ind.volumen_suma('1d',15)
    db.par_persistir_volumen_precio(moneda,moneda_contra,vol,px)

def hay_precios_minimos_como_para_habilitar(ind:Indicadores,g:Global_State,log):
        ret = True
        escalas=['1d','4h'] 
        for e in escalas:
            if not filtro_parte_baja_rango(ind,log,e,120,0.2):
                ret = False
                break
        return ret  

def hay_parte_baja_y_volumen_impulso(ind:Indicadores,log: Logger,g:Global_State,escala,p_xmin_impulso=26):
    ret = False
    escala_sup=g.zoom_out(escala,2)
    if filtro_parte_baja_rango(ind,log,escala_sup,200,.382):
        if filtro_parte_baja_rango(ind,log,escala,200,.382):  
            if filtro_xvolumen_de_impulso(ind,log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):
                ret = True
    return ret

def precio_cerca(pxmin,precio,porcentaje=0.30):
    return precio < pxmin   or  (precio - pxmin) / precio *100 < porcentaje       






