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
from variables_globales import  VariablesEstado
from funciones_utiles import strtime_a_fecha


log=Logger('analizar_trades_cerrados.log') 

pws=Pws()

intentos = 10
while intentos >=0:
    try:
        client = Client(pws.api_key, pws.api_secret)
        break
    except Exception as e:
        time.sleep(60)
    intentos -=1



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


def calcular_fecha_futura(fecha,minutos_al_futuro):
    fecha_futura = fecha + timedelta(minutes = minutos_al_futuro)
    return  fecha_futura  

def  px_par_fecha(fecha = None, par='BTCUSDT'):

    klines=[]
    intentos=5
    while len(klines)==0 and intentos >0:
        try:
            if fecha != None:
                sfecha=str(fecha)
                sfutur=str( calcular_fecha_futura(fecha,5)  )
                klines = client.get_historical_klines(par, Client.KLINE_INTERVAL_1MINUTE, sfecha,sfutur  )
            else:
                klines = client.get_historical_klines(par, Client.KLINE_INTERVAL_1MINUTE, '1 minute ago UTC'  )
        except Exception as e:    
            txt_error = str(e)
            print(txt_error)
            #error de límite de uso alcanzado
            if 'APIError(code=-1003)' in txt_error:
                time.sleep(60)
        intentos -=1          

    if len(klines)==0:
        print('error')
        return 0
    else:    
        return float(klines[0][4]) #precio close

def decimales(x):
    sx=str(x)
    try:
        dec=len(sx)-sx.index('.')-1
    except:
        dec=0
    
    return dec        
    
def print_trade(trade):
    
    print(trade['moneda'],trade['moneda_contra'],trade['fecha'],trade['cantidad'],trade['precio'],trade['senial_entrada'])
        
    if trade['moneda_contra']=='BTC':
        valorbtc_antes = trade['cantidad'] * trade['precio']

        precio_ahora = px_par_fecha(None,trade['moneda']+trade['moneda_contra'])  

        valorbtc_ahora = trade['cantidad'] * precio_ahora

        print( "Valor en btc antes",valorbtc_antes)
        print( "Valor en btc ahora",valorbtc_ahora)

        btc_antes = px_par_fecha(trade['fecha'])  

        btc_ahora = px_par_fecha() 

        valor_antes = valorbtc_antes * btc_antes
        valor_ahora = valorbtc_ahora * btc_ahora

    elif trade['moneda_contra']=='USDT':
        valor_antes = trade['cantidad'] * trade['precio']
        precio_ahora = px_par_fecha(None,trade['moneda']+trade['moneda_contra'])  
        valor_ahora = trade['cantidad'] * precio_ahora

    print( "Valor antes_usdt",valor_antes)
    print( "Valor ahora_usdt",valor_ahora)

    print('--------------------------------------------------------------------------------------------')    
    return valor_antes,valor_ahora

def get_trades(moneda):
    sql = '''  select cantidad,precio, moneda,moneda_contra,fecha,senial_entrada, analisis 
    from trades where ejecutado =0
    and moneda = %s 
    order by fecha desc
    '''
#     trades = db.ejecutar_sql_ret_dict(sql,(moneda_contra,top,))
# else:
#     sql = '''  select cantidad,precio, moneda,moneda_contra,fecha, senial_entrada, analisis 
#     from trades where ejecutado =0 and  moneda =%s
#     and analisis is not null
#     and moneda_contra = %s 
#     order by fecha desc 
#     limit %s
#     '''
    return db.ejecutar_sql_ret_dict(sql,(moneda,))

def get_monedas():
    sql='''select moneda from trades  where ejecutado=0
           group by moneda'''
    return db.ejecutar_sql_ret_dict(sql)       

for m in get_monedas():
    moneda = m['moneda']

    tvalor_antes=0
    tvalor_ahora=0

    for t in get_trades(moneda):
        antes,ahora = print_trade(t)
        tvalor_antes += antes
        tvalor_ahora += ahora

    if tvalor_antes < tvalor_ahora:
        g='+++'
    else: 
        g='   '    
    print (g+'TOTAL %s: antes = %s, ahora =%s' % (moneda,tvalor_antes,tvalor_ahora)    )
    

