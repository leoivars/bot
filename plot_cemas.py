from indicadores2 import *
from logger import *
import time
from LibroOrdenes import *
import matplotlib.pyplot as plt
from pws import Pws
from no_se_usa.acceso_db import *
from acceso_db_conexion import *
pws=Pws()
client = Client(pws.api_key, pws.api_secret)


log=Logger('Test_cemas.log') 

#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)


def dibujar(moneda,fecha,color):
    p=db.get_valores(moneda,'BTC')
    datos=db.ind_historico_get_ultimos(p['idpar'],fecha)
    plt.plot(*zip(*datos),color)

fecha='2019-10-01'
dibujar('BNB',fecha,'g')
dibujar('EDO',fecha,'r')
dibujar('ETH',fecha,'b')
dibujar('WABI',fecha,'y')


plt.show()


