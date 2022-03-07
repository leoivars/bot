import sqlite3
from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB
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

estado_general=VariablesEstado(p)

oe=OrdenesExchange(client,'BTCUSDT',log,estado_general)


parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"            , help="Moneda")
parser.add_argument("-c",   "--contra"     , help="Moneda Contra")
parser.add_argument("-i",   "--id"         , help="id de la operación en el exchange")
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

def tomar_orden_por_id(ordenes,id):
    ret = None
    for o in ordenes:
        #print('------------->',o['orderId'],id,type(o['orderId']),type(id))
        if o['orderId']==id:
            ret = o
            break
    return   ret 

def print_order(o):
    print('time:', strtime_a_fecha(  o['time']), 'price:', o['price'],'origQty:', o['origQty'],'executedQty:', o['executedQty'] ,'id:', o['orderId'],'status:', o['status'],'type:', o['type'],'side',o['side'])

def mostrar_ordenes(par):
    print('Trades--->',par)
    for orden in oe.consultar_ordenes(par):
        if float(orden['executedQty']) >0: 
            print_order(orden)



#{'symbol': 'NAVBTC', 'orderId': 49402668, 'orderListId': -1, 'clientOrderId': '7oLY4jaQvUdmyMsnqUVcgv', 'price': '0.00001305', 'origQty': '15.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'SELL', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1619169544819, 'updateTime': 1619169544819, 'isWorking': True, 'origQuoteOrderQty': '0.00000000'}

def motrar_ordenes_buy(ordenes):
    for orden in ordenes:
        if orden['side']=='BUY':
            print(orden['time'],'orderId',orden['orderId'],'origQty',orden['origQty'],'executedQty',orden['executedQty'],orden['status'])            


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


ordenes = oe.consultar_ordenes(par,50)

motrar_ordenes_buy(ordenes)

#encuentro la ultima orden que hizo algo.. la de id

id = args.id
if id == None:
    id = -1
else:
    id=int(id)    

print('id',id)

if id == -1:
    ultima = len(ordenes)-1
    executed=0
    while executed==0 and ultima>=0:
        orden= ordenes[ultima]
        executed = float(orden['executedQty'])
        ultima = ultima - 1
    print('ultima orden')
    print(orden) 
    print('-------------------------------------ultima')
    print_order(orden)  

else:
    orden=tomar_orden_por_id(ordenes,id)
    print('orden id',id)
    print(orden) 
    print('+++++++++++++++++++++++++++++++++++++  id...')
    print_order(orden)

print(trade)
print('----------------------------------------')

respuesta='??'

#print('cantidad',trade['cantidad'], 'origQty', orden['origQty'],'executedQty', orden['executedQty'],'ejecutado',  trade['ejecutado'] )
if ( orden['status']=='FILLED' or (orden['status']=='CANCELED' and float(orden['executedQty']) >0 )  ) and  orden['side']=='BUY' :
    print('OrdeN de Compra OK')
    respuesta = input("Ingresamos Compra? ")
    print(respuesta)

if respuesta.upper()=='SI':
    print('actualizado...')

    if orden['type'] == 'MARKET': # la ordek market no lleva precio, lo calculo a precio promedio asi:
        orden['price'] = float(orden['cummulativeQuoteQty']) / float(orden['executedQty'])


    db.trade_persistir(   moneda,moneda_contra,'1d','compra perdida',  float(orden['executedQty'])   ,float(orden['price']),0 ,5,10,-5,'', strtime_a_fecha(orden['time']), orden['orderId']  )

    print('listo.')

#{'symbol': 'IOTABTC', 'orderId': 159408534, 'orderListId': -1, 'clientOrderId': 'LxegY1fLCA51Sc4SFhgCmx', 
# 'price': '0.00003047', 'origQty': '7.00000000', 'executedQty': '7.00000000', 'cummulativeQuoteQty': '0.00021329', 
# 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 
# 'time': 1599019881913, 'updateTime': 1599019982072, 'isWorking': True, 'origQuoteOrderQty': '0.00000000'}
 



