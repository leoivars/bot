import sqlite3
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from logger import *
from datetime import *
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from ordenes_binance import OrdenesExchange
import argparse
import math
from variables_globales import  VariablesEstado
from funciones_utiles import strtime_a_fecha,str_fecha,str_fecha_hora_mysql


log=Logger('analizar_trades_cerrados.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)


#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

estado_general=VariablesEstado()


parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"            , help="Moneda")
parser.add_argument("-c",   "--moneda_contra"     , help="Moneda contra")
args = parser.parse_args()

    

def get_promedio(moneda,moneda_contra):
    sql = '''select sum(cantidad) as cantidad,sum(precio*cantidad)/sum(cantidad) as precio, count(1) as trades 
    from trades where ejecutado = 0
    and moneda = %s and moneda_contra = %s 
    '''   
    return db.ejecutar_sql_ret_dict(sql,(moneda,moneda_contra))

def cerrar_ordenes_promediadas(moneda,moneda_contra):
    analisis = 'promediado ' + str_fecha()
    sql = ''' update trades set ejec_precio = precio, ejecutado=cantidad,analisis = %s ,ejec_fecha=now() 
    where ejecutado=0 and moneda= %s and moneda_contra = %s '''
    db.ejecutar_sql(sql,(analisis,moneda,moneda_contra))

def crear_nueva_orden_con_promedio(moneda,moneda_contra,promedio):
    #                  moneda,moneda_contra ,escala, senial_entrada       ,cantidad            ,precio_compra     ,ganancia_infima,ganancia_segura,tomar_perdidas,analisis  ,fecha,orderid):
    db.trade_persistir(moneda,moneda_contra,'1d'   ,'promedio de compras',promedio['cantidad'],promedio['precio'],5              ,10             ,-5            ,'promedio',str_fecha_hora_mysql(),0)
    

moneda        = args.moneda.upper()
moneda_contra = args.moneda_contra.upper()

p = get_promedio(moneda,moneda_contra)[0]
print (p)
if p['precio'] > 0 and p['cantidad'] > 0 and p['trades']>1 : #tiene que haber mas de un trade para que tenga sentido promediar.
    cerrar_ordenes_promediadas(moneda,moneda_contra)
    crear_nueva_orden_con_promedio(moneda,moneda_contra,p)
