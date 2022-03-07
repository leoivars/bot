from variables_globales import VariablesEstado
from logger import Logger
import time
from acceso_db_conexion import Conexion_DB
from pool_indicadores import Pool_Indicadores
from acceso_db_modelo import Acceso_DB
from actualizador_info_par import ActualizadorInfoPar
from binance.client import Client
from funciones_utiles import cpu_utilizada
from ordenes_binance import OrdenesExchange
#from Monitor_precios_ws import MonitorPreciosWs
from acceso_db_conexion import Conexion_DB
from indicadores2 import Indicadores


def actualizar_par(moneda,moneda_contra,g:VariablesEstado,IndPool:Pool_Indicadores,conn:Conexion_DB,client:Client,loglocal:Logger):
    par=moneda+moneda_contra
    oe=OrdenesExchange(client, par ,loglocal,g)
    actualizador = ActualizadorInfoPar(conn, oe ,loglocal)
    ind=IndPool.indicador(par)

    actualizador.actualizar_info(ind,'1d',moneda,moneda_contra)
    

def actualizar_info_pares_deshabilitados(g:VariablesEstado,IndPool:Pool_Indicadores,conn:Conexion_DB,client:Client):
    
    loglocal=Logger('actualizar_info_pares_deshabilitados.log')
    loglocal.set_log_level(g.log_level)
    db = Acceso_DB(loglocal,conn.pool)

    #empezamos 
    loglocal.log ("----INICIO----")
    inicio=time.time()

    dict_pares_habilitables=db.get_habilitables_todos()
    
    for r in dict_pares_habilitables:
        
        #retardo para no matar tanto al procesador
        cpu=cpu_utilizada()
        if  cpu > 50:
            time.sleep( 60 * cpu/100 )

        try:
            
            moneda=r['moneda']
            moneda_contra=r['moneda_contra']

            actualizar_par(moneda,moneda_contra,g,IndPool,conn,client,loglocal)
        except Exception as e:
            loglocal.log('Error',str(e))    

    return time.time() - inicio        # retorna el tiempo que se demoró

def actualizar_ranking_por_volumen_global(g:VariablesEstado,IndPool:Pool_Indicadores,conn:Conexion_DB,client:Client):
    indbtc:Indicadores=IndPool.indicador('BTCUSDT')
    pxbtc = indbtc.precio_mas_actualizado()
    loglocal=Logger('actualizar_ranking_por_volumen.log')
    db = Acceso_DB(loglocal,conn.pool)
    cursor_ranking = db.ranking_de_monedas_por_volumen(pxbtc)
    dict_ranking={}
    i=1
    for par in cursor_ranking:
        key_par = par[0] + par[1]
        dict_ranking[ key_par ] = i
        i += 1
    g.rankig_por_volumen = dict_ranking    



if __name__  == '__main__':
    #TEST
    from pws import Pws
    pws=Pws()
    client = Client(pws.api_key, pws.api_secret)
    #base de datos
    log = Logger('actualizar_info_pares_deshabilitados')
    conn=Conexion_DB(log)
    db=Acceso_DB(log,conn.pool)
    g = VariablesEstado()
    #web soket de monitor de precios
    mo_pre=MonitorPreciosWs(log)
    mo_pre.empezar()
    #pool de indicadores para pares lindos.
    logpool=Logger('pool_indicadores.log') 
    IndPool=Pool_Indicadores(logpool,mo_pre,g)

    actualizar_info_pares_deshabilitados(g,IndPool,db,client)


