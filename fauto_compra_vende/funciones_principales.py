from binance.client import Client
from variables_globales import VariablesEstado
from logger import Logger
from time import time
from datetime import datetime

def crear_cliente(pws):
    client = None
    while True:
        try:
            #client = Client(pws.api_key, pws.api_secret,{ "timeout": 15})
            client = Client(pws.api_key, pws.api_secret,{ "timeout": 30})
            break
        except Exception as e:
            print('no se puede crear cliente')
            print( str(e) )
            time.sleep(30)
    
    return client

def esperar_correcto_funcionamiento(client:Client,e:VariablesEstado,log:Logger):
    # esperamos el corremto funcionamiento del systema
    
    while True:
        log.log( 'esperar_correcto_funcionamiento' )
        try:
            if client.get_system_status() ['status']==0:
                print('Sistema OK. Comenzamos!')
                e.se_puede_operar = True
                break
            else:
                print('Sistema en mantenimiento...')
                t=300
                e.se_puede_operar = False
        except:
            print('no responde client.get_system_status()...')
            t=10

        time.sleep(t)
    e.se_puede_operar = True
    log.log( 'todo ok, se puede operar' )    

def controlar_estado0(e:VariablesEstado,log:Logger):
     # detener inactivos
    for k in e.pares_control.keys():
        if e.pares[k][0].estado==0:
            log.log('######---OJO---######',k,'E.0')        

def esperar_a_que_todos_mueran(e:VariablesEstado,log:Logger):
     # detener inactivos
    alguno_vivo = True 
    c=300 
    while alguno_vivo and c>0:
        #log.log('Esperando para salir',c)
        alguno_vivo = False
        for k in e.pares_control.keys():
            if e.pares[k][0].estoy_vivo:
                log.log(k,'Vivo')
                alguno_vivo = True
                break
        time.sleep(1)
        c-=1
    
    #declaro muerto lo que exista
    lista_pares=e.pares_control.keys()
    for k in lista_pares:
        e.pares[k][0].estoy_vivo = False

    eliminar_pares_muertos()    
    
    log.log('todos muertos!')        

