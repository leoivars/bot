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
                 ,'DOGE','FTT','QTUM','ALGO','DCR'  ,'LSK'  ]

#pares=['LSKBTC','PIVXBTC','CELRBTC','EDOBTC']

#pares=['ETHBTC','EDOBTC','ATOMBTC']

monedas_ahora =['AION','DCR','SNT','TNT','HBAR','BTG','ADA','NKN']
pares=['BTCUSDT']
for m in monedas_ahora:
    pares.append(m+'BTC')

ganancia_segura=10


volumenes = []

for par in (pares):
    #par =mon+'BTC'
    prop=Par_Propiedades(par,client,log)

    ind=Indicadores(par,log)
    
    rango_actual,prango,velas =ind.rango('15m',3)
    print ('rango 15',par, rango_actual,prango,velas)  


    print (par)
    if ind.ema_rapida_mayor_lenta('4h',10,55):
        if velas > 9:# hay rango 
            macd = ind.macd_analisis('4h',velas)
            print ('rango',par, rango_actual,prango,velas,macd)    
            


    #p= round( ad / px * 100 ,2)

    
    
    

    



    
                
   

   