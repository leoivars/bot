# # -*- coding: UTF-8 -*-
import os
import sys
from pathlib import Path
sys.path.append(str(Path('..').absolute().parent))          #para que se pueda usar app. como mudulo
sys.path.append(str(Path('..').absolute().parent)+"/app")   #para que los modulos dentro de app encuentren a otros modulos dentro de su mismo directorio

print ('------------------getcwd()----->', os.getcwd())
print ('----------------__file__------->', __file__)
print ('---------------DIR_LOGS-------->', os.getenv('DIR_LOGS', '????'))
print ('---------------CONFIG_FILE----->', os.getenv('CONFIG_FILE', '????'))

from datetime import datetime
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
from app.logger import  Logger
from app.ordenes_binance import OrdenesExchange
from app.pws import Pws
from app.variables_globales import Global_State

pws=Pws()

log=Logger('test_ordenes_binance.log') 

client = Client(pws.api_key, pws.api_secret,{ "timeout": 20})
e = Global_State()

oe0=OrdenesExchange(client,'ETHUSDT',log,e)
oe1=OrdenesExchange(client,'BTCUSDT',log,e)
print( oe0.cantidad_disponible('USDT') )
print( oe1.cantidad_disponible('USDT') )

log.log('Fin')
