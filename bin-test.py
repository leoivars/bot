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
import pygame
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()


api_key = "AJ3CQ6LAJtpzAgG1wgnohjt5nVHk8VftntMGQrk1Rb2UcYkj5Z5TtxELMPv8elIh"
api_secret = "EGxRazPrqsw8wyWJcM2aC0dqkPgGXqcZLCxipA5DG5uchuVjg2Jw9XKO31LIhD2W"
client = Client(api_key, api_secret)

pares_a_ignorar=['HOTBTC','DENTBTC','SALTBTC','SYSBTC','GRSBTC','ARDRBTC']
pares_a_mirar=['BTCUSDT','BNBUSDT','NEOUSDT','TRXUSDT','TRXBTC',]


vector_s=[]





ahora={}
antes={}

sonido=audios.alerta(4)

log=Logger('bin-test-log')

lp=LectorPrecios(client)

def cargarlista(tickers):
    pares={}
    for t in (tickers):
        if t['symbol'].endswith("BTC") or t['symbol'].endswith("USDT"):
            pares[ t['symbol']]= float( t['quoteVolume'] )
    return pares
 

def porcentaje_cambio(antes,ahora):
    if antes<>0:
        return (ahora/antes-1)*100
    else:
        return 0


def iif(a,b,c):
    if a:
        return b
    else:
        return c        
         
       

def investigar(par,log):
    
    par=str(par) #esto remueve el encoding que biene como unicode pero yo estoy en utf8 y trae problemas para concatenar

    # si el para está en la lista de pares a ignorar no hago nada
    for p in (pares_a_ignorar):
        if p==par:
            return


    indicadores= Indicadores(par,log)

    

    avisar=False 
    avisos=[]  
        
    if indicadores.velas_positivas('5m',1,0.04):
        avisos.append(par + ' 5m x 1 una vela positiva 5m')
        #avisar=True 

    if indicadores.velas_positivas('5m',2,0.02):
        avisos.append(par + ' 5m x 2 velas positiva 5m')
        #avisar=True 

    if indicadores.velas_positivas('5m',3,0.015):
        avisos.append(par + ' 5m x 3 velas positiva 5m')
        #avisar=True 

    if indicadores.esta_subiendo('5m'):
        avisos.append(par + ' Está subiendo 5m')
        #avisar=True

    if indicadores.esta_subiendo('15m'):
        avisos.append(par + ' Está subiendo 15m')
        #avisar=True        

    if indicadores.velas_positivas('4h',3,0.01):
        avisos.append(par + ' 4h x 3 velas positivas')
        #avisar=True        
    
    if indicadores.esta_subiendo15m():
        if indicadores.la_ultima_vela_es_linda('4h'):
            rm=indicadores.rsi_mom('4h')
            vol=indicadores.volume('4h')
            avisos.append(par + ' Vela 4h linda: RSI ' + "%.2f " % rm[0] + 'MOM ' + "%.8f " % rm[1] + ' Vol: ' + iif(vol[0],'Bueno ','Malo ') +"%.2f " %  vol[1] +"%.2f " %  vol[2] +"%.2f " %  vol[3])
            avisar=True

    if avisar:

        print datetime.datetime.now().strftime('%Y %m %d %T'),'GMT -3'


        if indicadores.esta_lateral('15m'):
            avisos.append(par + '15m lateral')
        if indicadores.esta_lateral('1h'):
            avisos.append(par + '1h lateral')
        if indicadores.esta_lateral('4h'):
            avisos.append(par + '4h lateral')     


        libro=LibroOrdenes(client,par,'',2)
        libro.actualizar()






        sonido.play()



        for a in (avisos):
            print a



        px=lp.tomar_precio(par)
        if par.endswith("BTC"):
            btc=lp.tomar_precio('BTCUSDT')
            px=px*btc
        elif par.endswith("ETH"):
            eth=lp.tomar_precio('ETHUSDT')
            px=px*eth    
        
        print 'Volumen  1m:',indicadores.volumen_porcentajes('1m')
        print 'Volumen  5m:',indicadores.volumen_porcentajes('5m')
        print 'Volumen 15m:',indicadores.volumen_porcentajes('15m')
        print 'Volumen  1h:',indicadores.volumen_porcentajes('1h')
        print 'Volumen  4h:',indicadores.volumen_porcentajes('4h')
        print ''
        print 'subiendo  1m:',indicadores.esta_subiendo('1m')
        print 'subiendo  5m:',indicadores.esta_subiendo('5m')
        print 'subiendo 15m:',indicadores.esta_subiendo('15m')
        print 'subiendo  1h:',indicadores.esta_subiendo('1h')
        print 'subiendo  4h:',indicadores.esta_subiendo('4h')
        print ''
        print 'bajando   1m:',indicadores.esta_bajando('1m')
        print 'bajando   5m:',indicadores.esta_bajando('5m')
        print 'bajando  15m:',indicadores.esta_bajando('15m')
        print 'bajando   1h:',indicadores.esta_bajando('1h')
        print 'bajando   4h:',indicadores.esta_bajando('4h')
        print '' 
        print 'Tendencia: ',indicadores.tendencia() 




        print 'precio.usd:', px    , 'con 10 usd=',10/px

        print libro.imprimir()



tickers = client.get_ticker()
ahora=cargarlista(tickers)    


while True:
    lp.leerprecios()
    antes=ahora
    tickers = client.get_ticker()
    ahora=cargarlista(tickers)
    for k, v in ahora.iteritems():
        p= porcentaje_cambio(antes[k],v)
        
        if p>0.1:
            #print 'investigar:', k,'volumen',v,p
            #log.log(k,v,p)
            investigar(k,log)
        else:
            for ki in (pares_a_mirar): #fuerzo la investigación de los pares que estan en pares a mirar
                if ki==k:
                    investigar(k,log)
                    break
    log.log('---------------------------------')
    time.sleep(60)
            




        




