# # -*- coding: UTF-8 -*-
import sys
import time
from par import *
import datetime
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
import _thread
import json
#import sqlite3
from logger import *
from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB
from pws import Pws
from variables_globales import  Global_State
from pool_indicadores import Pool_Indicadores
#import tracemalloc
import gc
#import mem_top
#import traceback
from Monitor_precios_ws import MonitorPreciosWs

# import logging 
# logging.basicConfig(filename='./logs/auto_compra_vende.log',level=logging.DEBUG)


pws=Pws()

log=Logger('test_par.log') 

client = Client(pws.api_key, pws.api_secret,{ "timeout": 20})

#web soket de monitor de precios
mo_pre=MonitorPreciosWs(log)
mo_pre.empezar() 

conn=Conexion_DB(log)                          
fxdb=Acceso_DB_Funciones(log,conn.pool)        
db = Acceso_DB(log,fxdb) 

e=Global_State()

IndPool=Pool_Indicadores(log,mo_pre,e)

#                           MONEDA   MONEDA_CONTRA 
nuevo_par=Par(client,'BTC'  ,'USDT',conn.pool,mo_pre,e,IndPool)
nuevo_par.cargar_parametros_iniales()
#nuevo_par.tomar_precio(nuevo_par.lector_precios.leerprecios())


#ind: Indicadores= IndPool.indicador('BTCUSDT')


IndPool.actualizar_parametros_btc()
nuevo_par.estado=2
nuevo_par.funcion='comprar'
#nuevo_par.analisis_provocador_entrada='decidir_comprar_ema_macd_adx2'

nuevo_par.precio_salir_derecho=10333

#nuevo_par.actualizar_valores_de_rango()
#nuevo_par.calcular_gi_gs_tp()
print (nuevo_par.g.ema_pendiente_maxima)
for k in nuevo_par.g.ema_pendiente_maxima:
    print (k,nuevo_par.g.ema_pendiente_maxima[k],type(nuevo_par.g.ema_pendiente_maxima[k]))



#print('PRECIO INICIAL',nuevo_par.estado_1_calcular_precio_inicial() )


#nuevo_par.calcular_precio_objetivo()


#print(nuevo_par.precio_ganancia_infima,nuevo_par.precio_ganancia_segura,nuevo_par.tomar_perdidas,nuevo_par.precio_objetivo )



# print('texto_analisis_par ',nuevo_par.texto_analisis_par()  )


#print(' test---calcular_cantidad_posible_para_comprar:    ',nuevo_par.calcular_cantidad_posible_para_comprar()  )

#print ('rango',ind.redondear_uni)


#nuevo_par.ganancia_infima=2
#nuevo_par.precio_compra=100


#print ('precio_de_venta_minimo',nuevo_par.precio_de_venta_minimo(2))
#print ('Calcular Precio de Compra:',nuevo_par.calcular_precio_de_compra())

#nuevo_par.establecer_cantidad_a_comprar()



#nuevo_par.precio_compra=8700
#print ('precio',nuevo_par.precio)
#print ( 'calcular_ganancies',nuevo_par.ganancias())
#print ( 'calcular_precio(5pganancias)',nuevo_par.calc_precio(5))

#nuevo_par.precio_compra=nuevo_par.calcular_precio_de_compra()
#print ('test...nuevo_par.precio_compra',nuevo_par.precio_compra)
#cant=nuevo_par.calcular_cantidad_a_comprar()
#print ('test...calcular_cantidad_a_comprar',cant, cant * nuevo_par.precio)
#print ('test...precio',nuevo_par.precio)
#print ('test...tickSize',nuevo_par.tickSize)
#print ( 'fondos para comprar', nuevo_par.fondos_para_comprar())
#print ( 'objetivo', nuevo_par.calcular_precio_objetivo())


#nuevo_par.establecer_cantidad_a_vender()
#print ('self.idtrade',nuevo_par.idtrade)
#print ('self.precio_compra',nuevo_par.precio_compra)
