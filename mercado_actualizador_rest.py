# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from velaset import VelaSet
from vela import Vela
# from vela import *
# from binance.client import Client #para el cliente
# from binance.enums import * #para  create_order
from binance.client import Client
import time
import random
import numpy as np

import traceback
from datetime import datetime
#from market_profile import MarketProfile
import pandas as pd
import pandas_ta as ta

from  variables_globales import Global_State

from cola_de_uso import Cola_de_uso

from funciones_utiles import variacion,compara,signo



class Actualizador_rest:
    '''
      Clase responsalbe de actualizar el velaset via rest
    '''
    max_retardo=15
    max_actualizacion=65

    def __init__(self,log,estado_general,cliente:Client):
        
        self.g:Global_State = estado_general
        
        self.log=log
        self.retardo=5
        self.errores=0
        self.client = cliente
        
        self.cola = Cola_de_uso(log,estado_general)
        self.prioridad = 0

    def cargainicial(self,par,escala):
        '''
        Retorna un velaset con los datos obtenidos 
        '''
        
        self.errores=0
        self.retardo=0
        
        ahora=time.time()

        ret = None
        
        # configuro el intervalo y la cantidad de velas que necesito para cada uno de ellos
        rango_fin=int(ahora * 1000  )
        
        if escala=='1m':
            cvel=500
            ch=int(cvel/60)+1 #60 velas por hora
            rango_pedido = str(ch)+" hour ago UTC"
            intervalo = Client.KLINE_INTERVAL_1MINUTE
        elif escala=='3m':
            cvel=500
            ch=int(cvel/20)+1 #20 velas por hora
            rango_pedido = str(ch)+" hour ago UTC"
            intervalo = Client.KLINE_INTERVAL_3MINUTE
        elif escala=='5m':
            cvel=500
            ch=int(cvel/12)+1 #12 velas por hora
            rango_pedido = str(ch)+" hour ago UTC"
            intervalo = Client.KLINE_INTERVAL_5MINUTE
        elif escala=='15m':
            cvel=500
            cd=int(cvel/96)+1 #96 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_15MINUTE
        elif escala=='30m':
            cvel=500
            cd=int(cvel/96/2)+1 #96/2 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_30MINUTE
        elif escala=='1h':
            cvel=500
            cd=int(cvel/24)+1 #24 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1HOUR
        elif escala=='2h':
            cvel=500
            cd=int(cvel/12)+1 #12 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_2HOUR
        elif escala=='4h':
            cvel=500
            cd=int(cvel/6)+1 #6 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_4HOUR
        elif escala=='1d':
            cvel=500
            rango_pedido = "180 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1DAY
        elif escala=='1w':
            cvel=500
            rango_pedido = "399 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1WEEK
        elif escala=='1M':
            cvel=500
            rango_pedido =  "1460 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1MONTH

        rango_ini=int(  ahora - self.g.escala_tiempo[escala] * cvel)    * 1000 

        while self.g.trabajando: 
            self.operacion_empezar(par+'_'+escala + '_i_')    
            err=False 
            
            try:
                if self.retardo >0: 
                    self.log.err( "inicio cargainicial(",par, escala , intervalo,  rango_ini,rango_fin,")")

                klines = None
                klines =self.client.get_historical_klines(par, intervalo,  rango_ini, rango_fin) # para carga inicial

                if klines != None:
                    ret = VelaSet(klines,cvel)   
                    self.dec_retardo()
                    del klines

                if self.retardo >0: 
                    self.log.err( "fin cargainicial(",escala,")")
                
            except Exception as e:
                txt_error=str(e)
                #self.log.log( e )
                #binance.exceptions.BinanceAPIException: APIError(code=-1003): Too much request weight used; current limit is 1200 request weight per 1 MINUTE. Please use the websocket for live updates to avoid polling the API.
                #tb = traceback.format_exc()
                #self.log.log( tb)
                self.log.log('klines',klines,par,rango_pedido)
                err=True
                tiempo_espara=self.tiempo_espera_error(txt_error)
                self.inc_retardo()
                #self.crear_cliente() #boora y crea un nuevo cliente
                self.log.err( "....Error en cargainicial(",escala,"), rango (",rango_pedido,") , reintento en" ,self.retardo, txt_error)
           
            self.operacion_terminar() #libero el semáforo     
            
            if err:#=True 
                #self.prioridad=0
                self.log.err( 'Retardo--->',self.retardo)  
                #self.crear_cliente()
                time.sleep(tiempo_espara) # espero en caso de errors
                
            else:
                #self.log.log('Carga inicial:', par,escala, ret.df.count() )
                
                break    
         
        return ret
    
    def operacion_empezar(self,referencia):
        #self.log.log('Waiting for lock')
        #print ('...acquire'+par)
        #Indicadores.semaforo.acquire()

        self.cola.acceso_pedir(referencia,self.prioridad)
        self.cola.acceso_esperar_mi_turno()
        

        self.__inicio_ocupando_turno = time.time()
        #self.regulador_requests_minute()

        #log de la cola
        #lin='SOY:__' +par+'COLA:\n'
        #for c in Indicadores.cola:
        #    lin += c +'\n'
        #self.log.log(lin)   
        pedcola = self.cola.largo()
        if pedcola > 120:
            self.log.log('Pedidos en cola =',  pedcola,'demora_promedio',self.cola.demora_de_cola() ) 

        if self.retardo > 0 and self.errores > 10: #debug solo cuando hay mucho errores
            self.log.err('--operacion_empezar--------------->',referencia, 'errores,errores/minuto',self.errores)
            #self.log.err('ERROR MUY FEO! acceso_finalizar_turno: ',self.ticket_acceso)    
        
    def operacion_terminar(self):
        #control de rendimiento
        demora=time.time() - self.__inicio_ocupando_turno
        #if demora > self.cola.demora_promedio * 10:
        #self.log.err('DEMORA!=',round(demora,4), 'ticket', self.cola.ticket_acceso,'cola',self.cola.largo(),'demora_promedio',self.cola.demora_de_cola() )
            
              
        self.cola.acceso_finalizar_turno(demora)

    def dec_retardo(self):
        self.retardo-=1
        if self.retardo<0: 
            self.retardo=0

        self.errores-=1
        if self.errores<0:
           self.errores=0         

    def inc_retardo(self):
        
        self.errores += 1
        self.retardo += 1
        if self.retardo > self.max_retardo:
            self.retardo > self.max_retardo

    def minimizar_retardos(self):
        self.retardo=5
                            

    
    def tiempo_espera_error(self,txt_error):
        tiempo=random.randint(27, 30)
        if 'Too much request weight used' in txt_error:
            tiempo=random.randint(60, 120)

        if 'ECONNRESET' in txt_error:
            tiempo=random.randint(70, 150)    

        return tiempo    

    def carga_de_actualizacion_escala(self,par,escala,hora_ini):

        klines = None
        self.errores=0
        self.retardo=0
        ahora=time.time()
        intentos=50

        rango_fin=int(ahora * 1000  )
        rango_ini= hora_ini

        
        
        while self.g.trabajando: #21/01/2020 eliminé ----->intentos>0 and  porque no se puede avanzar si no se actualiza
            
            self.operacion_empezar(par+'_' + escala  + '_a_')
            
            klines= None
            err=False
            try: 

                if self.retardo >0: 
                    self.log.err( f'inicio carga_de_actualizacion_escala {escala} {par}' )

                if escala=='1m':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1MINUTE, rango_ini,rango_fin) 
                elif escala=='3m':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_3MINUTE, rango_ini,rango_fin) 
                elif escala=='5m':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_5MINUTE, rango_ini,rango_fin) 
                elif escala=='15m':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_15MINUTE, rango_ini,rango_fin) 
                elif escala=='30m':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_30MINUTE, rango_ini,rango_fin) 
                elif escala=='1h':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1HOUR, rango_ini,rango_fin ) 
                elif escala=='2h':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_2HOUR, rango_ini,rango_fin )     
                elif escala=='4h':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_4HOUR, rango_ini,rango_fin ) 
                elif escala=='1d':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1DAY, rango_ini,rango_fin)
                elif escala=='1w':
                    klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1WEEK, rango_ini,rango_fin) 
                elif escala=='1M':
                    klines=self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1MONTH, rango_ini,rango_fin)     

                #valido set_velas_web
                if type(klines) is list:
                    if len(klines)>0:
                        pass
                else:
                    err=True

                if self.retardo >0: 
                    self.log.err( "fin carga_de_actualizacion_escala(",escala,")")    
                
            except Exception as e:
                #self.log.log( e  )
                txt_error = str(e)
                tiempo_espera=self.tiempo_espera_error(txt_error)
                #tb = traceback.format_exc()
                #self.log.log( tb)
                #self.log.log('klines',klines,par,rango_pedido,rango_ini,rango_fin)
                err=True
                
                self.inc_retardo()
                #self.crear_cliente() #boora y crea un nuevo cliente
                self.log.err( "...Error actualización",par,"._escala(",escala,") ---Err:",txt_error)

              
            intentos-=1 
            
            self.operacion_terminar()   

            if err:
                self.log.err( 'Retardo--->',self.retardo)
                #self.crear_cliente()
                time.sleep(tiempo_espera)
                
            else:
                break # toso ha salido bien, etamos actualizados, dejamos de intentar
        return klines    
        
    
