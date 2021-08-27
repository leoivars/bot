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

log=Logger('bintest1.log') 

i1=Indicadores(arg_par,log)
btc='BTCUSDT'
i2=Indicadores(btc,log)

while True:
    print 'Par:',arg_par
    rm=i1.rsi_mom('4h')
    print 'RSI 4H:',rm[0]
    print 'MOM 4H:',rm[1]
    print 'ATRs:',i1.atr_todos()
    print '-------------------------'
    print 'Par:',btc
    rm=i2.rsi_mom('15m')
    print 'RSI 15m:',rm[0]
    print 'MOM 15m:',rm[1]
    print 'EMA 15M,25p:',i1.ema('15m',20)
    print 'subiendo:',i1.esta_subiendo15m()


    rm=i2.rsi_mom('4h')
    print 'RSI 4h:',rm[0]
    print 'MOM 4h:',rm[1]
    print 'EMA 15M,25p:',i2.ema('15m',20)
    print 'subiendo  1m:',i2.esta_subiendo('1m')
    print 'subiendo  5m:',i2.esta_subiendo('5m')
    print 'subiendo 15m:',i2.esta_subiendo('15m')
    print 'subiendo  1h:',i2.esta_subiendo('1h')
    print 'subiendo  4h:',i2.esta_subiendo('4h')
    print ''
    print 'bajando   1m:',i2.esta_bajando('1m')
    print 'bajando   5m:',i2.esta_bajando('5m')
    print 'bajando  15m:',i2.esta_bajando('15m')
    print 'bajando   1h:',i2.esta_bajando('1h')
    print 'bajando   4h:',i2.esta_bajando('4h')
    print '' 
    print 'Tendencia: ',i2.tendencia() 
    
    


    print 'ATRs:',i2.atr_todos()
    print '---------------------------------------------------------------------------------------'
    

    time.sleep(30) 

