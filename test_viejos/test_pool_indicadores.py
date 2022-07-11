from pool_indicadores import Pool_Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from variables_globales import Global_State
import psutil
from Monitor_precios_ws import MonitorPreciosWs




#import matplotlb.pyplot as plt

pws=Pws()

client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_pooll_indicadores.log') 

pares=['EDOBTC','ZECBTC','LTCBTC','BTCUSDT']
e = Global_State()

#web soket de monitor de precios
mo_pre=MonitorPreciosWs('Test_pooll_indicadores.log')
mo_pre.empezar()


pind=Pool_Indicadores(log,mo_pre,e)







def mostrar(velas):
    l=len(velas)
    print('len',l)
    
    #velas[l-6].imprimir()
    #velas[l-5].imprimir()
    #velas[l-4].imprimir()
    #velas[l-3].imprimir()
    velas[l-2].imprimir()
    velas[l-1].imprimir()
    



def probar(par,escala):
    ind=pind.indicador(par)
    e=ind.ema(escala,10)
    print(time.time,   'ema',e)
    px=ind.precio_mas_actualizado()
    print('px',px)
    print(ind.actualizado)
    mostrar(ind.velas[escala].velas)

def probar_actualizar_btc_apto_para_altcoins():
    pind.actualizar_btc_apto_para_altcoins()
    



i=0
while i<90:
    probar_actualizar_btc_apto_para_altcoins()
    txt_btc_volatil='_' if pind.btc_apto_para_altcoins else '!'
    print('btc_volatil',txt_btc_volatil)
    time.sleep(10)
    print('----------------------------------------------------------------------------------------------------------------',)

