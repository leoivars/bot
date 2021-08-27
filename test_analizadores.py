
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from numpy import isnan
from par_propiedades import Par_Propiedades
from variables_globales import VariablesEstado
import matplotlib.pyplot as plt
from  formateadores import format_valor_truncando
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from indicadores2 import Indicadores
from analizador import Analizador_Patrones

pws=Pws()

client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_analizadores.log') 
e = VariablesEstado()
    
def probar_atr_bajos(par,escala): 
    ind=Indicadores(par,log,e,client)
    ana = Analizador_Patrones(ind)
    
    print(ana.detectar_patrones(escala))
    print('---------------------------------------------------------')



while True:
    probar_atr_bajos('LTCUSDT','5m')
    time.sleep(60)



   