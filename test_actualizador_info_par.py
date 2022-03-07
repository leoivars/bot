# # -*- coding: UTF-8 -*-
import sys
import time
import datetime
from binance.client import Client #para el cliente

from logger import *
from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB
from indicadores2 import Indicadores
from ordenes_binance import OrdenesExchange
from actualizador_info_par import ActualizadorInfoPar
import pws


log=Logger('test_actualizador_info_par.log') 
client = Client(pws.api_key, pws.api_secret,{ "timeout": 20})
oe=OrdenesExchange(client,log)

conn=Conexion_DB(log)                          
fxdb=Acceso_DB_Funciones(log,conn.pool)        
db = Acceso_DB(log,fxdb)  




moneda='BTC'
moneda_contra='USDT'
ind= Indicadores(moneda+moneda_contra,log)     

actualizador = ActualizadorInfoPar(conn,oe )
actualizador.actualizar_info(ind,escala,moneda,moneda_contra)
