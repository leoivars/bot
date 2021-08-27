# # -*- coding: UTF-8 -*-
import sys
import time
from par import *
import datetime
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
import _thread
import json
#import sqlite3
from logger import *
from acceso_db import *
from acceso_db_conexion import *
from pws import Pws
from variables_globales import  VariablesEstado
from pool_indicadores import Pool_Indicadores
#import tracemalloc
import gc
#import mem_top
#import traceback

from bot_api import *


pws=Pws()

log=Logger('test_bot_api.log') 

#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

e=VariablesEstado()

bapi = BotApi(log,db,e)

bapi.run()

