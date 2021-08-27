# # -*- coding: UTF-8 -*-
import sys
import os
from par_arbitraje import Par_arbitraje
from datetime import datetime, timedelta
import time
from binance.client import Client #para el cliente
import _thread
import threading
import json
from pws import Pws
from indicadores2 import Indicadores
from logger import *
from ordenes_binance import OrdenesExchange

from controlador_de_tiempo import Controlador_De_Tiempo
from correo import Correo
from reporte_estado import ReporteEstado


from funciones_utiles import memoria_consumida,cpu_utilizada,calc_tiempo
from twisted.internet import reactor

#import tracemalloc
import types
#import mem_top
#import traceback

#tracemalloc.start()

# import logging 
# logging.basicConfig(filename='./logs/auto_compra_vende.log',level=logging.DEBUG)


class VariablesEstado:
    # variables globales
    fee = 0.001
    se_puede_operar = False
    log_level = 2
    trabajando = True
    






pws=Pws()
log=Logger('auto_compra_vende.log') 
 
c=True
while c:
    try:
        #client = Client(pws.api_key, pws.api_secret,{ "timeout": 15})
        client = Client(pws.api_key, pws.api_secret)
        c=False
    except Exception as e:
        print('no se puede crear cliente')
        print( str(e) )
        print (time.time())
        time.sleep(30)

def cargar_config_json():
    with open('config.json','r') as f:
        try:
            config = json.load(f)
        except:
            config = None   
        f.close() 
    return config    


def set_log_levels():
    try: 
        config = cargar_config_json()
        ll = int(config[0]['log_level'])
    except:
        ll = 2
    e.log_level = ll       
    log.set_log_level(ll)
    
            
    
e = VariablesEstado()
cargar_config_json()


nuevo_par=Par_arbitraje(client,'USDT','DAI',e,50,3,3)  
nuevo_par.set_log_level(e.log_level)


_thread.start_new_thread(nuevo_par,())
            
