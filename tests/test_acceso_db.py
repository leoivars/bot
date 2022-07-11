import os
import sys
from pathlib import Path
sys.path.append(str(Path('..').absolute().parent))          #para que se pueda usar app. como mudulo
sys.path.append(str(Path('..').absolute().parent)+"/app")   #para que los modulos dentro de app encuentren a otros modulos dentro de su mismo directorio

# print ('------------------getcwd()----->', os.getcwd())
# print ('----------------__file__------->', __file__)
# print ('---------------DIR_LOGS-------->', os.getenv('DIR_LOGS', '????'))
# print ('---------------CONFIG_FILE----->', os.getenv('CONFIG_FILE', '????'))

from app.acceso_db_conexion import Conexion_DB
from app.acceso_db_funciones import Acceso_DB_Funciones
from app.acceso_db_modelo import Acceso_DB

from app.logger import Logger
from datetime import *
from app.indicadores2 import Indicadores
from app.pws import Pws
from binance.client import Client #para el cliente

log=Logger('test_acceso_db.log') 
pws=Pws()

#apertura del pool de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
if conn.pool:
    fxdb=Acceso_DB_Funciones(log,conn.pool)        
    db = Acceso_DB(log,fxdb)  

    print ('trades_cantidad_de_pares_con_trades', db.trades_cantidad_de_pares_con_trades() )
    print ('trades_cantidad',db.trades_cantidad('PNT','USDT')  )

