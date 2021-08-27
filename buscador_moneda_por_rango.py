#!/usr/bin/python3
# # -*- coding: UTF-8 -*-

import sys
from logger import * #clase para loggear
from correo import * #clase para mandar correos
from acceso_db import * #acceso a la base de datos 
from acceso_db_conexion import *
from indicadores2 import *
from funciones_utiles import *
from pws import Pws
import sys
import time
from par_propiedades import Par_Propiedades
from formateadores import format_valor_truncando

tiempos=[6,12,24,48,96,192,384,768]

def buscar_pares(dic_pares):
    for r in dic_pares:
        moneda=r['moneda']
        moneda_contra=r['moneda_contra']
        par=moneda+moneda_contra
        #print (par)

        prop = Par_Propiedades(par,client,log)
        i = Indicadores(par,log)
        precio = i.precio('1h')
    
        encontrado = False
        for tiempo in tiempos:
            time.sleep(0.25)
            if tiempo>= horas:
                poc= i.mp_slice(tiempo,prop.tickSize)
                variacion = (precio / poc[0] -1) * 100
                #print (par,tiempo,variacion,precio,poc)
                if precio > poc[0] and poc[0] < poc[1] < poc[2] and variacion <2  :
                    encontrado=True
                    break
            
        if encontrado:
            log.log ( par,'tiempo:',round(tiempo/24,2), 'Max:' ,format_valor_truncando(poc[2],prop.moneda_precision), \
                                                        'POC:' ,format_valor_truncando(poc[1],prop.moneda_precision), \
                                                        'Px:'  ,format_valor_truncando(precio,prop.moneda_precision), \
                                                        'Min:' ,format_valor_truncando(poc[0],prop.moneda_precision)
                    )


pws=Pws()
client = Client(pws.api_key, pws.api_secret)
log=Logger('buscador_mercados_por_rango.log') 
conn=Conexion_DB(log)
db=Acceso_DB(log,conn.pool)


try:
    horas=int(sys.argv[1])
except:
    horas=0

#valido par

if horas > 0:
    log.log('---INICIO----')
    buscar_pares( db.get_habilitables_lindos() )
    buscar_pares( db.get_habilitables_feos()  )
    log.log('---- FIN ----')
else:
    print ('Horas debe > 0')    
    
