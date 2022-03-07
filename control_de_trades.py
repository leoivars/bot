import sqlite3
from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB
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


log=Logger('control_de_trades.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)


conn=Conexion_DB(log)                          
fxdb=Acceso_DB_Funciones(log,conn.pool)        
db = Acceso_DB(log,fxdb)     

estado_general=VariablesEstado()

oe=OrdenesExchange(client,'BTCUSDT',log,estado_general)


parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"            , help="Moneda")
parser.add_argument("-q",   "--cantidad"          , help="Filtro de Cantidad")
args = parser.parse_args()



def decimales(x):
    sx=str(x)
    try:
        dec=len(sx)-sx.index('.')-1
    except:
        dec=0
    
    return dec        



#print ('Candidad            BTC ',oe.tomar_cantidad('BTC')    

#monedas de pares en las que no tengo hay trade alguno
# sql=''' select moneda from pares where moneda not in (
#             SELECT moneda as total 
#             from trades where ejecutado=0 
#             group by moneda) and habilitable=1
#         group by moneda '''


def print_order(o):
    print( o )
    print('time:', strtime_a_fecha(  o['time']), 'price:', o['price'],'origQty:', o['origQty'],'executedQty:', o['executedQty'] ,'id:', o['orderId'],'status:', o['status'],'type:', o['type'],'side',o['side'])



moneda=args.moneda
if moneda==None:
    sql="select moneda, count(1) as cantidad  from pares where moneda is not null and moneda not in ('EDO','BTC','BNB') group by moneda "
    monedas = db.ejecutar_sql_ret_cursor(sql)
else:
    monedas = [(moneda,1)]

filtro_cantidad=args.cantidad
if filtro_cantidad==None:
    filtro_cantidad = 0
else:
    filtro_cantidad = float(filtro_cantidad)


def mostrar_ordenes(par,filtro_cantidad):
    print('Trades--->',par)
    for orden in oe.consultar_ordenes(par,500):
        if float(orden['executedQty']) >0 and ( float(orden['executedQty']) == filtro_cantidad  or filtro_cantidad == 0   ): 
            print_order(orden)

def mostrar_ordenes20(par):
    print('Trades--->',par)
    for orden in oe.consultar_ordenes(par,20):
        print_order(orden)            





for r in monedas:
    m = r[0]
    #print('Moneda:-->',m,'<--')
    cant=oe.tomar_cantidad(m)
    

    dec=decimales(cant)
    tot=round(  db.total_moneda_en_trades(m) ,dec)
    
    if cant > 0: 
        if not math.isclose(cant,tot):
            
            if moneda!=None:
                for contra in ['BTC','USDT']:
                    par=(m+contra).upper()
                    mostrar_ordenes(par,filtro_cantidad)

            print('---->',m,cant,'en trades-->',tot,'cant-tot=',cant-tot)              
                    
            
    else:
        for contra in ['BTC','USDT']:
            trade=db.get_trade_menor_precio(m,contra)
            if trade['idtrade'] !=-1:
                print('---->',m,'=0 pero hay trades registrados') 
                par=(m+contra).upper()
                mostrar_ordenes(par,filtro_cantidad)


#if moneda !=None:
#    m=moneda.upper()
#    mostrar_ordenes20(m+'BTC')
#    mostrar_ordenes20(m+'USDT')
    
    

              
        
          

            




