from reporte_estado import ReporteEstado

from no_se_usa.acceso_db import *
from acceso_db_conexion import *
from logger import *
from datetime import *
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from Monitor_precios_ws import MonitorPreciosWs
from variables_globales import  VariablesEstado
from twisted.internet import reactor




log=Logger('test_reportess.log') 


#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)
mo_pre = MonitorPreciosWs(log)
mo_pre.empezar()
e=VariablesEstado()

time.sleep(60)


r = ReporteEstado(log,db,mo_pre,e)


print ( r.reporte(1,2020) ) 
print ( r.reporte(2,2020) ) 
print ( r.reporte(3,2020) ) 
print ( r.reporte(4,2020) ) 
print ( r.reporte(5,2020) ) 
print ( r.reporte(6,2020) ) 

mo_pre.detener()
reactor.stop()



mo_pre.empezar()
time.sleep(60)
mo_pre.morir()
reactor.stop()
