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
from funciones_utiles import  calcular_fecha_futura,  strtime_a_fecha



log=Logger('control_de_trades.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)





#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)

estado_general=VariablesEstado()

oe=OrdenesExchange(client,'BTCUSDT',log,estado_general)


parser = argparse.ArgumentParser()
parser.add_argument("-m",   "--moneda"                , help="Moneda")
parser.add_argument("-c",   "--contra"                , help="Moneda Contra")
parser.add_argument("-d",   "--dias_en_el_futuro"     , help="Días en el futuro")
args = parser.parse_args()




#valido par
moneda=args.moneda.upper()
moneda_contra=args.contra.upper()
par_ok=False
try:
    p = db.get_valores(moneda,moneda_contra)
    par=moneda+moneda_contra
    print ('Par:',par,p['idpar'])
    
    if p['idpar'] != -1:
        par_ok=True
        print ('Par OK')

except Exception as e:
    print ('No se puede validar Par')


#valido dias
dias=0
try:
    dias=int(args.dias_en_el_futuro)
    
except Exception as e:
    print ('No se puede validar los días en el futuro')


if not par_ok or dias <=0:
    print('Argumentos inválidos')
else:
    print('actualizando') 
    fecha_habilitacion_futura =  calcular_fecha_futura( 1440 * dias )   
    db.habilitar_en_el_futuro(moneda,moneda_contra,fecha_habilitacion_futura)



