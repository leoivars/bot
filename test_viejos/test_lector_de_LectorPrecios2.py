from binance.client import Client # Cliente python para acceso al exchangue
from LectorPrecios2 import *
from indicadores2 import *
from logger import *
import time
import pws

client = Client(pws.api_key, pws.api_secret)

log=Logger('lector_precios2.log') 


lector=LectorPrecios(client)

precios=lector.leerprecios()
lista=[]
for p in precios:
    if p['symbol'].endswith('BTC'): # si la moneda es contra btc
        #print (p)
        try:
            i=Indicadores(p['symbol'],log)
            rsi= i.rsi('1d')
            adx= i.adx('1d')[0]
            #print (p['symbol'],p['price'] , rsi , adx )
            lista.append([p['symbol'],p['price'] , rsi , adx])

        except Exception as e:
                print ( e )
                print ( p['symbol'],"Error al calcular indicadores" )

#print('****** TODOS')
#for l in lista:
#    print (l)
        

print('*******30 a 35')
for l in lista:
    if l[2]>=30 and l[2]<=35:
        print(l[0],l[1],l[2],l[3])  

print('****** menores a 30')
for l in lista:
    
    if l[2]<30:
        print(l[0],l[1],l[2],l[3])





        

   
        
