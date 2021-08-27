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



lector_precios=LectorPrecios(client)

lector_precios.leerprecios()

btc= lector_precios.tomar_precio('BTCUSDT')

gas= lector_precios.tomar_precio('GASBTC')


print (btc,gas,lector_precios.valor_usdt(8,'VIABTC'))

print ( '30 NEOBTC',lector_precios.usdt_cantidad(1,'NEOBTC'))
print ('30 NEOUSDT',lector_precios.usdt_cantidad(30,'NEOBTC'))
print ('30 BTCUSDT',lector_precios.usdt_cantidad(30,'BTCUSDT'))
print ('30 ZRXBTC',lector_precios.usdt_cantidad(30,'ZRXBTC'))
print ('30 ETHUSDT',lector_precios.usdt_cantidad(30,'ETHUSDT'))
print ('30 BATBTC',lector_precios.usdt_cantidad(30,'BATBTC'))
print ('valor 108 BATBTC',lector_precios.valor_usdt(108,'BATBTC'))


print (' 1 BTCUSDT', lector_precios.valor_usdt(1,'BTCUSDT'))
print (' 1 NEOUSDT', lector_precios.valor_usdt(10,'NEOUSDT'))
print (' 1 NEOBTC', lector_precios.valor_usdt(10,'NEOBTC'))
print (' BTCUSDT BTCUSDT', lector_precios.valor_usdt(0.00021074,'BTCUSDT'))