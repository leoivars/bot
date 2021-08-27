from binance.client import Client # Cliente python para acceso al exchangue
from LectorPrecios2 import *
from indicadores2 import *
from logger import *

import time
import pws

client = Client(pws.api_key, pws.api_secret)

log=Logger('buscar_mercados3.log') 
#logrsi=Logger('oportunidades.log') 

lector=LectorPrecios(client)
precios=lector.leerprecios()


paresinutiles=[
    'BCCBTC','HSRBTC','ICNBTC','VENBTC','TRIGBTC','CHATBTC','BCNBTC','PAXBTC',
    'USDCBTC','RPXBTC','MODBTC','SALTBTC','SUBBTC','WINGSBTC','CLOAKBTC','TUSDBTC',
    'BCHSVBTC'
    ]

def buscar(escala):
    lista=[]
    for p in precios:
        if p['symbol'].endswith('BTC') and not p['symbol'] in paresinutiles: # si la moneda es contra btc
            #print (p)
            try:
                i=Indicadores(p['symbol'],log)
                adx= i.adx(escala)
                rsi= round(i.rsi(escala),2)
                macd=i.macd(escala)
                if rsi!=rsi: # es nan! lo transformo en 0. Como voy a ordenar la lista por este valor, si tengo valores nan el ordenamiento no funciona
                   rsi=0
                if adx[0] >= 23 and macd[1]>macd[0] and macd[2]>0:
                    lista.append([p['symbol'],p['price'] , rsi , adx])

            except Exception as e:
                print ( e )
                print ( p['symbol'],"Error al calcular indicadores" )
    
    #ordenar por rsi
    lista.sort(key=lambda e: e[2],reverse= True)

    cuenta=len(lista)
    for e in lista:
        log.log(e[0],e[2],e[3])
        

    log.log (escala,'encontrados=',cuenta)

buscar('1h')
buscar('4h')
buscar('1d')

        

   
        
