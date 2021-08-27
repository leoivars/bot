from indicadores2 import Indicadores

from logger import *
import time
from pws import Pws
from binance.client import Client # Cliente python para acceso al exchangue
#import matplotlib.pyplot as plt
from analizador import Analizador
from variables_globales import VariablesEstado

pws=Pws()
client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_indicadores.log') 


#pares=['BTCUSDT','EDOBTC','XRPBTC']
#pares=['BNBBTC','THETABTC','NEBLBTC','WTCBTC']
ganancia_segura=10

pares=['SKYBTC','BTCUSDT','PNTBTC']
periodos=[30,60]
e = VariablesEstado


for par in (pares):
    d=7
    i=Indicadores(par,log,e)
    a=Analizador(i)

    precio_compra=i.precio('1d')
    
    #print('precio compra',precio_compra)
    
    r = a.altobajo.calcular_gi_gs_tp(precio_compra, '1d')
    print (par,r)
        #print(r)



    #print (a.fibo.retroceso_fibo('15m')) 

    #for i in range(0,7):
    #    print ('soporte--->',i,a.riesgo_beneficio.soporte(i) )
    # print (par,'ganancia_infima',a.riesgo_beneficio.ganancia_infima)
    # print (par,'ganancia_segura',a.riesgo_beneficio.ganancia_segura)
    # print (par,' tomar_perdidas',a.riesgo_beneficio.tomar_perdidas)
    # print (par,' riesgo_beneficio',a.riesgo_beneficio.riesgo_beneficio)
    # print (par,' riesgo_beneficio_natural',a.riesgo_beneficio.riesgo_beneficio_natural)

    # print (par, 'patrones',a.patrones.buscar_patron())
    
    # print (par, 'enaemas ', a.emas.soporte(1))

    # print (par, 'resistencia ', a.riesgo_beneficio.primer_resistencia())
    # print (par, 'resistencia p', a.riesgo_beneficio.primer_resistencia_porcentaje())
    
    # a.riesgo_beneficio.set_temporalidades(['15m','30m'])
    # a.riesgo_beneficio.set_poc(0)
    # print (par, 'soporte poc 0 ', a.riesgo_beneficio.soporte(1)    ,a.riesgo_beneficio.soporte(2),a.riesgo_beneficio.precio )
    
    # a.riesgo_beneficio.set_poc(1)
    # print (par, 'soporte poc 0 ', a.riesgo_beneficio.soporte(1)    ,a.riesgo_beneficio.soporte(2),a.riesgo_beneficio.precio )
    
    # a.riesgo_beneficio.set_poc(2)
    # print (par, 'soporte poc 0 ', a.riesgo_beneficio.soporte(1)    ,a.riesgo_beneficio.soporte(2),a.riesgo_beneficio.precio )

    # print (par, 'soporte fibo', a.riesgo_beneficio.soporte_fibo(1),a.riesgo_beneficio.soporte_fibo(2) )





    #print (par, a.riesgo_beneficio.relacion_riesgo_beneficio())
    #print (par,i.analisis_minmax("1d",d,2,4)  )
    #print (par,i.puntos_pivote('atr'))
    

    print('--------------------------------')    
        
