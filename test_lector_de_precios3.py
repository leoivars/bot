#from indicadores2 import *
from logger import *
import time
import pws
from LectorPrecios3 import LectorPrecios

#import matplotlib.pyplot as plt




def hacer_tiempo(t):
    print('haciendo tiempo...',t)
    time.sleep(t)


log=Logger('Test_lector_de_precios_3.log') 




lt=LectorPrecios(log)
lt.empezar()



bucles=10
while bucles>0:
    bucles-=1

   

    hacer_tiempo(900)
    
    

lt.detener()


    
   

    