from binance.client import Client # Cliente python para acceso al exchangue
from LectorPrecios import *
from indicadores2 import *
from logger import *
import time
import pws

client = Client(pws.api_key, pws.api_secret)

log=Logger('test_lector_precios.log') 


lector=LectorPrecios(client)

precios=lector.leerprecios()


print ( )



print (lector.conveunidades_posibles(10,'USDT','BTC') )



        

   
        
