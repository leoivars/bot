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




def calcular():
    prop=Par_Propiedades(par,client,log)
    i=Indicadores(par,log)
    precio=i.precio('1h')
    pocs={}

    tiempo = 24
    while True:
        poc= i.mp_slice(tiempo,prop.tickSize)

        if poc[1] not in pocs:
            pocs[ poc[1] ]=[ poc[0], poc[2], 1 ]
        else:
           pocs[ poc[1] ] [2] += 1 
           if pocs[ poc[1] ] [0] > poc[0]:
               pocs[ poc[1] ] [0] = poc[0]
           if pocs[ poc[1]  ] [1] < poc[2]:
               pocs[ poc[1] ] [1] = poc[2]
        #print (pocs)

        #print('horas=',tiempo, poc, precio+atr, precio,atr)


        if  tiempo > 720: #> precio  +atr:
           
            break
        tiempo += 24

    
    print ('------------------------')
    lista = sorted(pocs.keys())
    pcompra=0
    difp_min=100
    for p in lista:
        dif = round( (precio/p -1)*100,2)
        difp = round( dif / pocs[p][2],2)  #diferencia con peso
         
        if difp > 0 and difp < difp_min:
            difp_min = difp
            pcompra = p
        
        print (p,dif,difp ,pocs[p])
    print ('------------------------')
    print ('precio compra=',pcompra)
    print ('------------------------')    
    
    





#-----------------------------------------------------------------------------------------------------


pws=Pws()
client = Client(pws.api_key, pws.api_secret)
log=Logger('config_moneda.log') 
conn=Conexion_DB(log)
db=Acceso_DB(log,conn.pool)

try:
    moneda=sys.argv[1].upper()
    moneda_contra=sys.argv[2].upper()
    hora_ini=int(sys.argv[3])
    #hora_fin=int(sys.argv[4])
except:
    moneda='???'
    moneda_contra='???'
    hora_ini=0
    #hora_fin=0

#valido par
par_ok=False
try:
    p = db.get_valores(moneda,moneda_contra)
    par=moneda+moneda_contra
    print ('Par:',par,p['idpar'])
    
    if p['idpar'] != -1:
        par_ok=True
        ind=Indicadores(par,log)
        print ('Par OK')

except Exception as e:
    print ('No se puede validar Par')

if par_ok and hora_ini >=0:
    for i in (1,3):
        calcular()
        time.sleep (90)

else:
    print ('analizar moneda moneda_contra hora_ini')    








