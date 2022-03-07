# # -*- coding: UTF-8 -*-

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
parser.add_argument("-c",   "--contra"     , help="Moneda Contra")
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
    print('time:', strtime_a_fecha(  o['time']), 'price:', o['price'],'origQty:', o['origQty'],'executedQty:', o['executedQty'] ,'id:', o['orderId'],'status:', o['status'],'type:', o['type'],'side',o['side'])

def mostrar_ordenes(par):
    print('Trades--->',par)
    for orden in oe.consultar_ordenes(par):
        if float(orden['executedQty']) >0: 
            print_order(orden)


moneda        = args.moneda
moneda_contra = args.contra

if moneda==None or moneda_contra == None:
    print ('hace falta moneda y moneda contra')
    exit()


moneda=moneda.upper()
moneda_contra=moneda_contra.upper()
par     = moneda+moneda_contra

print( moneda,moneda_contra,par)

trade=db.get_trade_menor_precio(moneda,moneda_contra)

if trade['cantidad'] != -1:
    ordenes = oe.consultar_ordenes(par)

    ultima = len(ordenes)-1
    i=ultima

    while i>=0:
        orden= ordenes[i]
        print(trade['cantidad'],float(orden['origQty']))
        if trade['cantidad']==float(orden['origQty']):
            break
        i-=1

    if i == -1: # no encontro nada
        orden= ordenes[ultima]

    print(trade)
    print_order(orden)

    respuesta='??'
    print('cantidad' ,trade['cantidad'], float(orden['origQty'])   )
    print('ejecutado',trade['ejecutado'], float(orden['executedQty'])  )

    #print('cantidad',trade['cantidad'], 'origQty', orden['origQty'],'executedQty', orden['executedQty'],'ejecutado',  trade['ejecutado'] )
    if trade['cantidad']==float(orden['origQty']) and trade['cantidad'] - trade['ejecutado'] >= float(orden['executedQty']):
        print('Cantidades OK ' )
        if ( orden['status']=='FILLED' or (orden['status']=='CANCELED' and float(orden['executedQty']) >0 )  ) and  orden['side']=='SELL' :
            print('Orde de venta OK')
            respuesta = input("Cerramos el Trade la Orden? ")
            print(respuesta)

    if respuesta.upper()=='SI':
        print('actualizado...')
        db.trade_sumar_ejecutado(trade['idtrade'],float(orden['executedQty']),float(orden['price']),strtime_a_fecha(orden['time']),orden['orderId'])
        print('listo.')
else:
    print("no hay trades abierto")






