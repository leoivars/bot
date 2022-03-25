# # -*- coding: UTF-8 -*-
import sys
import time
from par import *
from datetime import datetime
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
import _thread
import json
#import sqlite3
from logger import *
from no_se_usa.acceso_db import *
from ordenes_binance import OrdenesExchange
from pws import Pws
from variables_globales import Global_State
#import tracemalloc
import gc
#import mem_top
#import traceback


# import logging 
# logging.basicConfig(filename='./logs/auto_compra_vende.log',level=logging.DEBUG)
pws=Pws()

log=Logger('test_ordenes_binance.log') 

client = Client(pws.api_key, pws.api_secret,{ "timeout": 20})
e = Global_State()

oe0=OrdenesExchange(client,'PNTBTC',log,e)

print( oe0.tomar_cantidad_disponible('USDT') )
