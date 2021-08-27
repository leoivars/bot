# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

import talib
from velaset import VelaSet
from vela import Vela
# from vela import *
# from binance.client import Client #para el cliente
# from binance.enums import * #para  create_order
from binance.client import Client
from binance.websockets import BinanceSocketManager



import time
import random
import numpy as np

import traceback
from datetime import datetime
from market_profile import MarketProfile
import pandas as pd
import pandas_ta as ta

from  variables_globales import VariablesEstado

from cola_de_uso import Cola_de_uso

from funciones_utiles import variacion,compara,signo



class Indicadores:
    
    operando = False
    escala_siguiente   ={'1m':'5m','5m':'15m','15m':'30m','30m':'1h','1h':'2h','2h':'4h','4h':'1d','1d':'1w','1w':'1M'}
    tiempo_actualizar  ={'1m':30,  '5m':90,   '15m':100,  '30m':110, '1h':120, '2h':150, '4h':120, '1d':600, '1w':600,'1M':600}
    var_velas          ={'1m':5,   '5m':7,    '15m':9,    '30m':11,  '1h':13,  '2h':15,  '4h':17,  '1d':19,  '1w':30,' 1M':50}
    var_velas_seguidas ={'1m':9,   '5m':11,   '15m':13,   '30m':15  ,'1h':17,  '2h':19,  '4h':21,  '1d':27,  '1w':30, '1M':70}
    #var_velas_seguidas ={'1m':1,   '5m':2,    '15m':3,    '30m':7  , '1h':8,   '2h':9,   '4h':12,  '1d':20, '1w':30,'1M':60}


    fibo=[76.4,61.8,50,38.2,21.4,0]
    
    #
    #semaforo=Semaphore(30) #cantidad de requests al mismo tiempo

    #variables para contar requests/minute
    crequests=0

    cerrores=0 #igual que crquests
    
    minute = time.time()
    
        
    def __init__(self,par,log,estado_general,cliente):
        pd.set_option('mode.chained_assignment', None)
        self.bm = BinanceSocketManager(client)

        self.actualizado={'1m':0,'5m':0,'15m':0,'30m':0,'1h':0,'2h':0,'4h':0,'1d':0,'1w':0,'1M':0}
        self.g:VariablesEstado = estado_general
        self.velas={}
        for k in self.actualizado:
            self.velas[k]=None
        
        
        self.par=par
        self.log=log
        self.retardo=5
        self.errores=0
        self.tiempo_actualizacion=25
        self.incremento_volumen_bueno=1.5
        
        self.client = cliente
        
        #self.lock_actualizador= Lock()
        self.prioridad = 0
        self.cola = Cola_de_uso(log,estado_general)

    def init_sockets
    

    #def __del__(self):
    #    for k in self.actualizado:
    #        self.velas[k]=None
    #    del self.velas
    #    del self.client
    #    del self.log
    #    del self.actualizado
     
    
    
    def operacion_empezar(self,referencia):
        #self.log.log('Waiting for lock')
        #print ('...acquire'+self.par)
        #Indicadores.semaforo.acquire()

        self.cola.acceso_pedir(referencia,self.prioridad)
        self.cola.acceso_esperar_mi_turno()
        

        self.__inicio_ocupando_turno = time.time()
        #self.regulador_requests_minute()

        #log de la cola
        #lin='SOY:__' +self.par+'COLA:\n'
        #for c in Indicadores.cola:
        #    lin += c +'\n'
        #self.log.log(lin)   
        pedcola = self.cola.largo()
        if pedcola > 120:
            self.log.log('Pedidos en cola =',  pedcola,'demora_promedio',self.cola.demora_de_cola() ) 

        if self.retardo > 0 and self.errores > 10: #debug solo cuando hay mucho errores
            self.log.err('--operacion_empezar--------------->',self.par, 'self.crequests,errores,errores/minuto',Indicadores.crequests,self.errores,Indicadores.cerrores)
            #self.log.err('ERROR MUY FEO! acceso_finalizar_turno: ',self.ticket_acceso)    
        
    def operacion_terminar(self):
        #control de rendimiento
        demora=time.time() - self.__inicio_ocupando_turno
        if demora > self.cola.demora_promedio * 10:
            self.log.err('DEMORA!=',round(demora,4), 'ticket', self.cola.ticket_acceso,'cola',self.cola.largo(),'demora_promedio',self.cola.demora_de_cola() )
            
              
        self.cola.acceso_finalizar_turno(demora)
        #self.regulador_requests_minute()# hace una demora dinámica dependiendo de la cantidad de errores que se estén registrando 
        
        # demora=int(Indicadores.crequests / 30)
        # if demora >0 and self.retardo == 0: #solamente demora cuando no hay retardos porque en ese caso ya hizo una buen pausa
        #     time.sleep(demora)
        

    
    def regulador_requests_minute(self): 
        #Indicadores.lock_rqm.acquire()
        #xrint( '------------------------------------rqm---errm---cola---demora_prom---->',Indicadores.crequests,Indicadores.cerrores,self.cola.largo())

        if Indicadores.cerrores > 0: 
            time.sleep(Indicadores.cerrores * 0.125)
        elif Indicadores.crequests > 90:
            time.sleep(0.125)    

        if Indicadores.crequests < 1200 and time.time() - Indicadores.minute < 110: 
            Indicadores.crequests += 1
        else:
            while time.time() - Indicadores.minute < 150:
                time.sleep(0.1)
            Indicadores.minute = time.time()    
            
            if Indicadores.crequests > 50:
                restar = 1
            else:    
                restar = 5

            Indicadores.crequests = 1     

            if Indicadores.cerrores >= restar:
                Indicadores.cerrores -= restar
        
        #Indicadores.lock_rqm.release()
        
        
    def dec_retardo(self):
        self.retardo-=1
        if self.retardo<0: 
            self.retardo=0
            self.tiempo_actualizacion-=1
            if self.tiempo_actualizacion<=17:
                self.tiempo_actualizacion=17
        self.errores-=1
        if self.errores<0:
           self.errores=0         

    def inc_retardo(self):
        
        max_retardo=15
        max_actualizacion=65
        
        Indicadores.cerrores += 1
        self.errores += 1
        self.retardo += 1
        if self.retardo>max_retardo:
            self.retardo=max_retardo
            self.tiempo_actualizacion+=1
            if self.tiempo_actualizacion>max_actualizacion:
                self.tiempo_actualizacion=max_actualizacion

    def minimizar_retardos(self):
        self.retardo=5
        self.tiempo_actualizacion=17                        

    def cargainicial(self,escala):
        #self.log.log( "cargainicial(",escala,")", self.par )
        #print 'cargainicial',self.par,escala
        
        self.errores=0
        self.retardo=0
        
        ahora=time.time()
        
        
        # configuro el intervalo y la cantidad de velas que necesito para cada uno de ellos
        rango_fin=int(ahora * 1000  )
        
        if escala=='1m':
            cvel=200
            ch=int(cvel/60)+1 #60 velas por hora
            rango_pedido = str(ch)+" hour ago UTC"
            intervalo = Client.KLINE_INTERVAL_1MINUTE
        elif escala=='5m':
            cvel=200
            ch=int(cvel/12)+1 #12 velas por hora
            rango_pedido = str(ch)+" hour ago UTC"
            intervalo = Client.KLINE_INTERVAL_5MINUTE
        elif escala=='15m':
            cvel=200
            cd=int(cvel/96)+1 #96 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_15MINUTE
        elif escala=='30m':
            cvel=200
            cd=int(cvel/96/2)+1 #96/2 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_30MINUTE
        elif escala=='1h':
            cvel=200
            cd=int(cvel/24)+1 #24 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1HOUR
        elif escala=='2h':
            cvel=200
            cd=int(cvel/12)+1 #12 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_2HOUR
        elif escala=='4h':
            cvel=255
            cd=int(cvel/6)+1 #6 velas por dia
            rango_pedido = str(cd)+" day ago UTC"
            intervalo = Client.KLINE_INTERVAL_4HOUR
        elif escala=='1d':
            cvel=180
            rango_pedido = "180 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1DAY
        elif escala=='1w':
            cvel=200
            rango_pedido = "399 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1WEEK
        elif escala=='1M':
            cvel=48
            rango_pedido =  "1460 day ago UTC"
            intervalo = Client.KLINE_INTERVAL_1MONTH

        rango_ini=int(  ahora - self.g.escala_tiempo[escala] * cvel)    * 1000 

        while self.g.trabajando: # and self.actualizado[escala] >0:  #21/01/2020 eliminé ----->intentos>0 and  porque no se puede avanzar si no se actualiza
            self.operacion_empezar(self.par+'_'+escala + '_i_')    
            err=False 
            
            try:
                if self.retardo >0: 
                    self.log.err( "inicio cargainicial(",self.par, escala , intervalo,  rango_ini,rango_fin,")")

                klines = None
                klines =self.client.get_historical_klines(self.par, intervalo,  rango_ini, rango_fin) # para carga inicial

                if klines != None:
                    self.velas[escala]=VelaSet(klines,cvel)    
                    self.actualizado[escala]=ahora
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
                self.log.log('klines',klines,self.par,rango_pedido)
                err=True
                tiempo_espara=self.tiempo_espera_error(txt_error)
                self.actualizado[escala]=0
                self.inc_retardo()
                #self.crear_cliente() #boora y crea un nuevo cliente
                
                self.log.err( "....Error en cargainicial(",escala,"), rango (",rango_pedido,") , reintento en" ,self.retardo,'rqm,errm',Indicadores.crequests,Indicadores.cerrores, txt_error)
                    

            self.operacion_terminar() #libero el semáforo     
            
            if err:#=True 
                #self.prioridad=0
                self.log.err( 'Retardo--->',self.retardo,'rqm,errm',Indicadores.crequests,Indicadores.cerrores)  
                #self.crear_cliente()
                time.sleep(tiempo_espara) # espero en caso de errors
                
            else:
                
                break    
         
        #print (self.velas[escala])

    def tiempo_espera_error(self,txt_error):
        tiempo=random.randint(27, 30)
        if 'Too much request weight used' in txt_error:
            tiempo=random.randint(60, 120)

        if 'ECONNRESET' in txt_error:
            tiempo=random.randint(70, 150)    


        return tiempo    

    def carga_de_actualizacion_escala(self,escala):

        self.errores=0
        self.retardo=0
        ahora=time.time()
        intentos=50

        #print ('carga de actualizacion',ahora-self.actualizado[escala],self.tiempo_actualizacion)
        
        while ahora-self.actualizado[escala] > self.tiempo_actualizacion and self.g.trabajando: #21/01/2020 eliminé ----->intentos>0 and  porque no se puede avanzar si no se actualiza
            
            self.operacion_empezar(self.par+'_' + escala  + '_a_')
            
            klines= None
            err=False
            try: 

                if self.retardo >0: 
                    self.log.err( "inicio carga_de_actualizacion_escala(",escala,")")

                minutos_desactualizado=int((ahora-self.actualizado[escala])/60) # tiempo en minutos

                rango_fin=int(ahora * 1000  )
                rango_ini=int(  self.actualizado[escala] - self.g.escala_tiempo[escala])    * 1000 
                if escala=='1m':
                    t= 1 * minutos_desactualizado + 2
                    rango_pedido = str(t)+' minute ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1MINUTE, str(t)+' minute ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1MINUTE, rango_ini,rango_fin) 
                elif escala=='5m':
                    
                    t= int(minutos_desactualizado/5)  + 10
                    rango_pedido = str(t)+' minute ago UTC'

                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_5MINUTE, str(t)+' minute ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_5MINUTE, rango_ini,rango_fin) 
                elif escala=='15m':
                    t=int(minutos_desactualizado/15) + 30
                    rango_pedido = str(t)+' minute ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_15MINUTE, str(t)+' minute ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_15MINUTE, rango_ini,rango_fin) 

                elif escala=='30m':
                    t=int(minutos_desactualizado/30) + 60 
                    rango_pedido = str(t)+' minute ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_15MINUTE, str(t)+' minute ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_30MINUTE, rango_ini,rango_fin) 
                
                elif escala=='1h':
                    t=int(minutos_desactualizado/60)  + 2
                    rango_pedido = str(t)+' hour ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1HOUR, str(t)+' hour ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1HOUR, rango_ini,rango_fin ) 
                elif escala=='2h':
                    t=int(minutos_desactualizado/60)  + 4
                    rango_pedido = str(t)+' hour ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1HOUR, str(t)+' hour ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_2HOUR, rango_ini,rango_fin )     
                elif escala=='4h':
                    #t=int((tiempo_desactualizado/60)/4) * 4 + 12
                    t=int(minutos_desactualizado/60) + 8
                    rango_pedido = str(t)+' hour ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_4HOUR, str(t)+' day ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_4HOUR, rango_ini,rango_fin ) 
                elif escala=='1d':
                    t=int((minutos_desactualizado/60)/24)  + 2
                    rango_pedido = str(t)+' day ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1DAY, str(t)+' day ago UTC')
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1DAY, rango_ini,rango_fin)
                elif escala=='1w':
                    t=int(((minutos_desactualizado/60)/24)/7) + 14
                    rango_pedido = str(t)+' day ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1WEEK, str(t)+' day ago UTC') 
                    klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1WEEK, rango_ini,rango_fin) 
                elif escala=='1M':
                    t=int(((minutos_desactualizado/60)/24)/30)  + 60
                    rango_pedido = str(t)+' day ago UTC'
                    #klines =self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1WEEK, str(t)+' day ago UTC') 
                    klines=self.client.get_historical_klines(self.par, Client.KLINE_INTERVAL_1MONTH, rango_ini,rango_fin)     
                

                #valido set_velas_web
                if type(klines) is list:
                    if len(klines)>0:
                        self.velas[escala].actualizar(klines)
                        self.actualizado[escala]=ahora
                        self.dec_retardo()
                        del klines
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
                #self.log.log('klines',klines,self.par,rango_pedido,rango_ini,rango_fin)
                err=True
                
                self.actualizado[escala]=0
                self.inc_retardo()
                #self.crear_cliente() #boora y crea un nuevo cliente
                self.log.err( "...Error actualización",self.par,"._escala(",escala,"), rango(",rango_pedido,"), r.",self.retardo,"seg.",'rqm,errm',Indicadores.crequests,Indicadores.cerrores,"---Err:",txt_error)

              
            intentos-=1 
            
            self.operacion_terminar()   

            if err:
                self.log.err( 'Retardo--->',self.retardo)
                #self.crear_cliente()
                time.sleep(tiempo_espera)
                
            else:
                break # toso ha salido bien, etamos actualizados, dejamos de intentar
        
    def actualizar_velas(self,escala):
        difftime = time.time()-self.actualizado[escala]
        
        if self.actualizado[escala]==0 or difftime > 709200: #nunca cargado o pasó mas de 60" * 60 * 197
            self.actualizar_completamete(escala)
        
        elif difftime>self.tiempo_actualizar[escala]: #actualizo
            self.actualizar_parcialmente(escala)

    def actualizar_parcialmente(self,escala):
        ini=time.time()
        #self.lock_actualizador.acquire()
        
        if time.time() - ini > 2: #si se demoró mucho vuelvo a consultar la actualizacion por que es posible que ya haya sido actualizada
            difftime = time.time()-self.actualizado[escala]
            if difftime>self.tiempo_actualizar[escala]:
                self.carga_de_actualizacion_escala(escala)
        else:
            self.carga_de_actualizacion_escala(escala)        
        
        #self.lock_actualizador.release()        

    def actualizar_completamete(self,escala):
    
        ini=time.time()
        #self.lock_actualizador.acquire()
        
        if time.time() - ini > 2: #si se demoró mucho vuelvo a consultar la actualizacion por que es posible que ya haya sido actualizada
            difftime = time.time()-self.actualizado[escala]
            if self.actualizado[escala]==0 or difftime > 709200:
                self.cargainicial(escala)
        else:
            self.cargainicial(escala)

        #self.lock_actualizador.release()        






        
        

    def get_vector_np_open(self,escala):
        return self.velas[escala].valores_np_open()

    def get_vector_np_close(self,escala):
        return self.velas[escala].valores_np_close()

    

    def get_vector_np_high(self,escala):
        return self.velas[escala].valores_np_high()

    def get_vector_np_low(self,escala):
        return self.velas[escala].valores_np_low()

    def get_vector_np_volume(self,escala):
        return self.velas[escala].valores_np_volume()    


    def hay_vela_corpulenta_cerca(self,escala,coeficiente):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_cuerpo()
        avg=np.average(vector)
        l=vector.size

        ret=False

        v3=round(vector[l-3]/avg ,2)
        v2=round(vector[l-2]/avg ,2)
        v1=round(vector[l-1]/avg ,2)

        if v1>coeficiente or v2>coeficiente or v3>coeficiente:
            ret= True
        
        return [ ret , avg , v3, v2, v1]

    def analisis_BB_inferior(self,escala,cant_velas):
        self.actualizar_velas(escala)
        vc=self.velas[escala].valores_np_close() #vector close
        vo=self.velas[escala].valores_np_open()  #vector open
        bs, bm, bi = talib.BBANDS(vc, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        l=vc.size
        if cant_velas>l:
           c=l
        else:
           c=cant_velas   

        salida=[]

        
        #print ("l,c",l,c,l-c,l-1) 

        for i in range(l-c,l): #recorrido desde el ultimo elemento, el mas atual, al mas viejo
           # print ("i,",i)
            if vo[i]<vc[i]: #vela alsista
                if vo[i]>=bi[i]:  #abre y cierra por encima de la banda inferior
                    salida.append( 3)
                elif vo[i]<=bi[i] and vc[i] >=bi[i]:  #la vela abre abajo de la bi (banda inferior) y cierra encima de la bi
                    salida.append( 2)
                elif vc[i]<=bi[i]:  #la vela abre y cierra por debajo  abajo de la bi (banda inferior)
                    salida.append( 1)
                else:
                    salida.append( 0)   

            else: #vela bajista
                if vc[i] >= bi[i]:  #abre y cierra por encima de la banda inferior
                    salida.append( -1)
                elif vo[i]>=bi[i] and vc[i] <=bi[i]:  #la vela abre encima de bi y cierra debajo de bi
                    salida.append( -2)
                elif vo[i]<=bi[i]:  #labre y cierra por bajo de la banda inferior
                    salida.append( -3)
                else:
                    salida.append( 0)         

        return salida            
    

    
    # la idea de este indicador es calcular el minimo y el maximo en un cierta cantidad de velas
    # y la relacion con el precio actual, o sea desde la ultima vela hacia atras.
    # lo que se pretende es establecer un precio y un porcentaje hacia el precio minimo 
    # lo mismo para maximo
    # para tratar de determinar cuando sería una toma de ganancia o perdidas.
    def minmax(self,escala,periodos):
        self.actualizar_velas(escala)
        vmax=self.velas[escala].valores_np_high()
        vmin=self.velas[escala].valores_np_low()
        precio=self.velas[escala].ultima_vela().close
        l=vmax.size


        if periodos>l-1:
            p=l-1
        else:
            p=periodos

        min=vmin[l-1]
        max=vmax[l-1]

        for i in range(l-p,l):
            #print (min,vmin[i],max,vmax[i])
            if vmin[i]<min:
                min=vmin[i]
            
            if vmax[i]>max:
                max=vmax[i]
        
        pmax=round((1-max/precio)*100,2)
        pmin=round((1-min/precio)*100,2)

        return [min,max,pmin,pmax]


    def logvelas(self,escala,periodos):
        self.actualizar_velas(escala)
        l=len(self.velas[escala].df)

        if periodos>l-1:
            p=l-1
        else:
            p=periodos

        for i in range(l-p,l):
            v=self.velas[escala].get_vela(i)

            self.log.log(i, v.open, v.high, v.low, v.close, v.volume, v.open_time, v.close_time)




    def adosc(self,escala): 
        
        self.actualizar_velas(escala)

        high  = self.get_vector_np_high(escala)
        low   = self.get_vector_np_low(escala)
        close = self.get_vector_np_close(escala)
        volume= self.get_vector_np_volume(escala)

        ret =  talib.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
        l=ret.size
        return [ret[l-2],ret[l-1]]


    def tendencia_adx(self,escala,per_rapida=10,per_lenta=55,c=None,h=None,l=None):
        '''
         evalua la tendencia y el adx retornando los siguientes valores
          5 ascendente con mucha fuerza
          4 ascendente con fuerza
          3 ascendente sin fuerza pero creciendo el interés
          2 ascendente con fuerza y perdinedo interé
          1 ascendente sin fuerza y perdiendo el interes
         -1 bajista , sin fuerza y perdiendo fuerza (adx hacia abajo)
         -2 bajista , con fuerza pero perdiendo fuerza (adx hacia abajo)
         -3 bajista , sin fuerza y fuerza creciente (adx hacia hacia arriba)
         -4 bajista , con fuerza y creciendo

        '''
        if c is None:
            self.actualizar_velas(escala)
            c=self.get_vector_np_close(escala)
            h=self.get_vector_np_high(escala)
            l=self.get_vector_np_low(escala)
        emar=talib.EMA(c , timeperiod=per_rapida)
        emal=talib.EMA(c , timeperiod=per_lenta)
        adx = self.adx(escala,c,h,l)
        #print(adx)
        ret=0
        confirmacion_adx = self.g.confirmacion_adx
        if emar[-1] > emal[-1]: #alcista
            if adx[1]>0: #pendiente positiva
                if adx[0] >= confirmacion_adx:
                    if adx[0] >= confirmacion_adx * 1.1:
                        ret=5 # hay mucha fuerza
                    else:
                        ret=4 # hay fuerza
                else:
                    ret=3 # está creciendo el interés pero no hay fuerza
            else:
                if adx[0] >= confirmacion_adx: 
                    ret=2 # hay fuerza pero se está perdiendo el interés
                else:
                    ret=1 # no hay fuerza y se está perdiendo el interés
        else: #bajista
            if adx[1]>0:
                if adx[0] >= confirmacion_adx:
                    ret=-4
                else:
                    ret=-3
            else:
                if adx[0] >= confirmacion_adx:
                    ret=-2
                else:
                    ret=-1

        return ret            




    def situacion_adx_macd(self,escala):
        ''' Evalua la situación del adx con el macd
            si hist-,pend+ adx- y menor a 23 ----> 2 --> rango o caída pero  ya sin fuerza y recuperando 
            si hist+,pend+ adx+ y mayor=23 ------> 1 --> subiendo con fuerza
            cual quier otro caso 0 ----> no comprar
        '''
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)
    
        _, _, hist = talib.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)
        dhist = self.macd_describir(escala,hist)
        adx = self.adx(escala,c,h,l)

        ret = 0

        if dhist[1] == 1: # la pendiente debe ser positiva en ambos casos
            if dhist[0] == -1  and adx[1] < 0 and adx[0] < 23:
                ret = 2
            elif dhist[0] == 1 and adx[1] > 0 and adx[0] >= 23:
                ret = 1    

        return  ret

    def situacion_adx_macd_rango_caida(self,escala):
        ''' Evalua la situación del pendiete/adx con el macd
           ---> rango o caída  --> True
            sino retorna False
            
        '''
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)

        tadx = self.tendencia_adx(escala,9,55,c,h,l) 
        if  tadx < 3:
            _, _, hist = talib.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)
            dhist = self.macd_describir(escala,hist)
            ret = dhist[0] == -1 and dhist[1] == 1 
        else:
            ret = False    
        
        return ret


    def adx(self,escala,close=None,high=None,low=None):
        if close is None or high is None or low is None:
            self.actualizar_velas(escala)
            c=self.get_vector_np_close(escala)
            h=self.get_vector_np_high(escala)
            l=self.get_vector_np_low(escala)
        else:
            c = close
            h = high
            l = low    

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size

        
        try:
            radx=round(vadx[l-1],2)
            m01= round( vadx[l-1] - vadx[l-2] ,2 ) 
            m02= round( vadx[l-2] - vadx[l-3] ,2 )
            m03= round( vadx[l-3] - vadx[l-4] ,2 )
            m04= round( vadx[l-4] - vadx[l-5] ,2 )
        except:
            radx=0
            m01=-1
            m02=-1
            m03=-1
            m04=-1

        
        return [radx,m01,m02,m03,m04]

    def rsi_minimo(self,escala,close=None):
        ''' retorna el rsi minimo local y el rsi actual
        '''
        if close is None:
            self.actualizar_velas(escala)
            c = self.get_vector_np_close(escala)
        else:
            c = close

        rsi=talib.RSI( c , timeperiod=14)
        
        minimo = 100
        l=rsi.size
        mi = 0
        
        
        i=-1
        lneg = l * -1
        try:
            if rsi[-2] < rsi[-1]:
                while i > lneg:
                    if rsi[i-1] > rsi[i]:
                        mi = i
                        break
                    i -= 1

                if mi < 0:
                    minimo = rsi[mi]    
    
        except Exception as e:
            self.log.log(str(e))  

        return minimo,rsi[-1]  # si no ecuetra minimo retorna 100 que es un valor seguro para la toma de desiciones que se pretende tomar con esta funcion      



    def adx_negativo(self,escala,close=None,high=None,low=None):
        ''' retorna una lista con
            [0] = True si es negativa la pendiente del adx
            [1] el pico negativo del adx
            [2] el valor actual del adx
        '''
        if close is None or high is None or low is None:
            self.actualizar_velas(escala)
            c=self.get_vector_np_close(escala)
            h=self.get_vector_np_high(escala)
            l=self.get_vector_np_low(escala)
        else:
            c = close
            h = high
            l = low    

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size
        lneg = l * -1

        pico = 0
        padx = -1
        
        negativo = False
         
        try: 

            if vadx[-2] > vadx[-1]: #hay pendiente negativa
                negativo = True
                #busco cual fue el pico
                i=-2
                while i > lneg:
                    if vadx[i-1] < vadx[i]:
                        pico = i
                        break
                    i -= 1

            if pico < 0: #encontró el pico 
                padx = vadx[pico]   
        except Exception as e:
            self.log.log(str(e)) 

    
        return [negativo,padx,vadx[-1]]           

            


        
        try:
            radx=round(vadx[l-1],2)
            m01= round( vadx[l-1] - vadx[l-2] ,2 ) 
            m02= round( vadx[l-2] - vadx[l-3] ,2 )
            m03= round( vadx[l-3] - vadx[l-4] ,2 )
            m04= round( vadx[l-4] - vadx[l-5] ,2 )
        except:
            radx=0
            m01=-1
            m02=-1
            m03=-1
            m04=-1

        
        return [radx,m01,m02,m03,m04]    
    
    
        



    def adx_mr(self,escala):
        '''
        Es casi lo mismo que adx per las pendienteas con relativas a la ultima vela
        '''
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size

        
        try:
            radx=round(vadx[l-1],2)
            m01= round( vadx[l-1] - vadx[l-2] ,2 ) 
            m02= round( (vadx[l-1] - vadx[l-3])/2 ,2 )
            m03= round( (vadx[l-1] - vadx[l-4])/3 ,2 )
            m04= round( (vadx[l-1] - vadx[l-5])/4 ,2 )
        except:
            radx=0
            m01=-1
            m02=-1
            m03=-1
            m04=-1

        return [radx,m01,m02,m03,m04]


    def sar(self,escala):
        self.actualizar_velas(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)
        vsar=talib.SAR(h,l, acceleration=0.02, maximum=0.2)
        l=vsar.size

        return float(vsar[l-1]) # -2 es la ultima vela cerrada -1 vela en desarrollo 


    
    def macd(self,escala):
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        
        r_macd, r_macdsignal, r_macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        l=len(r_macd)-1
        
        return [r_macd[l], r_macdsignal[l], r_macdhist[l]]

    def macd_analisis(self,escala,cvelas):
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        
        senial=0
        p=-1
        for u in range(l-1,l-cvelas,-1):
            #print (u,hist[u-1], hist[u])
            if hist[u]==0 or hist[u-1]<0 and hist[u]>0: #histograma positivo y creciente
                if mac[u]>=sig[u]:
                    for i in range(u-1, u-5, -1): 
                        if mac[i] < sig[i] and mac[u]>mac[i]:
                            #deteccion de cruce positivo
                            senial=1
                            p=l-u-1
                            break
            elif hist[u]==0 or hist[u-1]>0 and hist[u]<0: #histograma negativo y decreciente
                if mac[u]<=sig[u]:
                    for i in range(u-1, u-5, -1): 
                        if mac[i] > sig[i] and mac[u] < mac[i]:
                            #deteccion de cruce negativo, señar de salida
                            senial=-1
                            p=l-u-1
                            break
            if senial !=0:
                break 
        
        #analisis del histotrama para detectar si pasa por el punto cero
        senial_hist=0
        psenial_hist=-1
        for u in range(l-2,l-cvelas,-1): 
            if hist[u-1] == 0:
                senial_hist=1
                psenial_hist = l - u - 2
                break
            elif hist[u-1] > 0  and hist[u] <0:
                senial_hist=3
                psenial_hist = l - u - 1
                break
            elif hist[u-1] < 0 and  hist[u] > 0:
                senial_hist=2
                psenial_hist = l - u - 1
                break

        #si hay señal devuelvo el histograma
        #if senial==0: #no se encontró un cruce
        #    h=-9999
        #else:
        #    h=hist[u]  

        #pendiente de 
        #m00=  mac[l-1]-mac[l-2]     #aca iria /1 pero es al pedo dividir por 1
        #mp2= (mac[l-1]-mac[l-int(cvelas/2)])/7 # vela intermedia
        #mpp= (mac[l-1]-mac[l-14])/14

        mhist=  hist[l-1]-hist[l-2]     #aca iria /1 pero es al pedo dividir por 1        
        



        return [senial,p,hist[l-1],mhist,senial_hist,psenial_hist]                        


    def retroceso_macd_hist_max(self,escala):
        ''' en la escala seleccionada retorna un precio entre el precio
        desde que el histograma =0 hasta que el histograma toma su valor máximo '''

        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        px=0

        #1) busco maximo historial de macd
        imax=-1
        for i in range(l-1,1,-1):
            
            if hist[i-1] <  hist[i]  and hist[i-1] >0 and  hist[i] >0 : #estamos en bajada, seguimos
                imax = i
                break
        
        if imax > -1:
            icero = - 1

            #2) busco la primer vela positiva
            for i in range(imax,1, -1):
                
                if hist[i-1] <0 and  hist[i]>=0:
                    icero=i
                    break
  
            px =  close[icero] + ( close[imax] - close[icero] ) *.5

        return px    

    def divergenica_macd(self,escala):
        ''' busca divergencias en el macd '''

        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        i= l - 1
        
        ipos=[]
        zona_signo= 1 if hist[i] > 0 else -1
        signo_hist= zona_signo * -1 # si entoy en positivo busco negativo y si estoy en negativo, busco positivo
        max = 0
        imax= -1
        cambios = 0
        while i > -1:
            signo = 1 if hist[i] > 0 else -1 
            
            if signo == zona_signo:#cambio de signo
                if signo_hist and signo: #sigo en la misma zona
                    if signo == 1:
                        if hist[i] > max:
                            max = hist[i]
                            imax = i
                    else:
                        if hist[i] < max:
                            max = hist[i]
                            imax = i
            else:
                
                if signo_hist == zona_signo:
                    ipos.append(imax)
                
                zona_signo = signo
                imax=i
                max=hist[i]
            
            if len(ipos)==2:
                break    
            i -= 1

       # print ('ipos',ipos)
        div = 0
        if len(ipos)==2:
            a = ipos[1]
            b = ipos[0]
           # print (l-b,l-a)
            if signo_hist: # signo positivo
                if hist[a] > hist[b] and close[a] < close[b]:
                    div = -1 #divergencia bajista
                elif hist[a] < hist[b] and close[a] >= close[b]:
                    div = 1
            else: # signo negativo
                if hist[a] < hist[b] and close[a] >= close[b]:
                    div = 1 
                elif hist[a] > hist[b] and close[a] < close[b]:
                    div = -1  

        print (signo_hist)
        return div            

    def busca_pico_loma_hist(self,hist,high,low,psigno_loma,principio,velas_minimas_de_la_loma=5):
        ''' Busca la posición de la prime loma del histograma del macd que cumpla con el sigo + o - según psigno_loma y que tenga
            al menos la cantidad de velas especificadas en  velas_minimas_de_la_loma de al principio hacia la izquierda ( a cero)
        '''
        ret = -1
        ret_principio= -1
        
        i = principio

        while i >=0:
            tam,signo_loma,principio,pxpico = self.propiedades_macd_loma(hist,high,low,i)
            if tam >= velas_minimas_de_la_loma and signo_loma == psigno_loma:
                ret = pxpico
                ret_principio = principio
                break
            else:
                i = principio - 1
        
        return ret,ret_principio 

    def busca_pico_loma_hist_ema(self,hist,ema,psigno_loma,principio,velas_minimas_de_la_loma=5):
        ''' Busca la posición de la prime loma del histograma del macd que cumpla con el sigo + o - según psigno_loma y que tenga
            al menos la cantidad de velas especificadas en  velas_minimas_de_la_loma de al principio hacia la izquierda ( a cero)
        '''
        ret = -1
        ret_principio= -1
        
        i = principio

        while i >=0:
            tam,signo_loma,principio,pxpico = self.propiedades_macd_loma_ema(hist,ema,i)
            if tam >= velas_minimas_de_la_loma and signo_loma == psigno_loma:
                ret = pxpico
                ret_principio = principio
                break
            else:
                i = principio - 1
        
        return ret,ret_principio


    def propiedades_macd_loma_ema(self,hist,ema,p):
        ''' retorna el tamaño y el principio de una loma '''

        principio,final = self.busca_princpipio_y_final_loma(hist,p)
        signo_loma = signo( hist[p] )
                
        #busca px maximo o minimo de la loma
        #para conseguir su posicion
        pxpico  = ema[principio]
        
        for i in range(principio,final+1):
            if signo_loma == 1:
                if pxpico < ema[i]:
                    pxpico = ema[i]
                    #ipxpico = i
            else:
                if pxpico > ema[i]:
                    pxpico = ema[i]
                    #ipxpico = i

        tam = final - principio + 1
 
        
        return tam,signo_loma,principio,pxpico

    
    def propiedades_macd_loma(self,hist,high,low,p):
        ''' retorna el tamaño y el principio de una loma '''

        principio,final = self.busca_princpipio_y_final_loma(hist,p)
        signo_loma = signo( hist[p] )
                
        #busca px maximo o minimo de la loma
        #para conseguir su posicion
        if signo_loma == 1:
            pxpico  = high[principio]
        else:
            pxpico  = low[principio]
        #ipxpico  = principio    

        for i in range(principio,final+1):
            if signo_loma == 1:
                if pxpico < high[i]:
                    pxpico = high[i]
                    #ipxpico = i
            else:
                if pxpico > low[i]:
                    pxpico = low[i]
                    #ipxpico = i



        tam = final - principio + 1
 
        
        return tam,signo_loma,principio,pxpico


    def busca_princpipio_y_final_loma(self,hist,posicion_loma):
        signo_loma = signo( hist[posicion_loma] )
        #busco final de la loma 
        i = posicion_loma
        l = len(hist)
        while i < l:
            if signo(hist[i]) == signo_loma:
                final = i
            else:
                break   
            i += 1
            
        #busco el principio    
        i = posicion_loma
        while i >= 0:
            if signo(hist[i]) == signo_loma:
                principio = i
            else:
                break   
            i -= 1
        
        return principio, final    

    def promedio_bajos_macd(self,escala):
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        _, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.get_vector_np_low(escala)
        ultimo = len(low)-1
        principio,final = self.busca_princpipio_y_final_loma(hist,ultimo)

        subset = low[principio:final+1]
        vector_emas  = talib.EMA(subset, timeperiod=3)
        ret =  vector_emas[-1] 

        #si no se pudiera calcular la ema, se toma el valor mas chico del rango
        if np.isnan(ret):
            #print('ema',ret)
            top = int(len(subset)/5)
            if top == 0:
                top=1
            subset[::1].sort() 
            ret = np.average(subset[ 0 : top+1 ] )

        return float( ret)   

    def buscar_escala_con_rango_o_caida_macd(self,escala):
        ''' empieza por la escala  y si encuentra rango o caída retorna esa escala 
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de 1m '''
        esc = escala
        while esc != "1m": # si llega a 1m  la retorna
            if self.situacion_adx_macd_rango_caida(esc): 
                break
            else:
                esc = self.g.escala_anterior[esc]
        
        return esc 

    def buscar_subescala_con_tendencia(self,escala,per_rapida=10,per_lenta=55):
        ''' empieza por la escala  y si encuentra tendencia   retorna esa escala
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de 1m '''
        esc = self.g.escala_anterior[escala]
        escala_tope="5m"
        while esc != escala_tope: # solo busca hasta escala_tope
            if self.tendencia_adx(esc,per_rapida,per_lenta) >=3 :  #3 tendendia 4 tendencia confirmada
                break
            else:
                esc = self.g.escala_anterior[esc]
        if esc == escala_tope:
            esc ='xx' # se llegó a tope y no se encontró nada.
        return esc 
    
    
    def buscar_subescala_con_rango_o_caida_macd(self,escala):
        ''' empieza por la escala  y si encuentra rango o caída retorna esa escala 
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de xx '''
        esc = self.g.escala_anterior[escala]
        while esc != "xx": # si llega a 1m  la retorna
            if self.situacion_adx_macd_rango_caida(esc) : 
                break
            else:
                esc = self.g.escala_anterior[esc]
        
        return esc     


    
    def busca_principio_macd_hist_min(self,escala):
        ''' retorna la posición del primer  histograma en minimo
        '''
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        li=l-1

        lfin=-1
        lini=-1
        

        while li >=0:
            if lfin==-1:
                if hist[li]<0:
                    lfin = li
                    
            if lfin > -1:
                if hist[li] <0:
                    lini=li
                else:
                    break
            li -= 1    

        if lini > -1:
            ret = l - lini
        else:
            ret =-1

        return ret                

    
    
    
    
    def el_precio_puede_caer(self,escala):
        ''' situacion1:
            macd+ pendiente- no compramos
        
            situacion2:
            estando en una loma de hist+ de 2 o mas de velas y adx+ 
            busca en el histograma negativo anterior el precio máximo alcanzado 
            y si ese precio no es superado ( se rompió la resistencia ) es posible 
            que el precio caiga '''

        self.actualizar_velas(escala)
        hist,sqz = self.sqzmon_lb(escala)
        low  = self.get_vector_np_low(escala)
        high = self.get_vector_np_high(escala)
        close = self.get_vector_np_close(escala)

        ult_vela=len(close) -1 
        ret = False
        
        #situacion 1
        desc_hist = self.squeeze_describir(escala,hist,sqz)
        if desc_hist[0] == 1 and desc_hist[1]  == -1: 
            ret = True

        # situacion 2
        if not ret: 
            tam,signo_loma,principio,pxpico = self.propiedades_macd_loma(hist,high,low,ult_vela)

            #print("tam,signo_loma,principio,pxpico",tam,signo_loma,principio,pxpico)

            if tam > 2 and signo_loma ==1:
                #adx = self.adx(escala,close,high,low)
                #print('adx',adx)
                #if adx[1] > 0:
                siguiente = principio - 1
                #print('siguiente',siguiente)
                if siguiente >0:
                    pico, principio = self.busca_pico_loma_hist(hist,high,low,-1,siguiente,1)
                    #print('pico, principio,precio',pico, principio,close[ult_vela])
                    if pico > close[ult_vela]:
                        ret = True # el precio puede caer!


        return ret            
    
    
    def retrocesos_fibo_macd(self,escala,ifib=2):
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.get_vector_np_low(escala)
        high = self.get_vector_np_high(escala)
        ret =[]
        minimo =-1
        maximo,principio = self.busca_pico_loma_hist(hist,high,low, 1 ,len(hist)-1,velas_minimas_de_la_loma=5)
        if maximo != -1: 
            principio_min = principio -1
            minimo,principio = self.busca_pico_loma_hist(hist,high,low, -1 ,principio_min,velas_minimas_de_la_loma=5)
        if minimo >=0:
            for f in range( ifib , len(self.g.ret_fibo) ):
                #print(self.g.ret_fibo[f])
                ret.append( maximo - (maximo - minimo) * (  self.g.ret_fibo[f] ) )
        else: 
            ret.append(0)    

        return ret  
    def retrocesos_fibo_macd_ema(self,escala,ifib=2):
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        ema  = talib.EMA(close, timeperiod=3)
        ret =[]
        maximo,principio = self.busca_pico_loma_hist_ema(hist,ema, 1 ,len(hist)-1,velas_minimas_de_la_loma=5)
        if maximo != -1: 
            principio_min = principio -1
            minimo,principio = self.busca_pico_loma_hist_ema(hist,ema, -1 ,principio_min,velas_minimas_de_la_loma=5)
       
        if minimo >=0:
            for f in range( ifib , len(self.g.ret_fibo) ):
                ret.append( maximo - (maximo - minimo) * (  self.g.ret_fibo[f] ) )
        else: 
            ret.append(0)    
            

        return ret        

    def retrocesos_convergentes_fibo_macd(self,escala,pos=0):
        '''
        calcula un retroceso fibo varias veces. ordena los resultados por distancia entre resultados.
        pos=0 el de la distancia mas corta
        pos=1 el primer retroceso menor (en precio) a pos=0
        pos=2 el segundo retroceso menor a pos=0

        '''
        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.get_vector_np_low(escala)
        high = self.get_vector_np_high(escala)
        
        iperiodo_alcista,fperiodo_alcista=self.periodo_alcista(close)
        
        #print('iperiodo_alcista,fperiodo_alcista',iperiodo_alcista,fperiodo_alcista)

        ret = []
        ifib =1 #el primer nivel despues de 0
        maximo,principio = self.busca_pico_loma_hist(hist,high,low, 1 ,fperiodo_alcista,velas_minimas_de_la_loma=3)
        if maximo != -1: 
            principio_min = principio -1
            
            c=0 #cuenta de macds
            while c<5 and principio_min > iperiodo_alcista:
                minimo,principio = self.busca_pico_loma_hist(hist,high,low, -1 ,principio_min,velas_minimas_de_la_loma=3)
                if minimo >=0:
                    #print('minimo',minimo)
                    for f in range( ifib , len(self.g.ret_fibo) ):
                        r = maximo - (maximo - minimo) * self.g.ret_fibo[f]
                        if r >0 : 
                            ret.append( r )
                else: 
                    break
                c += 1 
                
                principio_min = principio -1

        if len(ret)>0:
            ret.sort()
            dis=[]
            for i in range(1,len(ret)-1):
                di = ret[i]   - ret[i-1]
                dis.append([di, ret[i-1],ret[i]  ])
            
            dis.sort(key=lambda x: x[0])
    
            #print(dis)
            convergencia = dis[0][1]
        else:
            convergencia = 0    

        if pos >0 and convergencia >0:
        #en caso de pos >0 selecciono la convergenica menor 
            valores_por_distancia =[]
            for v in dis:
                valores_por_distancia.append(v[1])
                valores_por_distancia.append(v[2])
            p=1
            i=1
            while p <= pos:
                while valores_por_distancia[i] >= convergencia:
                    i +=1
                convergencia = valores_por_distancia[i]
                p +=1


        return convergencia    

    def ___deprecated___periodo_alcista(self,close):
        emar=talib.EMA(close, timeperiod=10)
        emal=talib.EMA(close, timeperiod=55)
        
        i=len(emar)-1
        fin = i
        try:
            while i>=0 and emar[i] <= emal[i]:
                i-=1
            
            if i != fin:
                fin = i+1

            while i>=0 and emar[i] > emal[i]:
                i -= 1

            ppo = ppo = i + 1

                
        except Exception as e:
            print(str(e))
                    

        return ppo,fin







    def busca_macd_hist_min(self,escala,vela_fin=0):
        ''' 
        dede vela_fin (0 es la ultima)
        busca el mínimo del histograma en el macd y retornas
        [0] = -1 si no encontró minimo
        [0] > -1 si no encontró minimo
        [1] distancia del minimo a la posicion actual
        [2] signo del ultimo histograma y anterior
            -1 los dos son negativos
             1 los dos son positivos
             0 uno es positivo y el otro es negativo para cuando [0] >-1
        [3] pendiente entre el penultimo y ultimo histograma
        [4] cantidad de velas del minimo
        [5] cantidad de velas con pendiente positiva
        [6] rsi de minimo
        [7] incremento del precio experado en atrdebajos
        
          
        '''

        self.actualizar_velas(escala)
        close = self.get_vector_np_close(escala)
        mac, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector

        #1) busco minimo histograma de macd
        imin=-1
        for i in range(l-1-vela_fin,1,-1):
            #print(i,hist[i],close[i])
            if hist[i-1] >  hist[i]  and hist[i-1] < 0 and  hist[i] < 0 : #estamos en bajada, seguimos
                imin = i
                break
        
        #print('---->imax',imax)
        
        if imin > -1:
            mxhist = hist[l-1] - hist[l-2]
            dx=l-imin-1-vela_fin
            if hist[l-1] < 0  and hist[l-2]  < 0:
                signo = -1
            elif hist[l-1] > 0  and hist[l-2]  > 0:
                signo = 1
            else:
                signo = 0 
            
            #cuento las velas del minimo
            chist_neg=1
            i= imin + 1 #l-imin es el indice absoluto
            while i < l-1:
                if hist[i] < 0:
                    chist_neg += 1
                    i +=1
                else:
                    break
            i= imin - 1
            while i >= 0:
                if hist[i] < 0:
                    chist_neg += 1
                    i -=1
                else:
                    break

            #calculo del rsi del minimo
            vrsi=talib.RSI(close, timeperiod=14)
            rsi=vrsi[imin]    
               

        else:
            mxhist=-1
            dx=-1
            signo = 0
            chist_neg = 0
            imin=-1
            rsi=None
        
        #cuento velas con pediente positivas y seguidas desde la vela actual
        cant_velas_pen_positiva=0
        if signo < 1 and mxhist>=0:
            #print(l-1,l-dx-1)
            for i in range(l-1,l-dx-1,-1):
                #print(i,hist[i-1],hist[i],)
                if hist[i-1]<=hist[i]: #el histo de la vela actual es menor o igual que el anteior sumo 1
                    cant_velas_pen_positiva+=1
                else: # se corta la seguidilla, dejo de sumar
                    break 

        #incremento 
        # saco el aumento del precio y si hay un aumento
        # lo comparo con el atr_bajos aumentado en la cantidad de velas que ha trascurrido
        # si el incremoento porcentual es muy grande ( a determiar ) se puede
        # interpretar como un posible pump
        incremento= -1
        if imin >0:
            vi: Vela = self.velas[escala].get_vela(imin)
            vf: Vela = self.velas[escala].ultima_vela()

            deltap = vf.close - vi.low
            if deltap >0:
                atrb = self.atr_bajos(escala,top=50,cvelas=None,restar_velas=1)
                incremento= round( variacion((atrb * (dx+1)) , deltap) ,2 )






        
        return [imin,dx,signo,mxhist,chist_neg,cant_velas_pen_positiva,rsi,incremento]     


    def macd_describir(self,escala,histo=None):
        '''
        Hace macd y describe su histograma

        [0] = 1  macd positivo
        [0] = -1 macd negativo
        [1] = 1 pendiente positiva distancia del minimo a la posicion actual
        [1] = -1 pendiente negativa
          
        '''
        if histo is None:
            self.actualizar_velas(escala)
            close = self.get_vector_np_close(escala)
            _, _, hist = talib.MACD(close, fastperiod=10, slowperiod=26, signalperiod=9)
        else:
            hist = histo   

        l=len(hist)-1#utimo dato del vector

        #signo del histograma
        signo=-1
        if hist[l]>0:
            signo=1

        #
        pendiente=-1
        if hist[l-1] < hist[l]:
            pendiente=1

        return [signo,pendiente]     

    def squeeze_describir(self,escala,hist=None,sqz=None):
        '''
        Hace squeeze y describe su histograma

        [0] = 1  squeeze positivo
        [0] = -1 squeeze negativo
        [1] = 1 pendiente positiva distancia del minimo a la posicion actual
        [1] = -1 pendiente negativa
          
        '''

        if hist is None:
            hist,sqz = self.sqzmon_lb(escala)
        
        l=len(hist)-1#utimo dato del vector

        #signo del histograma
        
        signo=0
        if hist[l]>0:
            signo=1
        else:
            signo=-1    

        pendiente=0
        if hist[l-1] < hist[l]:
            pendiente=1
        else:
            pendiente=-1    

        return [signo,pendiente,sqz[-1]]    
 

    def busca_mfi_menor(self,escala,cvelas,valor):
        
        self.actualizar_velas(escala)
        
        high=  self.velas[escala].valores_np_high()
        low=   self.velas[escala].valores_np_low()
        close= self.velas[escala].valores_np_close()
        volume=self.velas[escala].valores_np_volume()

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        
        print(mfi)

        p=-1

        l=len(mfi)#utimo dato del vector
         
        for i in range(l-1,l-cvelas,-1):
            print(mfi[i])
            if mfi[i] <= valor:
                p=l-i-1
        
        return p

                 






    
                    
    def busca_rsi_menor(self,escala,rsi_menor,cant_velas):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        vrsi=talib.RSI(vector, timeperiod=14)
        l=vector.size
        if cant_velas>l:
           c=l
        else:
           c=cant_velas  

        imenor=0# indi
        rsim=100# valor del rsi menor
        for i in range(l-c,l):
            if vrsi[i]<rsim:
                imenor=i
                rsim=vrsi[i]

        ic=l-1-imenor
        return [rsim<=rsi_menor and ic<=c,round(rsim,2),ic]       


    def busca_cruce_emas(self,escala,rapida=9,lenta=35,cant_velas=10):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=rapida)
        emal=talib.EMA(vector, timeperiod=lenta)
    
        l=vector.size
        if cant_velas>l:
            c=l
        else:
            c=cant_velas  

        pos=0
        
        # 1 arriba -1 abajo - 0 iguales
        if emar[l-c]>emal[l-c]:
            pos=1
        elif emar[l-c]<emal[l-c]:
            pos=-1
        else:
            pos=0    

        
        cruces=0    
        icruce=0

        for i in range(l-c+1,l):
            if emar[i]>emal[i]:
                if pos<1: # es 0 o -1
                    icruce=i
                    cruces=+1
                pos=1    
                    
            elif emar[i]<emal[i]:
                if pos>-1:
                    icruce=i    
                    cruces=+1
                pos=-1 
            else:
                pos=0    
                    
        return [cruces,pos,l-icruce]        

    #si la ema rápida está por encima de la ema lenta quiere decir que la tendencia es ascendente
    #si el rsi es bajo seguramente la tendencia no será ascendente pero 
    #si se detecta una suba con rsi bajo es una buena oportunidad
    def emas_y_control_rsi_OK(self,escala):
        
        if self.rsi(escala)<70:
            vector=self.velas[escala].valores_np_close()
            emar=talib.EMA(vector, timeperiod=9)
            emal=talib.EMA(vector, timeperiod=55)
            ret=emar[emar.size-1]>emal[emal.size-1]
        else:
            ret=True

        return ret

    #retorna verdadero si la ema rápida está por debajo de la lenta
    def ema_rapida_menor_lenta(self,escala,per_rapida,per_lenta):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        
        return emar[emar.size-1] < emal[emal.size-1]



    #retorna verdadero si la ema rápida está por encima de la
    def ema_rapida_mayor_lenta(self,escala,per_rapida,per_lenta):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        
        return emar[emar.size-1] > emal[emal.size-1]    

    def ema_vector_completo(self,escala,periodos):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        ema=talib.EMA(vector, timeperiod=periodos)
        return ema  

    def precio_vector_completo(self,escala):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        return vector    




    def coeficiente_ema_rapida_lenta(self,escala,per_rapida,per_lenta):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        return float(round ( (1 - emal[emal.size-1] / emar[emar.size-1] )*100,2))
        


 
    def sombra_sup_grande_en_ultima_vela(self,escala,coeficiente,pos):
        self.actualizar_velas(escala)
        vela=self.velas[escala].get_vela_desde_ultima(pos)
        
        ret=False
        nz=0.00000000001

        v=round(vela.sombra_sup() / (vela.cuerpo()+nz) ,2)

        if v>=coeficiente:
            ret= True
        
        return [ ret , v]    


    # def contar_resistencias(self,escala,pdiferencia,cant_velas):
    #     self.actualizar_velas(escala)
    #     vector=self.velas[escala].valores_np_high()
        
    #     l=vector.size
    #     if cant_velas>l:
    #        c=l
    #     else:
    #        c=cant_velas   

    #     ultimo=vector[l-1]
    #     resistencias=0
        
    #     v=[]
    #     v.append(0) 
        
    #     for i in range(l-c,l-2): #desde c velas hacia atras hasta la penúltima vela
    #         m=round((vector[i]-ultimo)/ultimo*100,3)
    #         v.append(m)
    #         if m>=0 and m < pdiferencia:
    #             resistencias+=1
        
    #     v[0]=resistencias
    #     return  v       





    #     v3=round(vector[l-3]/avg ,2)
    #     v2=round(vector[l-2]/avg ,2)
    #     v1=round(vector[l-1]/avg ,2)

    #     if v1>coeficiente or v2>coeficiente or v3>coeficiente:
    #         ret= True
        
    #     return [ ret , avg , v3, v2, v1]

        
    
    def rsi_mom(self,escala):
        
        self.actualizar_velas(escala)

        vector=self.velas[escala].valores_np_close()

        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        rsi=vrsi[vrsi.size-1]
        mom=vmom[vmom.size-1]
     

        return [rsi,mom]


    def rsi(self,escala,vela=0):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close(40)
        try:
            vrsi=talib.RSI(vector, timeperiod=14)
            rsi=vrsi[vrsi.size-1-vela]
            if np.isnan(rsi):
                rsi=101 # un número que normalmente evitará que se tome un desición de compra por ser muy alto
        except:
            rsi = 101


        return round(float(rsi),2) 

   







    def precio_de_rsi(self,escala,rsi_buscado):
        ''' retorna el precio (mas bajo) para llegar al ris
            indicado como parámetro de las escala en que se busca.
        '''
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        vrsi=talib.RSI(vector, timeperiod=14)
        rsi_verdadero=vrsi[vrsi.size-1]

        ultimo = vector.size -1
        px_orig= vector[ultimo]
        
        salto = px_orig  / 100
        
        if rsi_buscado < rsi_verdadero:
            signo = -1
        else:
            signo = 1    
        
        i=1
        j=0
        diff_anterior=1000
        px_anterior=px_orig
        while i <20 and j<40:
            px = px_orig + salto * signo * i 
            vector[ultimo] = px
            vrsi = talib.RSI(vector, timeperiod=14)
            rsi_nuevo = vrsi[vrsi.size-1]
            
            diff = abs(rsi_nuevo - rsi_buscado)
           
            #print ('--',px, diff,diff_anterior)

            if  diff > diff_anterior:
                #print ('--->')
                if abs(diff) > 0.5:
                    salto = salto * 0.4
                    signo = signo * -1
                    px_orig = px_anterior
                    i = 0
                else:
                    break
            else:
                diff_anterior = diff  
                px_anterior = px  
            
            i += 1
            j+=1
            
        print(rsi_nuevo,px)
       


        return px


        

    def compara_rsi(self,escala,cant_rsi):
        ''' retorna un vector con la diferencias de la rsi actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        self.actualizar_velas(escala)
        close=self.velas[escala].valores_np_close(50)
        vrsi=talib.RSI(close, timeperiod=14)
        l=vrsi.size
        ret=[]
        for i in range( l - cant_rsi , l):
            #print(vema[i], vema[i-1],vema[i] - vema[i-1])
            diferencia = vrsi[i] - vrsi[i-1]
            ret.append( diferencia ) 
        
        return ret    



    def mfi(self,escala):
        
        self.actualizar_velas(escala)
        
        high=  self.velas[escala].valores_np_high(40)
        low=   self.velas[escala].valores_np_low(40)
        close= self.velas[escala].valores_np_close(40)
        volume=self.velas[escala].valores_np_volume(40)

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        
        return round(float(mfi[mfi.size-1]),2)



    def mom(self,escala):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        mom=vmom[vmom.size-1]
        

        return mom

    def momsube(self,escala,x_mas_de_la_ema):
        
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        vema=talib.EMA(vmom  , timeperiod=10)
       
        mom=vmom[vmom.size-1]
        ema=vema[vema.size-1]

        return [mom > ema * x_mas_de_la_ema,mom,ema]    
    
    #vector de momentums, retorna un vector con los tres ultimos momentums
    def vmom(self,escala,periodos):
        self.actualizar_velas(escala)
        vector=self.get_vector_np_close(escala)
        vmom=talib.MOM(vector, timeperiod=periodos)

        return [ vmom[vmom.size-3],vmom[vmom.size-2] , vmom[vmom.size-1] ]

    

    def esta_subiendo4(self,escala):

        self.actualizar_velas(escala)
        uv   =self.velas[escala].ultima_vela()
        close=self.velas[escala].valores_np_close()
        vemas=talib.EMA(close, timeperiod=14)
        l=vemas.size
        ema=vemas[l-1]

        if  uv.close >ema and uv.open<uv.close and uv.close > close[l-2]: 
            return True
        else:
            return False    


    

    def pendiente_positiva_ema(self,escala,periodos):
        '''
        retorna True si la ultima dif entre la ultimaema y la anterior es positiva
        '''
        self.actualizar_velas(escala)
        close=self.get_vector_np_close(escala)
        vemas=talib.EMA(close, timeperiod=periodos)
        #        ultima                penultima   
        return ( vemas[vemas.size-1] - vemas[vemas.size-2] >=0 )


    def ema(self,escala,periodos):
        self.actualizar_velas(escala)
        close=self.get_vector_np_close(escala)
        vemas=talib.EMA(close, timeperiod=periodos)
        return vemas[vemas.size-1]

    def ema_minimos(self,escala,periodos):
        self.actualizar_velas(escala)
        low=self.get_vector_np_low(escala)
        vemas=talib.EMA(low, timeperiod=periodos)
        return vemas[vemas.size-1]

    def periodos_ema_minimos(self,escala,cvelas):
        '''
        busca los periodos para la ema de escala indicada
        en lo que los mínimos de las cvelas son superiores 
        a la ema de esos periodos
        '''
        periodos=9
        self.actualizar_velas(escala)
        low=self.get_vector_np_low(escala)
        
        lx = low.size
        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1  

        while periodos < 100:
            vemas=talib.EMA(low, timeperiod=periodos)
            se_cumple=True
            for i in range(lx - 1, lx-cvelas-1,-1):
                #print(i,vemas[i] , low[i])
                if vemas[i] > low[i]:
                    se_cumple=False
                    break
            if se_cumple:
                break
            else:
                periodos += 1

        return periodos        


    def stoploss_ema_minimos(self,escala,cvelas,restar_velas=1):
        '''
        busca los periodos para la ema de escala indicada
        en lo que los mínimos de las cvelas son superiores 
        a la ema de esos periodos.
        En caso de no cumplir retorna el valor mas chico que encuentre de la ultima ema
        '''
        periodos=4
        self.actualizar_velas(escala)
        low=self.get_vector_np_low(escala)
        
        lx = low.size
        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1  

        ret = self.precio_mas_actualizado()

        while periodos < 60:
            #print('periodos',periodos)
            vemas=talib.EMA(low, timeperiod=periodos)
            se_cumple=True
            primero = lx - 1 - cvelas - restar_velas
            ultimo = lx - 1 - restar_velas
            #print(primero,ultimo)
            for i in range( ultimo, primero ,-1):
                #print(i,vemas[i] , low[i])
                if vemas[i] > low[i]:
                    se_cumple=False
                    break
            if se_cumple:
                ret = float(vemas[vemas.size-1])
                break
            else:
                periodos += 1
                e = float(vemas[vemas.size-1])
                if e < ret:
                    ret = e

        #print('periodos',periodos) 
        #print(vemas)
        return  ret

        



        





    

    def stoploss_emas_escalas_minimos(self,escala):
        '''busco la ema justo debajo del precio
           y retorno el precio de la ema de n periodos +10
        '''
        self.actualizar_velas(escala)
        low=self.get_vector_np_low(escala)
        px = self.velas[escala].ultima_vela().close
        ret=-1
        periodos=10
        while periodos < 200:
            vemas=talib.EMA(low, timeperiod=periodos)
            e=vemas[vemas.size-1]
            print(px,e,periodos)
            if e < px:
                
                ret = vemas[vemas.size-1] - self.atr(escala)
                break
            periodos += 1

        return ret     





    #
    def precio_mayor_ultimas_emas(self,escala,periodos,cant_velas=1,porcentaje_mayor=0):
        '''
        retorna True si el precio es mayor que la la ema en las ultimas n velas
        escala = 1h 4h etc
        periodos = 9 10 25 200 etc
        cant_velas = cantidad de velas que el precio debe ser mayor a la ema
        '''
        self.actualizar_velas(escala)
        precio=self.get_vector_np_close(escala)
        vemas=talib.EMA(precio, timeperiod=periodos)

        ret=True
        for  i in range(vemas.size-cant_velas,vemas.size):
            
            if precio[i] * (1+ porcentaje_mayor/100) < vemas[i]: #subo el precio un porcentje extra pra seguir comprando en esa ema
                ret=False
                break 
        return ret
    

    def pendientes_ema(self,escala,periodos,cpendientes):
        self.actualizar_velas(escala)
        ret=[]
        try:
            close=self.velas[escala].valores_np_close()
            vema=talib.EMA(close, timeperiod=periodos)
            l=vema.size-1
            unidad=vema[l-1]
            for i in range(l-cpendientes,l):
                m= round(   (vema[i] - vema[i-1]) /unidad ,8)
                ret.append(m) 
                #print(close[i],vema[i])
        except Exception as e: 
            self.log.err(str(e))       

        return ret    


    def compara_emas1(self,escala,periodos,cant_emas):
        ''' retorna un vector con la diferencias de la ema actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        self.actualizar_velas(escala)
        close=self.velas[escala].valores_np_close()
        #print(close)
        vema=talib.EMA(close, timeperiod=periodos)
        l=vema.size
        ret=[]
        for i in range( l - cant_emas , l):
            #print(vema[i], vema[i-1],vema[i] - vema[i-1])
            diferencia = vema[i] - vema[i-1]
            ret.append( diferencia ) 
        return ret

    def compara_emas(self,escala,periodos,cant_emas):
        ''' retorna un vector con la diferencias de la ema actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        self.actualizar_velas(escala)
        close=self.velas[escala].valores_np_close(periodos * 3)
        #print (close)
        try:
            vema=talib.EMA(close, timeperiod=periodos)
            l=vema.size
            ret=[]
            for i in range( l - cant_emas , l):
                #print(vema[i], vema[i-1],vema[i] - vema[i-1])
                diferencia = vema[i] - vema[i-1]
                ret.append( diferencia ) 
        except:
            ret=[-1]        
        
        return ret

    def compara_adx(self,escala,cant):
        ''' retorna un vector con la diferencias de la adx actual
        menos el adx anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)
        v=talib.ADX(h,l, c, timeperiod=14)
        l=v.size

        ret=[]
        for i in range( l - cant , l):
            diferencia = v[i] - v[i-1]
            ret.append( diferencia ) 
        return ret    

   





    #busca que existan cpendientes con un coeficiente mayor al dado
    def pendientes_ema_mayores(self,escala,periodos,cpendientes,coeficiente):
        self.actualizar_velas(escala)
        close=self.velas[escala].valores_np_close()
        vema=talib.EMA(close, timeperiod=periodos)
        l=vema.size-1
        unidad=vema[l-1]
        ret=True
        for i in range(l-cpendientes,l):
            
            m= round(   (vema[i] - vema[i-1]) /unidad ,8)
            
            if m < coeficiente:
                ret=False
                break
        return ret   

       



    def atr(self,escala,vela=0,cvelas=1):
        ret=0
        
        self.actualizar_velas(escala)

        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)
        
        try:

            vatr = talib.ATR(h, l, c, timeperiod=14)
            
            v=vatr.size-1-vela
            if cvelas==1:
                ret=vatr[v]
            else:
                ret=vatr[v-cvelas+1:v+1]
        except:
            pass            
            
        
        return ret

    def hay_pump3(self,escala,cvelas,xatr=10,xvol=10):
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)
        
        vvol=self.get_vector_np_volume(escala)

        vatr = talib.ATR(h, l, c, timeperiod=14)

        atr =self.atr_bajos(escala,100,200,0)
        vol =self.promedio_volumenes_bajos(escala,100,200,0)


        lx = vatr.size
        if cvelas > lx:
            cvelas = lx -1
        ret = False 
        for i in range(lx-cvelas,lx):
            if vvol[i]/vol > xvol or vatr[i]/atr > xatr:
                self.log.log('hay_pump3 escala',escala,'cvelas',cvelas,'i',i,'vvol[i]/vol',vvol[i]/vol, xvol ,'vatr[i]/atr', vatr[i]/atr , xatr )
                ret =True
                break

        return ret    

    def detectar_pumps(self,escala,cvelas,xatr=10,xvol=10):
        esc = escala
        ret = False
        while esc!='1w':
            if self.hay_pump3(esc,cvelas,xatr=10,xvol=10):
                ret = True
                break
            esc = self.g.escala_siguiente[esc]

        return ret    










            

    def vatr(self,escala,velas=5):
        self.actualizar_velas(escala)

        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)

        vatr = talib.ATR(h, l, c, timeperiod=14)
        
        v=vatr.size - 1

        print (vatr)
        return vatr[ vatr.size - velas : vatr.size ]   


    def vprecio(self,escala,velas=5):
        self.actualizar_velas(escala)

        p=self.get_vector_np_close(escala)
        
        return p[ p.size - velas : p.size ]   

    def vvolumen(self,escala,velas=5):
        self.actualizar_velas(escala)

        vector=self.velas[escala].valores_np_volume()
        
        return vector[ vector.size - velas :vector.size ]        
              
    def vp(self,escala,cvelas=None):
        self.actualizar_velas(escala)
        df=self.velas[escala].panda_df(cvelas)
        vp = df.ta.vp()
        
        return vp
      



    def atr_todos(self):
        todos=[]
        todos.append(self.atr('1w')  )
        todos.append(self.atr('1d')  )
        todos.append(self.atr('4h')  )
        todos.append(self.atr('1h')  )
        todos.append(self.atr('15m') )
        todos.append(self.atr('5m')  )
        todos.append(self.atr('1m')  )
        return todos

    def volume(self,escala):

        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()


        avg=np.average(vector)
        v2=vector[vector.size-1]
        v1=vector[vector.size-2]
        v0=vector[vector.size-3]

        return [ v0<v1 and v1>avg*1.1, v0, v1 ,v2]

    def volumen_porcentajes(self,escala):

        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()

        avg=round(np.average(vector),2)

        p=self.velas[escala].porcentaje_ultima_vela()

        v4=round((vector[vector.size-1]/avg)/p,2) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo
        v3=round(vector[vector.size-2]/avg,2)
        v2=round(vector[vector.size-3]/avg,2)
        v1=round(vector[vector.size-4]/avg,2)
        v0=round(vector[vector.size-5]/avg,2)

        return [ avg, v0, v1 ,v2, v3, v4]   

    def volumen_proyectado(self,escala):
        self.actualizar_velas(escala)
        p=self.velas[escala].porcentaje_ultima_vela()
        v=self.velas[escala].ultima_vela().volume
        return round(  v/p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo

    def volumen_proyectado_moneda_contra(self,escala):
        self.actualizar_velas(escala)
        p=self.velas[escala].porcentaje_ultima_vela()
        v=self.velas[escala].ultima_vela().volume
        precio = self.precio(escala)
        return round(  v * precio  /p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo    
    


    def volumen_creciente(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return ( vc[l-3]<vc[l-2]  and vc[l-2]<vc[l-1] and vc[l-2]>0.9 and vc[l-1]>1 )


    def volumen_bueno5(self,escala,coef):
        self.actualizar_velas(escala)
        vector_volumenes=self.velas[escala].valores_np_volume()
        vemavol=talib.EMA(vector_volumenes, timeperiod=20) #20 periodos es lo que usa tradingview por defecto para mostral el promedio del volumen
        ultima_vela=len(vector_volumenes)-1
        
        ret=( vector_volumenes[ultima_vela]   > vemavol[ultima_vela]   * coef or \
                 vector_volumenes[ultima_vela-1] > vemavol[ultima_vela-1] * coef   )
        return {'resultado':ret,'vol':[round(vector_volumenes[ultima_vela-1],2) , round(vector_volumenes[ultima_vela],2) ],'ema':[round(vemavol[ultima_vela-1],2) , round(vemavol[ultima_vela],2) ]  }

    def volumen_moneda_contra(self,escala): #entrega el volumen expresado en la moneda contra
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()
        precio=self.precio(escala)
        l=len(vector)
        
        if l >= 5:
            ini=l-5
        else:
            ini=l

        vol_mc=[]
        for i in range (ini,l):
            vol_mc.append(  self.redondear_unidades(  vector[i]*precio)  )

        return vol_mc     

    def volumen_sumado_moneda_contra(self,escala,velas=1): #entrega el volumen expresado en la moneda contra
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()
        precio=self.precio(escala)
        l=len(vector)
        
        if l >= velas:
            ini=l-velas
        else:
            ini=0

        volumen=0
        for i in range (ini,l):
            volumen +=  self.redondear_unidades(  vector[i]*precio) 

        return volumen       


    def redondear_unidades(self,unidades):
        cant=unidades
        if  0 < cant <1:
            cant=round(cant,4)
        elif 1 <= cant <9:
            cant=round(cant,2)
        else:
           cant=int(cant)
        return cant 
                





    # volumen_bueno trata de detectar un aumento creciente del volumen donde la ultima vela cerrada debe tener al menos un incremento superior a un coeficiente pasado como parametro
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    # no tengo en cuenta la ultima vela puesto que está en desarrollo y como es proyectada, no es exacto el calculo
    def volumen_bueno(self,escala):  
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return ( vc[l-4]>self.incremento_volumen_bueno*0.3 and vc[l-4]>self.incremento_volumen_bueno*0.4 and vc[l-3]>self.incremento_volumen_bueno*0.5 and vc[l-2]>self.incremento_volumen_bueno ) 

    # volumen_bueno2v trata de detectar un aumento casi instantaneo teniendo solamente encuenta la última vela cerrada y la vela en desarrollo
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    def volumen_bueno2v(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return  vc[l-2]>self.incremento_volumen_bueno*0.5 and vc[l-1]>self.incremento_volumen_bueno

    # volumen_bueno_ultima_v trata de detectar un aumento "instantaneo" ya que solo tiene en cuenta a la vela en desarrollo.
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    def volumen_bueno_ultima_v(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        return  vc[l-1]>self.incremento_volumen_bueno
        
    


                  





    def _deprecated_volumen_actual(self,escala):  #usa  *** hora de inicio y cierre de la vela y ya no tengo ese dato o volver a implementarlo en caso de ser necesario
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()

        avg=round(np.average(vector),2)

        p=self.velas[escala].porcentaje_ultima_vela() # ***

        v3p=round((vector[vector.size-1]/avg)/p,2) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo
        v3=round(  vector[vector.size-1]/avg,2) #volumen promedio real
        return [ avg, p, v3p,v3]     


    def volumen_mayor_al_promedio(self,escala):

        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_volume()

        

        avg=np.average(vector)
        v=vector[vector.size-1]

        
        
        return v>avg     

    def la_ultima_vela_es_linda(self,escala):
        self.actualizar_velas(escala)

        vela=self.velas[escala].ultima_vela()
        
        cuerpo=1-vela.open/vela.close # en porcentaje

        if cuerpo>0.03:
           return True
        else:
           return False

    def aumento_ultima_vela(self,escala):
        self.actualizar_velas(escala)

        vela=self.velas[escala].ultima_vela()
        
        cuerpo=1-vela.open/vela.close # en porcentaje

        return round(cuerpo * 100,2)
    


    
    def la_ultima_vela_es_positiva(self,escala):
        self.actualizar_velas(escala)

        vela=self.velas[escala].ultima_vela()
        
        return (vela.signo==1)

    def _deprecated_velas_positivas(self,escala,cant_velas,incremento):
        self.actualizar_velas(escala)
     
        vector=self.velas[escala].get_velas()  ## esta funcion ya no existe hay que ley el df directamente
      
        ultima_vela=len(vector)-1 

        ret=True # asumo que las velas son ok y las trato de invalidar
        for i in range(ultima_vela, ultima_vela - cant_velas, -1):
            
            cuerpo=vector[i].open - vector[i].close
            
            if cuerpo<incremento: #se invalida porque es menor al icremento deseado
                ret=False
                break
        return ret

    def analisis(self,escala,pvol):
        vatr=self.vatr(escala,30)
        vmom=self.vmom(escala,30)
        vvol=self.volumen_porcentajes(escala)
        #variacion de atr
        v2=vatr[1]/vatr[2] #variacion entre la vela en curso y la anterior
        v1=vatr[0]/vatr[1] #variacion entre la ultima vela completa y la anterior
        #direccion de momentum
        m=vmom[2] # tomamos el momentum de la vela en formacion que nos da la direccion y velocidad de precio actual
        #volumen
        
        #analizamos
        if  vvol[1]<vvol[2] and vvol[2]>1.7 and  vvol[3]>1:
            #hay vol
            if m>0:
                #positivo
                if v2>2 and v1>1.2:
                    #con atr
                    ret=3
                else:
                    ret=2
            else:
                #negativo
                if v2>2 and v1>1.2:
                    #sin atr
                    ret=-3
                else:
                    ret=-2
        else:
            #no hay vol
            if m>0:
                #positivo
                if v2>2 and v1>1.2:
                    #con volumen
                    ret=1
                else:
                    ret=0
            else:
                #negativo
                if v2>2 and v1>1.2:
                    #con volumen
                    ret=-1
                else:
                    ret=0
        return ret                

    def esta_subiendo15m(self):
        self.actualizar_velas('15m')
        
        vector=self.velas['15m'].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        

        return (r0<r1 and m0<m1 and self.volumen_mayor_al_promedio('15m'))  # rsi sube, momento sube, y hay volumen

    def esta_subiendo(self,escala):
        self.actualizar_velas(escala)
        
        vector=self.velas[escala].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        

        return (r0<r1 and m0<m1 and self.volumen_mayor_al_promedio(escala))  # rsi sube, momento sube, y hay volumen

    

    def esta_subiendo2(self,escala):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        uvela=self.velas[escala].ultima_vela()
        #self.log.log("Precios",escala,vector[vector.size-3],vector[vector.size-2],vector[vector.size-1])
        if uvela.open<uvela.close and ( (vector[vector.size-3]<=vector[vector.size-2] and  vector[vector.size-2]<=vector[vector.size-1] ) or vector[vector.size-3]<vector[vector.size-1]):
            return True
        else:     
            return False

    def esta_subiendo3(self):
        self.actualizar_velas('2h')
        self.actualizar_velas('15m')
        atr=self.vatr('2h',12)[2]
        ema=self.ema('15m',9)
        precio=self.velas['15m'].ultima_vela().close
        return precio>ema+atr
    
    def esta_bajando3(self):
        self.actualizar_velas('2h')
        self.actualizar_velas('15m')
        atr=self.vatr('2h',12)[2]
        ema=self.ema('15m',9)
        precio=self.velas['15m'].ultima_vela().close
        
        return precio<ema-atr

    def precio(self,escala):
        self.actualizar_velas(escala)
        try:
            px = self.velas[escala].ultima_vela().close
        except:
            px = -1
        return px      

    # cuando el momentum pierde fuerza, la diferencia entre el momento actual y el aterior se hace cada vez mas chica
    # eso indica que la velocidad de subia está disminuyendo,la curva de aplana y muy posiblemente comience a bajar
    # entonces esta funciona de True cuando NO pierde fuerza.
    def mom_bueno(self,escala):
        self.actualizar_velas(escala)
        vector=self.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)


        if vmom[vmom.size-4]<vmom[vmom.size-1]: #Controla que el mom sea creciente

            # if vmom[vmom.size-4]!=0:  
            #    m3=round(vmom[vmom.size-3]/vmom[vmom.size-4],3)
            # else:
            #    m3=0

            # if vmom[vmom.size-3]!=0:  
            #    m2=round(vmom[vmom.size-2]/vmom[vmom.size-3],3)
            # else:
            #    m2=0
            
            # if vmom[vmom.size-2]!=0:  
            #    m1=round(vmom[vmom.size-1]/vmom[vmom.size-2],3)
            # else:
            #    m1=0   

            # self.log.log("Cociente MOMs",m3,m2,m1)

            # if m3<m2<m1: # controla que no sea deshacelerado
            #     return True
            # else:
            #     return False    
            return True
        else:
            #self.log.log("MOM no es creciente")
            return False


    
    def esta_bajando(self,escala):
        self.actualizar_velas(escala)
        
        vector=self.velas[escala].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

      

        return (r1<r0 and m1<m0 )  # rsi sube, momento sube, y hay volumen
        
    def esta_lateral(self,escala):
        return (    not self.esta_subiendo(escala) and   not self.esta_bajando(escala)    )

    def tendencia(self):
        ten=0
        if self.ema('15m',25) < self.ema('15m',12): #la ema rápida es mayor que la lenta, está subiendo
            ten+=3
        if self.esta_subiendo('5m'):
            ten+=1
        if self.esta_subiendo('15m'):
            ten+=1
        if self.esta_subiendo('1h'):
            ten+=1
        if self.esta_subiendo('4h'):
            ten+=1
        if self.esta_subiendo('1d'):
            ten+=1    
        if self.esta_bajando('5m'):
            ten-=1
        if self.esta_bajando('15m'):
            ten-=1
        if self.esta_bajando('1h'):
            ten-=1
        if self.esta_bajando('4h'):
            ten-=1
        if self.esta_bajando('1d'):
            ten-=1    
        return ten    

   



    # def esta_subiendo(self,escala):
    #     self.actualizar_velas('15m')
        
    #     vector=self.velas15m.valores_np_close()
        
    #     vrsi=talib.RSI(vector, timeperiod=14)
    #     vmom=talib.MOM(vector, timeperiod=10)
        
    #     r1=vrsi[vrsi.size-1]
    #     r0=vrsi[vrsi.size-2]
        
    #     m1=vmom[vmom.size-1]
    #     m0=vmom[vmom.size-2]

    

    #     return (r0<r1 and m0<m1 and volumen_mayor_al_promedio('15m'))  # rsi sube, momento sube, y hay volumen    

    def esta_subiendo4h(self):

        if not self.la_ultima_vela_es_linda('4h'):
            return False
        
        vector=self.velas['4h'].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]

        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        #print "r0 r1 m0 m1",r0 ,r1 ,m0 ,m1

        return (r0<r1 and m0<m1) #el rsi subiendo y momento subiendo    

    def puntos_pivote(self,escala):
        self.actualizar_velas(escala)

        vela=self.velas[escala].ultima_vela_cerrada()
        pp=( vela.high + vela.low + vela.close) / 3 # PP (P) = (H + L + C) / 3
        r2= pp + (vela.high - vela.low)
        r1= pp + (pp - vela.low)
        s1= pp - (vela.high - pp)
        s2= pp - (vela.high - vela.low)

        return [s2,s1,pp,r1,r2]

    def puntos_pivote_fibo(self,escala):
        self.actualizar_velas(escala)
        vela=self.velas[escala].ultima_vela_cerrada()
        R = vela.high - vela.low
        PP = ( vela.high + vela.low + vela.close) / 3
        R1 = PP + (R * 0.382)
        R2 = PP + (R * 0.618)
        R3 = PP + (R * 1.000)
        R4 = PP + (R * 1.618)
        S1 = PP - (R * 0.382)
        S2 = PP - (R * 0.618)
        S3 = PP - (R * 1.000)
        S4 = PP - (R * 1.618)
        #print ([R4,R3,R2,R1,PP,S1,S2,S3,S4])
        return [R4,R3,R2,R1,PP,S1,S2,S3,S4]

   






    #detecta con respecto al precio actual si hay un movimiento (una diferencia porcentual del precio) > al coeficiente
    def __deprecated___movimiento(self,escala,cvelas,porcentaje):
        self.actualizar_velas(escala)
        ot=self.velas[escala].ultima_vela().open_time
        o =self.velas[escala].ultima_vela().open
        h =self.velas[escala].ultima_vela().high
        l =self.velas[escala].ultima_vela().low
        c =self.velas[escala].ultima_vela().close  

      
        p=self.diff_porcentaje(o,h,l,c)

        #print (69,datetime.utcfromtimestamp(int(ot)/1000).strftime('%Y-%m-%d %H:%M:%S'),o,h,l,c,p)


        if ( abs(p) > porcentaje ):
            ret=[True,p,-1,ot]
        else:
            ret=[False,p,-1,'-']
            
            fin =len(self.velas[escala].velas)-2
            ini = fin - cvelas +1
            for i in range(fin,ini,-1):

                ot=self.velas[escala].velas[i].open_time
                o =self.velas[escala].velas[i].open
                h =self.velas[escala].velas[i].high
                l =self.velas[escala].velas[i].low
                
                
                #c = es el de la ultima vela que tenemos, para conpararlo con las velas enterirore

                q=self.diff_porcentaje(o,h,l,c)


                if (abs(q) > porcentaje ):
                    ret=[True,q,i,ot]
                    break
          
        return ret

    def diff_porcentaje(self,o,h,l,c):
        p0=1 - o/c
        p1=1 - h/l

        if abs(p0) > p1:
            return round( p0 * 100 ,2)
        else:
            return round( p1 * 100 ,2)    
        


    def bollinger(self,escala,periodos=20,desviacion_standard=2,velas_desde_fin=60):
        self.actualizar_velas(escala)
        vc=self.velas[escala].valores_np_close(velas_desde_fin) # solo los ultimos <velas_desde_fin> elementos
        bs, bm, bi = talib.BBANDS(vc, timeperiod=periodos, nbdevup=desviacion_standard, nbdevdn=desviacion_standard, matype=0)

        return float(  bs[-1]  ),float(  bm[-1]  ),float(  bi[-1]  )
    

    #trata de determinar el precio donde hubo la menor volatilidad posible
    #entorno a un vela dada 
    #para ello saca la diferencia entre la banda superior y la inferior de bollinger
    #donde la diferencia es menor, tomamos el precio cierre redondeado como precio de rango
    def rango_por_bollinger(self,escala,velas_desde_fin):
        self.actualizar_velas(escala)
        vc=self.velas[escala].valores_np_close() #vector close
        #vo=self.velas[escala].valores_np_open()  #vector open
        bs, bm, bi = talib.BBANDS(vc, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    
        ultimo= len(bs)-1 
        
        ini= ultimo -velas_desde_fin
        if ini<0:
           ini=0

        
        p= ultimo  
        diff_bb=bs[p]-bi[p]  # saco la diferencia entre la banda superior e inferior 
       
        for i in range(ultimo,ini,-1):
            diff_bb_i=bs[i]-bi[i]
            if diff_bb==0:
                pass
            if diff_bb_i < diff_bb:

                diff_bb=diff_bb_i
                p=i

        #p ahora debe tener la posicion donde las bandas de bollinguer son mas angostas
        #el valor de la bm de bollinguer determina el rango
          
        return (p,bm[p]/10000000)

    def tiempo_a_escala_velas(self,horas):
       
        if 1 <= horas < 200:
            escala='1h'
            velas= horas
        elif 200 <= horas < 800:
            escala='4h'
            velas=int(horas/4)
        elif 800 <= horas <= 4800:
            escala='1d'
            velas=int(horas/24)
        elif 4800 <= horas <= 33600:
            escala='1w'
            velas=int(horas/168)    
        else:    
            escala='1m'
            velas=200    

        #print ('escalas,velas',escala,velas)    
        return escala,velas

    def sqzmon_lb(self,escala,cvelas=None):
        self.actualizar_velas(escala)
        df=self.velas[escala].panda_df(cvelas)
        sqz = df.ta.squeeze( lazybear = True)
        histo=[]
        sqz_on=[]
        for _,i in sqz.iterrows():
            histo.append(i['SQZ_20_2.0_20_1.5_LB'])
            sqz_on.append(i['SQZ_ON'])
        
        return histo,sqz_on


    def sqzmon_lb_df(self,escala,cvelas=None):
        self.actualizar_velas(escala)
        df=self.velas[escala].panda_df(cvelas)
        sqz = df.ta.squeeze( lazybear = True)
        #print(sqz)
        return sqz  

    def squeeze_df_describir(self,escala,df=None):
        '''
        Hace squeeze y describe su histograma

        [0] = 1  squeeze positivo
        [0] = -1 squeeze negativo
        [1] = 1 pendiente positiva distancia del minimo a la posicion actual
        [1] = -1 pendiente negativa
          
        '''

        if df is None:
            df = self.sqzmon_lb_df(escala,40)
        
        hist = 'SQZ_20_2.0_20_1.5_LB'
        #signo del histograma
        signo=0
        if df[hist].iloc[-1] >0:
            signo=1
        else:
            signo=-1    

        pendiente=0
        if df[hist].iloc[-2] < df[hist].iloc[-1]:
            pendiente=1
        else:
            pendiente=-1    

        return [    signo,pendiente, df['SQZ_OFF'].iloc[-1]   ]          






    def mp_slice_ev(self,escala,cvelas,tick_size=0.00000001):
        
        #print ('escala,cvelas',escala,cvelas)
        self.actualizar_velas(escala)
        df=self.velas[escala].panda_df(cvelas)
        #self.log.log(self.par,horas,'df.min.max',df.index.min(),df.index.max())
        mp = MarketProfile( df ,tick_size=tick_size)
        #mp_slice = mp[df.index.max() - pd.Timedelta(6.5, 'h'):df.index.max()]
                
        try:
            
            mp_slice= mp[df.index.min():df.index.max()]
            rango_inferior=mp_slice.value_area[0]
            rango_superior=mp_slice.value_area[1]
            poc=mp_slice.poc_price
            
            #print ("Initial balance: %f, %f" % mp_slice.initial_balance())
            #print ("Opening range: %f, %f" % mp_slice.open_range())
            #print ("POC: %f" % mp_slice.poc_price)
            #print ("Profile range: %f, %f" % mp_slice.profile_range)
            #print ("Value area: %f, %f" % mp_slice.value_area)
            #print (mp_slice.value_area[0])
            #print ("Balanced Target: %f" % mp_slice.balanced_target)

            
        except:
            rango_inferior=0
            rango_superior=0
            poc=0    
        
        return (rango_inferior,poc,rango_superior)
  





    def mp_slice(self,horas,tick_size=0.00000001):
        escala,cvelas = self.tiempo_a_escala_velas(horas)
        #print ('escala,cvelas',escala,cvelas)
        self.actualizar_velas(escala)
        df=self.velas[escala].panda_df(cvelas)
        #self.log.log(self.par,horas,'df.min.max',df.index.min(),df.index.max())
        mp = MarketProfile( df ,tick_size=tick_size)
        #mp_slice = mp[df.index.max() - pd.Timedelta(6.5, 'h'):df.index.max()]
                
        try:
            
            mp_slice= mp[df.index.min():df.index.max()]
            rango_inferior=mp_slice.value_area[0]
            rango_superior=mp_slice.value_area[1]
            poc=mp_slice.poc_price
            
            #print ("Initial balance: %f, %f" % mp_slice.initial_balance())
            #print ("Opening range: %f, %f" % mp_slice.open_range())
            #print ("POC: %f" % mp_slice.poc_price)
            #print ("Profile range: %f, %f" % mp_slice.profile_range)
            #print ("Value area: %f, %f" % mp_slice.value_area)
            #print (mp_slice.value_area[0])
            #print ("Balanced Target: %f" % mp_slice.balanced_target)

            
        except:
            rango_inferior=0
            rango_superior=0
            poc=0    
        
        return (rango_inferior,poc,rango_superior)


    #entrega una listas con los maximos y minimos poc y porcentaje de diff 
    #entre maximos y minimos 
    #desde el inicio hasta n luego hasta n-1 ....
    #esto sirve para detectar un cambio abrupto en differencia de porcentaje 
    #entre maximos y minimos lo que indica el comienzo de un movimiento
    def mp_slices_progresivos(self,escala,tick_size=0.00000001):
        self.actualizar_velas(escala)
        dftotal=self.velas[escala].panda_df()
         
        rows=dftotal.shape[0] 

        lista_mktp=[] 

        for i  in range(5,rows):
            print (i)
            df=dftotal.head(i)
            mp = MarketProfile( df ,tick_size=tick_size)
            
            mp_slice= mp[df.index.min():df.index.max()]
            pmin=mp_slice.value_area[0]
            ppoc=mp_slice.poc_price
            pmax=mp_slice.value_area[1]
        
            lista_mktp.append( (   pmin, ppoc, pmax, round( 1 - pmin/pmax,8 ) * 100  )      )
        #print ("Initial balance: %f, %f" % mp_slice.initial_balance())
        #print ("Opening range: %f, %f" % mp_slice.open_range())
        #print ("POC: %f" % mp_slice.poc_price)
        #print ("Profile range: %f, %f" % mp_slice.profile_range)
        #print ("Value area: %f, %f" % mp_slice.value_area)
        # print (mp_slice.value_area[0])
        #print ("Balanced Target: %f" % mp_slice.balanced_target)

        #return mp_slice.poc_price
        return lista_mktp

    
    #entrega una lista con los pocs de las escalas pasadas como parámetros
    def lista_pocs(self,lista_tiempos,poc=0,tick_size=0.00000001):
        listapocs=[]
        for tiempo in (lista_tiempos):
            try:
                tpoc=self.mp_slice(tiempo, tick_size)
                if tpoc[poc]>0:
                    listapocs.append (self.mp_slice(tiempo, tick_size)[poc])
            except Exception as e:
                self.log.log('Error listapocs()',e)
            

        return listapocs    


    #entrega una lista las emas solicitadas en {'1h':50,escala:periods,....}
    def lista_emas(self,dic_escalas):
        listaemas=[]
        for escala in dic_escalas:
           
            listaemas.append (self.ema(escala,dic_escalas[escala]))
        return listaemas    



    #
    def max_y_luego_min(self,escala,periodos_hacia_max=200,periodos_hacia_min=199):
        self.actualizar_velas(escala)
        vmax=self.velas[escala].valores_np_high()
        vmin=self.velas[escala].valores_np_low()
        #precio=self.velas[escala].ultima_vela().close
        l=vmax.size

        #primero busco max   
        if periodos_hacia_max>l-1:
            p=l-1
        else:
            p=periodos_hacia_max

        max=vmax[l-1]
        min=vmin[l-1]
        pmax=l-1

        for i in range(l-p,l):
            if vmax[i]>max:
                max=vmax[i]
                pmax=i
                min=vmin[i]
                #print('max,pmax,min',max,pmax,min)
                
        #a ahora busco min a partir de la direccion de pmax-1

        tope=pmax-1 - periodos_hacia_min
        if tope<0:
            tope=0
        pmin=pmax    
        for i in range(pmax-1,tope,-1):
            #print(i,vmin[i])
            if vmin[i]<min:
                min=vmin[i]
                pmin=i
        
        return [min,max,l-1-pmin,l-1-pmax]

    def buscar_la_vela_mas_grande(self,escala,cvelas):
        ''' Retorna la posición de la vela mas grande a apartir de la última
            0 = la ultima, 1 penultima,...
        '''
        self.actualizar_velas(escala)
        cuerpos=self.velas[escala].valores_np_cuerpo(cvelas)
        l=len(cuerpos)
        tam=0
        p=0

        for i in range(0,l):
            #print(i,cuerpos[i])
            if tam <= cuerpos[i]:
                tam = cuerpos[i]
                p=i

        return l-p-1        


    def promedio_de_altos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top mas altos
            top entre 2 y la maxima cantidad de velas
            memorizadas menos restar_velas (para no tomar las ultimas velas)
        '''    
        self.actualizar_velas(escala)
        vmax=self.velas[escala].valores_np_high()
        
        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = len(vmax) 
        if top > lx:
            top = lx 

        if cvelas == None or cvelas > lx:
            cvelas=lx

        subset=vmax[ lx-cvelas: lx - restar_velas]

        subset[::-1].sort() #odenada de menor a Mayor

        return float( np.average(subset[ 0 : top ]) )

    def promedio_de_bajos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top mas bajos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        self.actualizar_velas(escala)
        vmin=self.velas[escala].valores_np_low()
        
        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = len(vmin) 
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=vmin[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )
    
    def promedio_de_maxmin_velas_negativas(self,escala,top=10,cvelas=20,restar_velas=1):
        ''' retorna un promedio maximos - minimos
            de velas negativas
        '''    
        self.actualizar_velas(escala)
        ret = 0
        
        vmaxmin=self.velas[escala].valores_np_maxmin(cvelas)
        
        try:
            #correciones de entradas erroneas
            if top < 2:
                top = 2
            
            lx = len(vmaxmin) 
            if top > lx:
                top = lx 

            maxmin=[]

            for i in range(0 ,  lx - restar_velas -1):
                if vmaxmin[i] <0:
                    maxmin.append( vmaxmin[i] * -1 )

            maxmin[::-1].sort() #odenada de menor a Mayor

            ret = float( np.average(maxmin[ 0 : top ]) )    
        except:
            pass

        return ret    
    
    
    def atr_bajos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top atr mas bajos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)

        valores = talib.ATR(h, l, c, timeperiod=14)
        
        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = valores.size
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=valores[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )

    def atr_altos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top atr mas altos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        self.actualizar_velas(escala)
        c=self.get_vector_np_close(escala)
        h=self.get_vector_np_high(escala)
        l=self.get_vector_np_low(escala)

        valores = talib.ATR(h, l, c, timeperiod=14)
        
        valores= valores[~np.isnan(valores)] #limpieza de nan

        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = valores.size
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=valores[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::-1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )    

    def promedio_volumenes_bajos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top volumenes mas bajos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        self.actualizar_velas(escala)
        valores=self.get_vector_np_volume(escala)

        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = valores.size
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=valores[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )
    
    def rango(self,escala,prango_max=2,cvelas=None):
        ''' retorna el rango_actual y el rango que no se supere el prango_max
            tambien retorna la vela donde se superó el rango o la ultima vela posible 
            siempre contando desde lo mas nuevo a lo mas viejo
        '''    
        restar_velas=1
        self.actualizar_velas(escala)
        vopen  = self.velas[escala].valores_np_open()
        vclose = self.velas[escala].valores_np_close()

        lx = vopen.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        
        px = self.velas[escala].ultima_vela().close

        #calculo rango actual (ultima vela)
        min , max = self.__valor_menor_mayor(vopen[lx-1],vclose[lx-1])
        prango_actual= round( (max - min) / px * 100 ,2)

        #comienzo de busqueda de rango maximo
        min , max = self.__valor_menor_mayor(vopen[lx-1-restar_velas],vclose[lx-1-restar_velas])
        prango= round( (max - min) / px * 100 ,2)
        
        for i in range(lx - restar_velas - 2, lx-2-cvelas,-1):
            
            mi , ma =  self.__valor_menor_mayor(vopen[i],vclose[i])
            if mi < min:
                min = mi
            if ma > max:
                max = ma
            
            irango= round( (max - min) / px * 100 ,2)

            #print(i,prango)
            if irango > prango_max:
                break
            
            prango = irango # esta rango es bueno, me lo quedo
        
        vela = lx - 2 - i  # lx -1 - i-1

        return  prango_actual, prango, vela


    def precio_en_rango(self,escala,pmin,pmax,total_velas=30):
        '''
            retorna la cantidad de velas que el precio se encuentra entre pmax y pmin
        '''    
        self.actualizar_velas(escala)
        close = self.velas[escala].valores_np_close(total_velas)

        cvelas=0

        for p in reversed(close):
            if pmin <= p <= pmax:
                cvelas +=1
            else:
                break

        return cvelas

    def calc_rango_fibo(self,escala,pos=3):
        
        pxfc = self.retrocesos_fibo_macd(escala,pos)[0] #
        
        if pxfc == 0:
            rini = 0
            rfin = 0
        else:
            atr = self.atr_bajos(escala,top=10)
            rini = pxfc - atr
            rfin = pxfc + atr

        return  rini, rfin

    def calc_rango_fibo_bajista(self,escala):
        
        pxfc = self.retrocesos_fibo_macd(escala,5) 
        
        if pxfc[0] == 0:
            rmin = 0
            rmax = 0
        else:
            atr = self.atr_bajos(escala,top=10)
            rmin = pxfc[1] - atr 
            rmax = pxfc[0] + atr

        return  rmin, rmax


    
    def rango_ema(self,escala,periodos,prango_max=2,cvelas=None):
        ''' retorna el rango_actual y el rango que no se supere el prango_max
            tambien retorna la vela donde se superó el rango o la ultima vela posible 
            siempre contando desde lo mas nuevo a lo mas viejo
        '''    
        self.actualizar_velas(escala)
        vclose = self.velas[escala].valores_np_close()

        ema=talib.EMA(vclose, timeperiod=periodos)

        

        lx = ema.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        #la ultima vela se descarta que es px y es al base del calculo del rango actual
        px = ema[lx-1]
        rango_actual=abs(round( (ema[lx-2] / px -1 ) * 100 ,2))



        #comienzo de busqueda de rango maximo
        prango= rango_actual
        # 
        for i in range(lx - 3, lx-1-cvelas,-1):
            
            irango= abs(round( (ema[i] / px -1) * 100 ,2))

            #print(i,prango)
            if irango > prango_max:
                break
            
            prango = irango # esta rango es bueno, me lo quedo
        
        vela = lx - 3 - i  # lx -1 - i-1

        return  rango_actual, prango, vela
    
    def rango_minimo_promedio(self,escala,top=100,cvelas=None):
        ''' retorna el promedio de las top(velas) mas chicas en cuanto a su rango porcentual
            tomando las cvelas indicadas, por defecto todas
        '''    
        
        self.actualizar_velas(escala)
        vopen  = self.velas[escala].valores_np_open()
        vclose = self.velas[escala].valores_np_close()

        lx = vopen.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        #contruyo lista de rangos 
        vrangos=[]
        px = self.velas[escala].ultima_vela().close
        for i in range(lx - cvelas, lx-1):
            mi , ma =  self.__valor_menor_mayor(vopen[i],vclose[i])
            if mi < ma:
               rango_vela = (ma / mi  - 1 ) * 100
               vrangos.append(rango_vela)
               

        #ordeno 
        vrangos.sort() 
        
        #elimino el 5% de las muestras mas chicas obtenidas 
        eliminar= int( len(vrangos) * 0.07 ) 
        for i in range(0,eliminar):  
            vrangos.pop(0) 
        
        #hago promedio
        sumatop=0
        i=0
        ultimo=len(vrangos)
        while i < top:
            sumatop += vrangos[i]
            i += 1
            
            if i ==ultimo:
                break

        return  round(sumatop/i,2)   
    
    def patron_180(self,escala,vela_inicial=0):
        '''
        Esta funcion intenta detctar el patron 180 explicado en https://www.youtube.com/watch?v=W8nQVFTeN2g
        '''
        ret = 0
        self.actualizar_velas(escala)
        vpen: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial+1) #penultima vela
        #analizo que la penultima vela sea roja y de cuerpo grande
        if vpen.sentido() == -1: #bajista analizamos cuerpo
            mechas=vpen.sombra_sup() + vpen.sombra_inf()
            tot = vpen.cuerpo() + mechas
            if tot == 0:
                relacion = 0
            else:
                relacion =  vpen.cuerpo() / ( tot ) 


            #rsi=self.rsi(escala,vela_inicial+1)   
            atr=self.atr(escala,0,3)[0] #el atr anterior a la penuntima vela
            if atr == 0:
                xatr=0
            else:
                xatr = vpen.cuerpo() / atr

            varvela= variacion(vpen.open,vpen.close)   
            
            if relacion > 0.7 and varvela > self.var_velas[escala] and xatr > 1.5: # bajista     
                self.log.log(self.par,'relacion',relacion,'varvela',varvela,'xatr',xatr)
                ret = 0.5
                vult: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial) #ultima vela, en desarrollo
                if vult.sentido() == 1: 
                    ret = 0.6
                    varcuerpo = compara(vpen.cuerpo(),vult.cuerpo())
                    #self.log.log(self.par,'vela+',varcuerpo,vpen.cuerpo(),vult.cuerpo())
                    if vpen.low <= vult.low and variacion(vpen.close,vult.open) < 1 and\
                        -20  < varcuerpo < 5:  #la ultima vela cancela a la anterior al menos en un 90%
                        ret = 0.75
                        ema = self.ema(escala,20)
                        if vpen.open > ema and vpen.close < ema or variacion(vpen.open,ema) < 1 or variacion(vpen.close,ema) < 1: #la vela cora la ema o está a menos del 1%
                            ret = 1
        return ret

    def patron_rebote_macd(self,escala,vela_inicial=0):
        '''
        Busca una vela negativa gorda, y la siguiente positiva.
        con macd minimo
        
        '''
        ret = 0
        self.actualizar_velas(escala)
        vpen: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial+1) #penultima vela
        #analizo que la penultima vela sea roja y de cuerpo grande
        if vpen.sentido() == -1: #bajista analizamos cuerpo
            mechas=vpen.sombra_sup() + vpen.sombra_inf()
            tot = vpen.cuerpo() + mechas
            if tot == 0:
                relacion = 0
            else:
                relacion =  vpen.cuerpo() / ( tot ) 


            #rsi=self.rsi(escala,vela_inicial+1)   
            atr=self.atr(escala,0,3)[0] #el atr anterior a la penuntima vela
            if atr == 0:
                xatr=0
            else:
                xatr = vpen.cuerpo() / atr

            varvela= variacion(vpen.open,vpen.close)   
            
            if relacion > 0.1 and varvela > self.var_velas[escala] and xatr > 1.5: # bajista     
                ret = 0.5
                vult: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial) #ultima vela, en desarrollo
                if vult.sentido() == 1:
                    macd =self.busca_macd_hist_min(escala,vela_inicial)
                    if macd[0]>-1 and macd[1]<2 and  macd[4]>3: #encontró minimo,[4] 3 o mas velas negativas, [1] distancia <2
                        ret = 1
                    self.log.log(self.par,'relacion',relacion,'varvela',varvela,'xatr',xatr,'macd',macd)

        return ret

    def patron_seguidilla_negativa_rebote_macd(self,escala,vela_inicial=0):
        '''
        Busca una seguidilla de velas negativas, y la siguiente positiva.
        con macd minimo
        
        '''
        ret = 0
        self.actualizar_velas(escala)
        i=1
        neg: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial+i) # vela negativa inicial
        #analizo que la penultima vela sea roja y de cuerpo grande
        if neg.sentido() == -1: #bajista analizamos cuerpo
            vpen = neg
            tvelas= len(self.velas[escala].df) 
            while tvelas - vela_inicial - i - 1 >= 0:
                negant = neg
                i +=1
                neg: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial+i)
                if neg.sentido() == 1: #busco el final de la seguidilla
                    vpen.high = negant.high
                    vpen.open = negant.open
                    break

            #rsi=self.rsi(escala,vela_inicial+1) 
            if i > 3: #cantidad mínima de velas negativas  
                
                atr=self.atr(escala,0,3)[0] #el atr anterior a la penuntima vela
                if atr == 0:
                    xatr=0
                else:
                    xatr = vpen.cuerpo() / atr

                varvela= variacion(vpen.open,vpen.close)   
                
                if varvela > self.var_velas_seguidas[escala] and xatr > 2: # bajista     
                    ret = 0.5
                    vult: Vela = self.velas[escala].get_vela_desde_ultima(vela_inicial) #ultima vela, en desarrollo
                    if vult.sentido() == 1:
                        macd =self.busca_macd_hist_min(escala,vela_inicial)
                        if macd[0]>-1 and macd[1]<2 and  macd[4]>1: #encontró minimo,[4] 2 o mas velas negativas, [1] distancia <2
                            ret = 1
                            self.log.log(self.par,'var_seguidilla',varvela,'xatr',xatr,'macd',macd)

        return ret


    def sentido_vela(self,escala,vela_desde_ultima=0):
        self.actualizar_velas(escala)
        v: Vela = self.velas[escala].get_vela_desde_ultima(vela_desde_ultima)
        return v.sentido() 







    #esto todavia no está listo... reaprendiendo estadística
    def rango_porcentaje_acumulado(self,escala,tipo,porcentaje_casos=10,redondeo=2):
        ''' Retorna un porcentaje de rango minimo o maximo de una lista ordenada de casos agrupados por repeticiones.
            Ese porcentaje sería suficiente para cubrir todos los casos anteriores que son rangos inferiores
            escala = 1m..1M, tipo -1 = minimo, tipo = 1 maximo, porcentaje_casos = 10 por defecto
        '''    
        restar_velas=1
        self.actualizar_velas(escala)
        vopen  = self.velas[escala].valores_np_open()
        vclose = self.velas[escala].valores_np_close()

        lx = vopen.size
        cvelas=lx
        
        #contruyo dict rangos 
        drangos={}
        px = self.velas[escala].ultima_vela().close
        tcasos=0
        for i in range(lx - cvelas, lx-1):
            mi , ma =  self.__valor_menor_mayor(vopen[i],vclose[i])
            if mi < ma:
                tcasos += 1
                rango_vela = round( (ma / mi  - 1 ) * 100,redondeo)
                if rango_vela in drangos:
                    drangos[rango_vela] += 1
                else:
                    drangos[rango_vela] = 1

        #construyo histograma
        vrangos=[]
        for k in drangos.keys():
            
            vrangos.append (  [ k,drangos[k] ]   )

        if tipo == -1:
            vrangos.sort (key=lambda x: x[0]) #ordento los datos de menor a mayor
        else:
            vrangos.sort (key=lambda x: x[0], reverse=True) #ordento los datos de mayor a menor
                   
        suma_porcentaje=0
        ret=0
        for r in vrangos:
            
            suma_porcentaje += r[1]/tcasos * 100
            if suma_porcentaje >= porcentaje_casos:
                ret = r[0] #encontré el valor que abara a todos los casos inferiors a porcentaje_casos
                print ( '----------------------->',ret )
                break

        return  ret

    def __valor_menor_mayor(self,v1,v2):
        if v1 < v2:
            menor = v1
            mayor = v2
        else:
            menor = v2
            mayor = v1
        
        return menor, mayor    
                
    def retroceso_fibo_mm(self,escala,periodos=200,soporte=0):
        mm=self.max_y_luego_min(escala,periodos,periodos)
        px=self.precio(escala)
        minimo=mm[0]
        maximo=mm[1]
        
        sop=-1
        ret=minimo
        for f in (self.fibo):
            ret=maximo - (maximo-minimo) * (100 - f)  / 100  
           
            if ret < px:
                sop+=1
                if sop==soporte:
                    break
        if ret > px:
            ret=px

        return ret        
    
    def retroceso_fibo(self,precio,nivel=1):
        return  precio * self.fibo[nivel-1] / 100

    
    #si retorna valores positivos altos 10% o mas (a estuiar) la volatilidad a aumentado
    #si retorna valores negativos la volatilidad ha disminuido
    def variacion_atr_mm(self,escala,periodos_hacia_max=200,periodos_hacia_min=199):
        mm=self.max_y_luego_min(escala,periodos_hacia_max,periodos_hacia_min)
        amin=self.atr(escala, mm[2])
        amax= self.atr(escala, mm[3])
        return round(1-amin/amax,2)*100

    def precio_mas_actualizado(self):
        mas_actualizado = sorted(self.actualizado.items(), key=lambda x: x[1] ,reverse=True   )[0]
        if time.time() - mas_actualizado[1] < 60: # el precio mas actualizado tiene menos de un minuto
            
            
            return self.precio(mas_actualizado[0]) #retorno el precio del mas actualizado
        else:
            
            return self.precio('4h')   
            





