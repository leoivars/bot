from par_propiedades import *
from logger import *
import time
import pws
from binance.client import Client

#import matplotlib.pyplot as plt

log=Logger('test_par_propiedades.log') 

client = Client(pws.api_key, pws.api_secret)

parprop=Par_Propiedades('NPXSBTC',client,log)



print('ticksize',parprop.tickSize)
print('min_notional',parprop.min_notional)
print('min_notional',parprop.moneda_precision)
print('--------------------------------')    
        
