import sqlite3
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from logger import *
from datetime import *
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from ordenes_binance import OrdenesExchange
import argparse
import math
from variables_globales import  VariablesEstado
from funciones_utiles import strtime_a_fecha,format_valor_truncando



log=Logger('control_de_trades.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)





#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

estado_general=VariablesEstado()

oe=OrdenesExchange(client,'BTCUSDT',log,estado_general)


parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"     , help="Moneda")
parser.add_argument("-c",   "--contra"     , help="Moneda Contra")
parser.add_argument("-t",   "--trades"     , help="Numero entero: trades a promediar desde el ultimo")
args = parser.parse_args()



def decimales(x):
    sx=str(x)
    try:
        dec=len(sx)-sx.index('.')-1
    except:
        dec=0
    
    return dec        



moneda        = args.moneda
moneda_contra = args.contra
ntrades        = args.trades

if moneda==None or moneda_contra == None:
    print ('hace falta moneda y moneda contra')
    exit()


moneda=moneda.upper()
moneda_contra=moneda_contra.upper()
par     = moneda+moneda_contra

print( moneda,moneda_contra,par)

sql ='''SELECT idtrade,cantidad,precio,fecha,ganancia_infima,ganancia_segura,tomar_perdidas,escala,senial_entrada,ejecutado 
        from trades where moneda='%s' and moneda_contra='%s' and ejecutado=0  
        order by precio''' % (moneda,moneda_contra)

if ntrades != None:
    ntrades = int(ntrades)
    sql = sql + ' limit '+str(ntrades) 

trades=db.ejecutar_sql_ret_dict(sql)

suma=0
cant=0


for t in trades:
    suma += t['precio'] * t['cantidad']
    cant += t['cantidad']

print ('Suma=%s Cantidad= %s Promedio=%s trades=%s' % (suma,cant, format_valor_truncando(suma/cant,9),len(trades) )   )