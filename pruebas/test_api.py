# # -*- coding: UTF-8 -*-
import sys
from datetime import datetime
#from dateutil import tz
#from par import *

from logger import *
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
#from LectorPrecios import *
#from LibroOrdenes import *
import json
#import numpy
#import talib
import time
#import audios
from pws import Pws
import types

pws=Pws()
#import pygame
#pygame.mixer.pre_init(44100, -16, 2, 2048)
#pygame.init()

# codigo para tomar argumentos de linea de comando
# hay que mejorarlo para tomar varios argumentos
# mirar https://www.tutorialspoint.com/python/python_command_line_arguments.htm
#if len(sys.argv)<2:
#    arg_par='TRX'
#else:
#    arg_par=sys.argv[1].upper()




def consultar_ultima_orden_realizada(self,par):
        #self.log.log(  "Consulta de estado de ultima orden creada:" )
        
        orden={}
        intentos=3
        while intentos>0:
            try:
                orders = self.client.get_all_orders(symbol=par, limit=50)
                for o in orders:
                    print(o)
                orden=orders[0]
                break
            except Exception as e:
               #self.log.log(  e )
               # self.log.log(  "Error en consultar_ultima_orden_realizada():, reintento en 15 seg." )
                time.sleep(7)
            
            intentos-=1    
        
        return orden

def tomar_info_par(self): 
        #obtengo info de la moneda y fijo los paramentro necesarios por ahora solo la presicion de la cantidad
        #esto sirve para que se pueda realizar cualquier tipo de orden usado lo que pide el exchange
        
        intentos=20
        ejecutado= False
        while intentos>0 and not ejecutado:
            try:
                
                info = self.client.get_symbol_info(self.par)
                for f in (info['filters']):
                    print (f)
                    if f['filterType']=='LOT_SIZE':
                       self.cant_moneda_precision=int((f['stepSize']).find('1'))-1
                       if self.cant_moneda_precision==-1: self.cant_moneda_precision=0
                       #self.log.log(  'stepSize',f['stepSize'],self.cant_moneda_precision )

                    if f['filterType']=='PRICE_FILTER':

                        self.moneda_precision=int((f['tickSize']).find('1'))-1
                        if self.moneda_precision==-1: self.moneda_precision=0
                        #self.log.log(  'tickSize',f['tickSize'], self.moneda_precision )
                        self.tickSize=float(f['tickSize'])# este valor parece ser la minima unidad aceptada de incremento/decremento

                    if  f['filterType']=='MIN_NOTIONAL':
                        self.min_notional=float(f['minNotional'])
                        print (self.min_notional)
                        print ('MIN_NOTIONAL',f)


                        #"filterType": "MIN_NOTIONAL", Este es el valor minimo hipotetico que debe tener una orden en moneda_contra
                        #"minNotional": "0.00100000"

                ejecutado= True
            except Exception as e:
                
                print( e,self.par, "Error de tomar_info_par, reintento en 15 seg.")
                time.sleep(15)
            intentos-=1    
        return ejecutado     
    
def consultar_estado_orden(self):
        
    intentos=3
    exito= False
    estado_orden='NO_SE_PUDO_CONSULTAR'
    precio=0
    ejecutado=0
    while intentos>0 and not exito:
        #self.log.log(  "Consulta de estado de ultima orden creada intento:",intentos )
        try:
            order = self.client.get_order(symbol=self.par,orderId=14479554)
            ejecutado=True 
            estado_orden=str(order['status'])
            precio=float(order['price'])
            ejecutado=float(order['executedQty'])
            exito=True
            #self.log.log(  "Consulta de estado de ultima orden creada=", estado_orden )
        except Exception as e:
            
            #self.log.log(  e )
            #self.log.log(  "Error en consultar_estado_orden():, reintento en 15 seg." )
            time.sleep(15)
        
        intentos-=1    

    return {'estado':estado_orden,'precio':precio,'ejecutado':ejecutado}   

self=types.SimpleNamespace()
self.client = Client(pws.api_key, pws.api_secret)

self.par='HCBTC'
print(consultar_estado_orden(self))


