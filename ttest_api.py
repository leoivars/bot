# # -*- coding: UTF-8 -*-
import sys
from datetime import datetime
from dateutil import tz
from par import *
from indicadores2 import *
from logger import *
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
from LectorPrecios import *
from LibroOrdenes import *
import json
import numpy
import talib
import time
import audios

#import pygame
#pygame.mixer.pre_init(44100, -16, 2, 2048)
#pygame.init()

# codigo para tomar argumentos de linea de comando
# hay que mejorarlo para tomar varios argumentos
# mirar https://www.tutorialspoint.com/python/python_command_line_arguments.htm
if len(sys.argv)<2:
    arg_par='TRX'
else:
    arg_par=sys.argv[1].upper()

api_key = "AJ3CQ6LAJtpzAgG1wgnohjt5nVHk8VftntMGQrk1Rb2UcYkj5Z5TtxELMPv8elIh"
api_secret = "EGxRazPrqsw8wyWJcM2aC0dqkPgGXqcZLCxipA5DG5uchuVjg2Jw9XKO31LIhD2W"
client = Client(api_key, api_secret)




def consultar_estado_ultima_orden(par):
        #self.log.log(  "Consulta de estado de ultima orden creada:" )
        
        orden={}
        intentos=3
        while intentos>0:
            try:
                orders = client.get_all_orders(symbol=par, limit=1)
                estado_orden=orders[0]['status']
                price=float(orders[0]['price'])
                #print(  "Consulta de estado de ultima orden creada=", estado_orden )
                #print (orders)
                orden=orders[0]
                break
            except Exception as e:
                
                print(  e.message )
                print(  "consultar_estado_ultima_orden:, reintento en 15 seg." )
                time.sleep(15)
            
            intentos-=1    
        
        return orden



print (consultar_estado_ultima_orden('MODBTC'))