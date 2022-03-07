# # -*- coding: UTF-8 -*-
from no_se_usa.acceso_db import *
from acceso_db_conexion import *
from pws import Pws
from logger import *
from binance.client import Client




def cargarlista(tickers):
    pares={}
    for t in (tickers):
        if t['symbol'].endswith("BTC") or t['symbol'].endswith("USDT"):
            pares[ t['symbol']]= float( t['quoteVolume'] )
    return pares


pws= Pws()
log=Logger('mercados.log') 
conn=Conexion_DB(log)
db=Acceso_DB(log,conn.pool)
client = Client(pws.api_key, pws.api_secret)

monedas_contra=['BTC']


tickers = client.get_ticker()


sql='INSERT INTO criptomonedas (idcripto)'
sql+='values (%s)'

for t in tickers:
    moneda_contra=''
    moneda=''
    precio= float(t['lastPrice'])
    porcentaje_cambio_precio=  float(t['priceChangePercent'])      
    for m in monedas_contra:
        lm=len(m)
        s=t['symbol']
        if s.endswith(m):
            moneda=str(s[:len(s)-lm])
            moneda_contra=m
            print (moneda) 
            db.ejecutar_sql(sql,(moneda,))
            #cursor.execute(sql,(moneda, moneda_contra,'comprar','dinamico',precio,0,1, 1.9, precio , porcentaje_cambio_precio, 0))

            break

        
           




