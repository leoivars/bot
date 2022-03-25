from logger import Logger
import time
from pws import Pws
from binance.client import Client #para el cliente
from variables_globales import Global_State
from mercado import Mercado

pws=Pws()
#client = Client(pws.api_key, pws.api_secret)
log=Logger('Test_mercado.log')


#globales = Global_State()

par = 'BTCUSDT'
escala = '1m'

#escala  ={'1m':60 ,'5m': 300 ,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,'1w':604800,'1M':2419200}
#escala  ={'1m':60 ,'5m': 300 ,'15m':900}
#escala  ={'1m':60,'5m': 300,'15m':900}
#escala  ={'1m':60,'5m': 300}
escala  ={'1m':60}
#pares=['APPCBTC','NAVBTC','POWRBTC','POWRBTC','POWRBTC','GVTBTC','RCNBTC','BTCUSDT']
pares=['APPCBTC']

m = Mercado(log,'globales','client')

m.registrar_ws(1,'NAVBTC','5m')
m.registrar_ws(1,'POWRBTC','1m')
m.registrar_ws(1,'POWRBTC','5m')
m.registrar_ws(1,'BTCUSDT','5m')

print(m.par_escala_ws)

m.eliminar_ws('NAVBTC','5m')
m.eliminar_ws('POWRBTC','1m')
m.eliminar_ws('POWRBTC','5m')
m.eliminar_ws('BTCUSDT','5m')

print(m.par_escala_ws)