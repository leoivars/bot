import sqlite3
from no_se_usa.acceso_db import Acceso_DB
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
from variables_globales import  Global_State
from funciones_utiles import strtime_a_fecha


log=Logger('trade_pendientes.log') 

pws=Pws()

#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

estado_general=Global_State()

parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"            , help="Moneda")
parser.add_argument("-c",   "--contra"     , help="Moneda Contra")
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

if moneda==None or moneda_contra == None:
    print ('hace falta moneda y moneda contra')
    exit()



sql="select * from trades where moneda='"+moneda+"' and moneda_contra='"+moneda_contra+"' and ejecutado<cantidad"


tmp = db.get_trade_menor_precio(moneda,moneda_contra)

#print ('trade menor precio',tmp)



trades = db.ejecutar_sql_ret_dict(sql)

#{'idtrade': 4089, 'fecha': datetime.datetime(2020, 9, 1, 8, 29, 2), 'moneda': 'MDT', 'moneda_contra': 'BTC', 
# 'senial_entrada': '1h decidir_comprar_como_jaime_scalping', 'escala': '1h', 'cantidad': 128.0, 'precio': 1.57e-06, 
# 'ganancia_infima': 10.29, 'ganancia_segura': 15.43, 'tomar_perdidas': -8.28, 'ejecutado': 0.0, 'ejec_precio': 0.0, 
# 'ejec_fecha': None, 'analisis': 'pendiente_positiva_ema 55: 4h True ~ 1d True ~ 1w False ~ EMA 10,55: 4h True ~ 1d True ~ 1w False ~ busca_macd_hist_min: 4h [246, 8, 1, 3.1150406188164347e-09, 26] ~ 1d [86, 2, 1, 1.4706554465009591e-08, 9] ~ 1w [-1, None, 0, None, 0] ~ RSI: 4h 67.7 ~ 1d 66.96 ~ 1w 50.0 ~ ADX: 4h [32.73, 1.87, 0.72, 0.78, 3.35] ~ 1d [36.81, 1.79, 1.93, -0.94, -0.1] ~ 1w [nan, nan, nan, nan, nan] ~ '}


def imprimir_analisis(analisis):
    try:
        for a in analisis.split('~'):
            print(a)
    except:
        print(analisis) 
        
def imprimir(trade):
    print (trade['idtrade'],trade['fecha'],trade['cantidad'],trade['precio'],trade['ganancia_infima'],trade['ganancia_segura'],trade['tomar_perdidas'])
    print (trade['senial_entrada'],trade['escala'])
    imprimir_analisis(trade['analisis'])
    print('-----------------------------------------------------------------------------------------')

for t in trades:
    imprimir(t)
