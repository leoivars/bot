from acceso_db_conexion import Conexion_DB
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB

from logger import *
from datetime import *
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente

log=Logger('test_acceso_db.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)


#apertura del pool de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
if conn.pool:
    fxdb=Acceso_DB_Funciones(log,conn.pool)        
    db = Acceso_DB(log,fxdb)  

    print ('trades_cantidad_de_pares_con_trades', db.trades_cantidad_de_pares_con_trades() )
    print ('trades_cantidad',db.trades_cantidad('PNT','USDT')  )

