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
from funciones_utiles import strtime_a_fecha


log=Logger('analizar_trades_cerrados.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)


#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

estado_general=VariablesEstado()




parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"            , help="Moneda")
parser.add_argument("-c",   "--moneda_contra"     , help="Moneda contra")
parser.add_argument("-t",   "--top"            , help="top n (las primeras n)")
args = parser.parse_args()


def decimales(x):
    sx=str(x)
    try:
        dec=len(sx)-sx.index('.')-1
    except:
        dec=0
    
    return dec        





    
def print_trade(trade):
    
    print(trade['moneda'],trade['moneda_contra'],trade['fecha'],'duracion:',trade['duracion'],'retultado:',trade['resultado'])
    for ana in trade['analisis'].split('~'):
        print(ana)
    print('--------------------------------------------------------------------------------------------')    


top=args.top
if top==None:
    top=100
else:
    top=int(top)        

moneda_contra=args.moneda_contra
if moneda_contra==None:
    moneda_contra='BTC'
else:
    moneda_contra=moneda_contra.upper()


moneda=args.moneda
if moneda==None:
    sql = '''  select moneda,moneda_contra,fecha,datediff(ejec_fecha,fecha)  as duracion ,
    round(ejec_precio*ejecutado - precio*cantidad - ejec_precio*ejecutado*0.001 - precio*cantidad*0.001 ,8) as resultado,
    analisis
    from trades where cantidad=ejecutado 
    and analisis is not null
    and moneda_contra = %s 
    order by resultado desc  
    limit %s
    '''
    trades = db.ejecutar_sql_ret_dict(sql,(moneda_contra,top,))
else:
    sql = '''  select  moneda,moneda_contra,fecha,datediff(ejec_fecha,fecha)  as duracion ,
    round(ejec_precio*ejecutado - precio*cantidad - ejec_precio*ejecutado*0.001 - precio*cantidad*0.001 ,8) as resultado,
    analisis
    from trades where cantidad=ejecutado and  moneda =%s
    and analisis is not null
    and moneda_contra = %s 
    order by resultado desc  
    limit %s
    '''
    trades = db.ejecutar_sql_ret_dict(sql,(moneda,moneda_contra,top))




for t in trades:
    print_trade(t)