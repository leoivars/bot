
from par import Par
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from variables_globales import  VariablesEstado
from logger import Logger
import _thread
import time

import gc

def materializar_pares_desde_db(inico,log:Logger,conn,e:VariablesEstado,mercado,client):

    db = Acceso_DB(log,conn.pool)
    log.log('materializar_pares_desde_db.ini',inico)
    #poner_pares_control_en_falso, luego si está query pasa a verdadero
    for k in e.pares_control.keys():
        e.pares_control[k]=False

    log.log('get_cuenta_pares_activos...')
    pares_activos=db.get_cuenta_pares_activos()
    
    #if inico:
    #    dict_pares_activos=db.lista_de_pares_activos_con_trades()
    #else:    
    log.log('lista_de_pares_activos...')
    dict_pares_activos=db.lista_de_pares_activos()

    log.log('materializando...')
    
    for r in dict_pares_activos:
        par=str(r['moneda'].upper()+r['moneda_contra'].upper())
        #pongo en verdadero su variable de control para que pueda vivir.
        e.pares_control[par]=True   
        # creo el objeto si no está
        if not par in e.pares: 
        
            log.log(par,'lanzado',par,'Balance=',r['balance'])
            
            nuevo_par=Par(client,r['moneda'].upper(),r['moneda_contra'].upper(),conn,e,mercado)
            nuevo_par.set_log_level(e.log_level)
            
            # e.pares[par][0] es el obj par
            # e.pares[par][1] es el obj proceso
        
            e.pares[par]= [ nuevo_par, None ] #[par,proceso]
            _thread.start_new_thread(e.pares[par][0].trabajar,())
            #e.pares[par][1] = threading.Thread( target=e.pares[par][0].trabajar,args=() )   
            #e.pares[par][1].start()
            
            if inico: #realizo una pequeña demora para no meter tanta presion en el inicio
                time.sleep(.7)
            else:
                time.sleep(.5) 
            #mostrar_informacion()
        
    e.cant_pares_activos = pares_activos
    
   
    # detener inactivos 
    for k in e.pares_control.keys():
        if not e.pares_control[k]:
            log.log('XXXXX--> Detener:',k)
            e.pares[k][0].detener()
        else:
            e.pares[k][0].set_log_level(e.log_level)    

    eliminar_pares_muertos(e)       

def eliminar_pares_muertos(e):
    eliminar=[]
    #  detecto los pares muertos
    for k in e.pares.keys():
        if not e.pares[k][0].estoy_vivo:
            eliminar.append(k)  
            
    # ahora los elimino
    for k in (eliminar):
        del e.pares_control[k]
        e.pares[k][0]= None
        del e.pares[k] 

    if len(eliminar) > 0:
        gc.collect() # ha eliminadoun par, que tiene indicadores que tienen velas... quiero esa memoria de vuelta porque soy probre
