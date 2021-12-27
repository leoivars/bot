from os import error
from binance.client import Client
from variables_globales import VariablesEstado
from logger import Logger
import time
from fauto_compra_vende.materializar_pares import eliminar_pares_muertos

def crear_cliente(pws,log:Logger):
    client = None
    #si no puedo crear el ciente, no puedo hacer nada por lo tanto. Espero hasta que se pueda.
    while True:              
        try:
            client = Client(pws.api_key, pws.api_secret,{ "timeout": 30})
            break
        except Exception as ex:
            strerror=str(ex)
            if 'failure in name resolution' in strerror:
                log.err('Error crear_cliente sin internet')
                t=150
            else:    
                log.err('Error crear_cliente:' + strerror)
                t=30
    return client

def esperar_correcto_funcionamiento(client:Client,e:VariablesEstado,log:Logger):
    # esperamos el corremto funcionamiento del sistema
    errores=0
    while True:
        try:
            if client.get_system_status() ['status']==0:
                print('Sistema OK. Comenzamos!')
                e.se_puede_operar = True 
                break
            else:
                log.err('Sistema en mantenimiento...')
                t=300
                e.se_puede_operar = False
        except Exception as ex:
            errores +=1
            strerror=str(ex)
            t=150
            if 'failure in name resolution' in strerror:
                log.err('Error client.get_system_status sin internet')
            else:    
                log.err('Error client.get_system_status:' + strerror)
                
            if errores >12:  
                e.se_puede_operar = False               #30 minutos (150 * 12) con errores, fuerzo la salida
                e.trabajando = False
                break
        time.sleep(t)

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

    eliminar_pares_muertos(e)    
    
    log.log('todos muertos!')        

