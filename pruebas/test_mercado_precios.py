import sys
sys.path.append('..')  

from logger import Logger
import time
from pws import Pws
from binance.client import Client #para el cliente
from variables_globales import Global_State
from mercado import Mercado

pws=Pws()
client = Client(pws.api_key, pws.api_secret)
log=Logger('Test_mercado_precios.log')


globales = Global_State()

m = Mercado(log,globales,client)


i = 90


while  i >=0:

    print( m.valor_usdt(1,'BTCUSDT')  )

    time.sleep(1)
    i -=1


m.detener_sockets()











