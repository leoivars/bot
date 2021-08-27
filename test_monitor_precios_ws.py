#from indicadores2 import *
from logger import *
import time
import pws
#from Monitor_precios_ws import MonitorPreciosWs
from funciones_utiles import memoria_consumida

#import matplotlib.pyplot as plt




def hacer_tiempo(t):
    print('haciendo tiempo...',t)
    time.sleep(t)


log=Logger('Test_lector_de_precios_3.log') 




mo_pre=MonitorPreciosWs(log)


mo_pre.empezar()

bucles=20
while bucles>0:
    bucles-=1
 
    print('ultima actualizacion' ,mo_pre.estado_general()  )
    #print('BTCUSDT', mo_pre.precio_no_baja2('BTCUSDT')  )
    #print('ETCBTC'  ,mo_pre.ema_precio_no_baja('ETCBTC')  )

    #print('estado_general', mo_pre.estado_general() )
    #
    # 
    # print('promedio_de_altos ETH', mo_pre.promedio_de_altos('ETHBTC')  )
    
    hacer_tiempo(5)
    
    print('reiniciando...')
    #mo_pre.reconectar()


mo_pre.morir()    

#del mo_pre


   

    #print('variacion_precio BTCUSDT', mo_pre.variacion_precio('BTCUSDT')  )
    #print('variacion_precio ATOMBTC', mo_pre.variacion_precio('ATOMBTC')  )
    
    
    
    #if mo_pre.precio_fecha('BTCUSDT'):
    #    print('BTCUSDT',mo_pre.precios['BTCUSDT'][1].actualizaciones)
    #if mo_pre.precio_fecha('ETHBTC'):
    #    print('ETHBTC',mo_pre.precios['ETHBTC'][1].actualizaciones)    

    #print ( mo_pre.precio('BTCUSDT') )
    #print ( mo_pre.precio_fecha('BTCUSDT') )


    #print ('BTCUSDT  no baja',mo_pre.precio_no_baja("BTCUSDT"),'px',mo_pre.precio('BTCUSDT'))
    #print ( mo_pre.precio_fecha("BTCUSDT")     )
    
  