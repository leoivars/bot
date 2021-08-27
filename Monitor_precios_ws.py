# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member
import time
import datetime
import sys

from binance.client import Client
from pws import Pws
from actualizaciones_par import ActualizacionesWS
from controlador_de_tiempo import Controlador_De_Tiempo
import statistics 
import numpy as np
import talib

# HAY QUE REEMPLAZAR LOS BINANCE WEB SOCKETS POR POR WEBSOCKETS DE MERCADO 


#trataré de hacer el lector de precios con websockets, no est'a terminaod eso


class MonitorPreciosWs:
    cantidad_de_muestras=600 #aprox 3 minutos #300 aprox 15 minutos 
    operando=False
    precios={}
    

    def __init__(self, log): 
        
        self.log=log 
        
        self.client = None
        self.crear_cliente()
        
        self.minuto=Controlador_De_Tiempo(60)
        self.precios_minuto=0
        self.__utima_actualizacion=time.time()

        self.bm=None #BinanceSocketManager(self.client)
        
    

    def crear_cliente(self):
        if self.client != None:
            self.log.err( "Re creando Cliente")
            time.sleep(35)
            self.client = None
            del self.client 
        pws=Pws()
        while True:
            try:
                self.client= Client(pws.api_key, pws.api_secret, { "timeout": (10, 27)})  #timeout=(3.05, 27
                break
            except Exception as e:
                self.log.err( "XXX No se puede crear Cliente",str(e))
                self.client = None
                time.sleep(35)
                del self.client     

    def empezar(self):
        self.bm=BinanceSocketManager(self.client)
        self.conn_key = self.bm.start_miniticker_socket(self.process_message,3000)
        print('MonitorPreciosWs empezando',self.conn_key)
        self.bm.start()

    def detener(self):
        print ('MonitorPreciosWs deteniendo')
        #print (self.conn_key,self.bm.stop_socket(self.conn_key)  )
        #print(  self.bm.stop_socket(self.conn_key) )
        self.bm.stop_socket(self.conn_key) 
        
                
    def morir(self):
        self.log.log ('MonitorPrecios.ws: Adios mundo cruel...')

        self.bm.close()
      
        del self.bm
        del self.client
        

    def reconectar(self):
        self.detener()
        time.sleep(5)
        self.conn_key = self.bm.start_miniticker_socket(self.process_message,3000)    
        
        
    def cerrar(self): # esto se usa al final del programa para que libere todos los recursos
        pass
        #reactor.stop_socket()

    def process_message(self,msg):
        #print("message type: {}".format(msg['e']))
        #print ('---> recibiendo')
        #print(msg)
        try:
            self.agregar_precios(msg)
        except Exception as e:
            self.log.err( 'agregar_precios',str(e))        
   
    
    def pendientes(self,simbol):
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            pf=self.calcular_ultimas_pendientes(pxs,self.cantidad_de_muestras)
            media=0
            desv=0

            if len(pf) > 0:
                media=statistics.mean(pf)
                desv=statistics.stdev(pf,media)
                
            for  p in pf:
                try:
                    varp = p/media
                except:
                    varp = 0
                        
                if abs(varp) > 50:
                    print(p,varp)

            #print ('media',media)
            #print ('dev  ',desv)    


    def imprimir(self,msg):
        print('imprimir')
        for k in msg:
            if k["s"]=='BTCUSDT':
                for i in k.keys():
                    print(i,'----->',k[i])


    def agregar_precios(self,msg):

        cant_precios=len(msg)

        self.__utima_actualizacion = time.time()
        if self.minuto.tiempo_cumplido():
            self.precios_minuto=0
        else:
            self.precios_minuto += cant_precios    

            

        
        for p in msg:
            simbol = p["s"]
            precio = [   float(p["c"]) ,  int(p["E"])  ]
            

            ingresar = False
            if ( simbol.endswith('BTC') or simbol.endswith('USDT') ):# and MonitorPreciosWs.lista_negra_de_pares.index(simbol)==-1:
                ingresar = True 


            if ingresar:
                if simbol in MonitorPreciosWs.precios:
                    #sumo uno al actualizador 
                    MonitorPreciosWs.precios[simbol][ 1 ].sumar_actualizacion()
                    
                    #agrego el precio
                    MonitorPreciosWs.precios[simbol][ 0 ].append(precio)
                    if len( MonitorPreciosWs.precios[simbol][ 0 ] ) > self.cantidad_de_muestras:
                        MonitorPreciosWs.precios[simbol][ 0 ].pop(0)
                else:
                    MonitorPreciosWs.precios[simbol]=[ [precio] , ActualizacionesWS() ]

        
        #print('---------------WS----------WS--------------WS-------->',len(msg),self.precios_minuto)       

    
    def estado_general(self,moneda_contra='BTC'):
        ret={'bajando':0,'nobajando':0}
        for s in MonitorPreciosWs.precios.keys():
            if s.endswith(moneda_contra):
                #print (s)
                if self.ema_precio_no_baja(s):
                    ret['nobajando'] +=1
                else: 
                    ret['bajando']  +=1    
            
        return ret

    def precio_no_baja(self,simbol):
        '''retorna true si el precio no baja 
           monitoreado a partir de 5 pendientes frescas
        ''' 
        ret = False
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            pf=self.calcular_ultimas_pendientes(pxs)
            #print (pf)
            if len( pf ) > 0:
                cant_pend_ok =0
                for p in reversed(pf):
                    if p >= 0:
                        cant_pend_ok += 1
                        if cant_pend_ok >=5:
                            ret = True
                            break
                    else:
                        ret = False
                        break

        return ret


    def ema_precio_no_baja(self,simbol,periodos_ema=10):
        '''retorna true si el precio no baja
        ''' 
        ret = False
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            #print(pxs)
            if len(pxs) > periodos_ema: 
                vector = []
                for p in pxs:
                    vector.append(p[0])

                np_precios = np.array(vector)    
                ema=talib.EMA(np_precios, timeperiod=periodos_ema)

                ret = ( ema[ema.size -2] <= ema[ema.size -1] )
                #print (ema[ema.size -2] , ema[ema.size -1], ret )
            else:
                #print ('ema_no_baja; sin datos')    
                pass

        return ret


    def variacion_precio(self,simbol):
        '''retorna la direncia entre el precio mayor
           y el precio menor registrado
        ''' 
        ret = 0
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            max=pxs[0][0]
            min=pxs[0][0]
            for i in range(1,len(pxs)):
                if pxs[i][0] > max:
                    max=pxs[i][0]
                elif pxs[i][0] < min:
                    min=pxs[i][0]    
                ##print (pxs[i][0]  )    

            ret = max - min 

            #print(pxs)
        return ret
    
    def lista_precios(self,simbol):
       
       if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
       else:
            pxs =[ [0,0]]     

       lista=[]
       for p in pxs:
           lista.append(p[0])
       return lista    

    def promedio_de_altos(self,simbol,top=10):
        ''' retorna un promedio de los top mas altos
            de todas las velas memorizadas
        '''    
        lprecios =self.lista_precios(simbol)

        #correciones de entradas erroneas
        if top < 2:
            top = 2
        fin = top 
        lx = len(lprecios) 
        if fin > lx:
            fin = lx 

        lprecios.sort(reverse=True) #odenada de menor a Mayor

        suma=0
        cant=0
        for i in range(0,fin):
            suma+=lprecios[i]
            cant+=1

        try:
            ret = suma/cant
        except:    
            ret = 0
        
        return ret     

    def precio(self,simbol):
        ret = -1
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            ret = pxs[ len(pxs) - 1 ][0]
        return ret    

    def precio_fecha(self,simbol):
        
        ret = None
        
        if simbol in MonitorPreciosWs.precios:
            pxs = MonitorPreciosWs.precios[simbol][0]
            ret = pxs[ len(pxs) - 1 ]

        return ret 

    def calcular_ultimas_pendientes(self,pxs,cant_pend=5):
        #print(pxs)
        pultimo = len( pxs ) - 1
        pendientes_frescas=[]
        if pultimo > 1:
            primero = pultimo - cant_pend # solo tomo 5 cantidad_de_muestras por defecto
            if primero < 0:
                primero = 0
            vultimo = pxs[ pultimo ]
            #antiguedad =  time.time() - vultimo[1]/1000
            for i in range(primero,pultimo):
                dy = vultimo[0] - pxs[i][0] 
                dx = vultimo[1] - pxs[i][1] 
                try:
                    pendientes_frescas.append(  dy / dx )
                except:
                    pendientes_frescas.append(  0 )    
        
        return pendientes_frescas   

    def comparar_actualizaciones(self,simbol_a,simbol_b,horas=0):
        
        try:
            if datetime.datetime.now().minute < 7: # no entrego datos durante los primeros 7 minutos para juntar valores
                return 0 

            #calculo el indice de simbol_a
            if simbol_a in self.precios:
                l = len(self.precios[simbol_a][1].actualizaciones)    
                if l > 0:
                    i = l - 1 - horas
                    if i >= 0:
                        act_a = self.precios[simbol_a][1].actualizaciones[ i ]
                    else:
                        act_a = 0    
                else: 
                    act_a = 0    
            else:
                act_a = 0

            #calculo el indice de simbol_b
            if simbol_b in self.precios:
                l = len(self.precios[simbol_b][1].actualizaciones)    
                if l > 0:
                    i = l - 1 - horas
                    if i >= 0:
                        act_b = self.precios[simbol_b][1].actualizaciones[ i ]
                        if act_b == 0: # no puede ser cero, es un divisor
                            act_b = 1
                    else:
                        act_b = 1    
                else: 
                    act_b = 1
            else:
                act_b = 1                
            ret = round(act_a/act_b,3)

        except Exception as moco:
            ret = 0
            self.log.log('-----ERROR---comparar_actualizaciones.MonitorPreciosWs',str(moco))       

        return ret

    def lista_actualizaciones(self):
        sb='BTCUSDT'
        lista = []
        for s in self.precios:
            if s != sb:
                lista.append( [s,self.comparar_actualizaciones(s,sb)] )

        lista.sort(key=lambda x:x[1],reverse=False) #ordeno 

        for i in lista:
            if i[0].endswith('BTC'):
                print(i)

    def ultima_actualizacion(self):
        return int( time.time() - self.__utima_actualizacion)

        




     


    