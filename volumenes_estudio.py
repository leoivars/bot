from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from numpy import isnan
from par_propiedades import Par_Propiedades
#import matplotlb.pyplot as plt

pws=Pws()

client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_indicadores.log') 



monedas=['MDA','BCPT','KEY','IOST','FUEL','FUN','SNT','QSP','']

primeras_monedas=['ETH','XRP','LTC','EOS','BNB','XTZ','LINK','ADA','XLM','XMR' \
                 ,'TRX','ETC','DASH','NEO','ATOM','IOTA','ZEC','XEM','ONT','BAT'\
                 ,'DOGE','FTT','QTUM','ALGO','DCR'  ,'LSK','EDO','MATIC'  ]

moneda_usdt=['BTC','ETH','LTC','BNB','EOS']                 

#pares=['LSKBTC','PIVXBTC','CELRBTC','EDOBTC']

pares=['ETHBTC','EDOBTC','ATOMBTC']

#pares=['ATOMBTC']
ganancia_segura=10


volumenes = []

for mon in (moneda_usdt):
    par =mon+'USDT'
    prop=Par_Propiedades(par,client,log)

    i=Indicadores(par,log)
    
    volumenes.append(  [ par , i.volumen_moneda_contra('1M') ]   )

    print (volumenes[-1]  )

promedios=[]
for p in volumenes:
    avg=p[1][0] + p[1][1] + p[1][2] + p[1][3]
    promedios.append([p[0],avg/4])

print('-------------------------------------------------')    

promedios.sort(key=lambda elem: elem[1])

vol_escala={'1M':1,'1w':1/4,'1d':1/30,'4h':(1/30)/24*4,'2h':(1/30)/24*2,'1h':(1/30)/24,'30m':((1/30)/24)/2,'15m':((1/30)/24)/4,'5m':((1/30)/24)/12,'1m':((1/30)/24)/60}

for a in promedios:
    print (a)


print('-------------------------------------------------')    
for a in promedios:
    #print (a)
    i=Indicadores(a[0],log)
    vp=i.volumen_proyectado_moneda_contra('1h')
    print(a, vp, a[1] * vol_escala['1h']   )
    


        
