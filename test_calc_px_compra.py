from indicadores2 import Indicadores
from par_propiedades import Par_Propiedades
from logger import Logger
import time
from pws import Pws
from binance.client import Client #para el cliente
from numpy import isnan
from par_propiedades import Par_Propiedades
from variables_globales import VariablesEstado
from libro_ordenes2 import Libro_Ordenes_DF
from ordenes_binance import OrdenesExchange
from  formateadores import format_valor_truncando
from mercado import Mercado

from calc_px_compra import Calculador_Precio_Compra

pws=Pws()

client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_calc_px_compra.log') 

moneda = 'BTC'
moneda_contra ='USDT'

par=moneda+moneda_contra
libro=Libro_Ordenes_DF(client,moneda,moneda_contra,25) #cleación del libro

g = VariablesEstado()

oe = OrdenesExchange(client,par,log,g)
info = oe.info_par()
tickSize  = info['tickSize']
precision = info['moneda_precision']

par_prop = Par_Propiedades(par,client,log)
mercado = Mercado(log,g,client)
#ind_par= Indicadores(par,log,g,client)
ind_btc= Indicadores("BTCUSDT",log,g,Mercado)


calc = Calculador_Precio_Compra(par,g,log,ind_btc,libro)

escalas=['1d','4h','1h']
metodos=[]
metodos.append('libro_grupo_mayor')
#metodos.append('libro_grupo_mayor')
#metodos.append('pefil_volumen')
#metodos.append('rango_macd_menor')     # NO ESTÁ FUNCIONAN BIEN para situaciones rango o alcistas
#metodos.append('parte_baja_rango_macd') # situaciones rango, bajistas
# metodos.append('libro_mejor_px')
# metodos.append('ret_fibo') # para situaciones bajistas
#metodos.append('ema_9')
# metodos.append('ema_20')
# metodos.append('ema_55')
# metodos.append('mecha_bajo_ema_20')
# metodos.append('mecha_bajo_ema_55')
# metodos.append('ema_menor')
# metodos.append('menor_de_emas_y_cazaliq') #hay que revisar
# metodos.append('mayor_de_emas_y_cazaliq') #hay que revisar
# metodos.append('scalping') #hay que revidar
# metodos.append('ema_minimos_1') #bajitas parte baja
# metodos.append('ema_minimos_3') #bajitas parte baja
# metodos.append('ema_55_min_3')  #bajitas parte baja
# metodos.append('cazabarridas_rango') #no usar y revidar
# metodos.append('cazabarridas') no usar revisar muy bien antes
# metodos.append('mejor_de_4')
#metodos.append('caza_rsi_bajo')
#metodos.append('cazaliq')

resultados = []
for e in escalas:
    for m in metodos:
       resultados.append( [ e,m,calc.calcular_precio_de_compra(m,e) ]  )

for r in resultados:
    print(r)
