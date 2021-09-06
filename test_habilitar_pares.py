from fauto_compra_vende.habilitar_pares import habilitar_pares

from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from variables_globales import VariablesEstado
from logger import *
from logger import *
from pws import Pws
log=Logger('habilitar_pares.log') 

pws=Pws()
#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
g = VariablesEstado()
if conn.pool:
    db = Acceso_DB(log,conn.pool)  
    print ('habilitar_pares', habilitar_pares(g,db) )

    