from binance.client import Client # Cliente python para acceso al exchangue
from LectorPrecios2 import *
from indicadores2 import *
from logger import *
import traceback

import time
import pws

client = Client(pws.api_key, pws.api_secret)

log=Logger('buscar_mercados2.log') 
logrsi=Logger('mercado_rsi.log') 
logcompra=Logger('oportunidades_compra.log') 


lector=LectorPrecios(client)
precios=lector.leerprecios()


paresinutiles=[
    'BCCBTC','HSRBTC','ICNBTC','VENBTC','TRIGBTC','CHATBTC','BCNBTC','PAXBTC',
    'USDCBTC','RPXBTC','MODBTC','SALTBTC','SUBBTC','WINGSBTC','CLOAKBTC','TUSDBTC',
    'BCHSVBTC'
    ]

def buscar(escala):
    lista=[]
    lista_oportunidades=[]
    for p in precios:
        if p['symbol'].endswith('BTC') and not p['symbol'] in paresinutiles: # si la moneda es contra btc
            #print (p)
            try:
                i=Indicadores(p['symbol'],log)
                adx= i.adx(escala)
                rsi= round(i.rsi(escala),2)
                
                if rsi!=rsi: # es nan! lo transformo en 0. Como voy a ordenar la lista por este valor, si tengo valores nan el ordenamiento no funciona
                   rsi=0
                
                lista.append([p['symbol'],p['price'] , rsi , adx])
                
                macd=i.macd_analisis(escala,5)
                bb=i.volumen_bueno5(escala,1.3)# volumen por encima de su ema 
                if adx[0] >= 23 and macd[0]==1 and macd[1]<1 or bb['resultado'] : #adx con fuerza y macd con señal de compra
                    lista_oportunidades.append([p['symbol'],p['price'] , rsi , adx, bb])


            except Exception as e:
                print ( e )
                print ( p['symbol'],"Error al calcular indicadores" )
                tb = traceback.format_exc()
                log.log( tb)
    
    #ordenar por rsi
    lista.sort(key=lambda e: e[2],reverse= True)

    cuenta=0
    rsi_sobreventa=0
    rsi_sobrecompra=0
    rsi_neutral=0
    for e in lista:
        rsi=e[2]
        
        if rsi>0:
            cuenta+=1
        
        if rsi>0 and rsi<30:
            rsi_sobreventa+=1
        elif rsi>=30 and rsi<=60:
            rsi_neutral+=1
        else: #rsi>60:
           rsi_sobrecompra+=1

        log.log(e[0],e[2],e[3])  

    logrsi.log (escala,cuenta,'sv',rsi_sobreventa,'ne',rsi_neutral,'sc',rsi_sobrecompra)
    
    #oportunidades
    cuenta=len(lista_oportunidades)
    for e in lista_oportunidades:
        logcompra.log(e[0],e[2],e[3],e[4])
    
    logcompra.log (escala,'encontrados=',cuenta)    

buscar('15m')
buscar('1h')
buscar('4h')
buscar('1d')

        

   
        
