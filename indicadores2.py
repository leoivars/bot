# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from math import atan, degrees, fabs
from pymysql.constants.ER import NO
#from pandas.core.missing import pad_2d
import talib
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
from datetime import datetime, timedelta
#from market_profile import MarketProfile
import pandas as pd
import pandas_ta as ta

from  variables_globales import VariablesEstado

from funciones_utiles import strtime_a_fecha, strtime_a_obj_fecha, variacion,compara,signo, variacion_absoluta
from mercado import Mercado
from mercado_back_testing import Mercado_Back_Testing
from vela_op import *

import inspect 




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

     
    
        
    def __init__(self,par,log,estado_general, mercado):
        pd.set_option('mode.chained_assignment', None)

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
        
        #self.client = cliente
        
        #self.lock_actualizador= Lock()
        self.prioridad = 0
        
        self.mercado = mercado

        self.cache={}

    def cache_add(self,parametros,valor):
        funcion_que_me_llamo = inspect.stack()[1][3] 
        self.cache[(funcion_que_me_llamo,parametros)] =(time.time(),valor)

    def cache_txt(self):
        txt = ''
        for t in self.cache:
            txt += f'{str(t)} {str(self.cache[t])}   \n'
        return txt    

    
    def min(self,escala,periodos):
        'entrega el minimo en una escala de los n periodos hacia atrás'

        vmin=self.mercado.get_vector_np_close(self.par,escala,periodos+2)
        l=vmin.size


        if periodos>l-1:
            p=l-1
        else:
            p=periodos

        min=vmin[l-1]
        
        for i in range(l-p,l):
            #print (min,vmin[i],max,vmax[i])
            if vmin[i]<min:
                min=vmin[i]
        return min
        
   
   

    def buscar_precio_max_rsi(self,escala,rsi_superior,rsi_inferior):
        '''estableze un rango buscando primero un rsi_superior y luego un rsi_inferior,
        luego retorna el precio maximo en ese rango y la variacion con rescpecto al precio actual'''
        df=self.mercado.get_panda_df(self.par,escala,200 ) 
        rsi = df.ta.rsi()
        #busco hacia atrás el rsi mayor al mínimo
        pxmax =0
        i=-1
        ini= len(rsi) *-1
        while ini<=i and  rsi.iloc[i] < rsi_superior:
            i -=1
        while ini<=i and  rsi.iloc[i] > rsi_inferior:
            i -=1
        
        if i<ini:
            zona_ini =ini
        else:    
            zona_ini =i

        #ahora que tengo al zona, saco el maximo
        pxmax = df.iloc[zona_ini]['high']
        pxmin = df.iloc[zona_ini]['low']
        for i in range(zona_ini,-1): #zona ini menor que -1
            
            pxmax=max( pxmax  ,df.iloc[i]['high']  )
            pxmin=min( pxmin  ,df.iloc[i]['low']  )
            #print(pxmax,pxmin)

        return pxmax,variacion_absoluta(pxmax,pxmin)  

    
    # la idea de este indicador es calcular el minimo y el maximo en un cierta cantidad de velas
    # y la relacion con el precio actual, o sea desde la ultima vela hacia atras.
    # lo que se pretende es establecer un precio y un porcentaje hacia el precio minimo 
    # lo mismo para maximo
    # para tratar de determinar cuando sería una toma de ganancia o perdidas.
    def minmax(self,escala,periodos):
        
        vmax= self.mercado.get_vector_np_high(self.par,escala)
        vmin= self.mercado.get_vector_np_low(self.par,escala)
        precio=self.precio_mas_actualizado()
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
        vs:VelaSet = self.mercado.par_escala_ws_v[self.par][escala][1]
        l=len(vs.df)

        if periodos>l-1:
            p=l-1
        else:
            p=periodos

        for i in range(l-p,l):
            v=vs.get_vela(i)

            self.log.log(i, v.open, v.high, v.low, v.close, v.volume, v.open_time, v.close_time)

    
    
    def rsi_minimo(self,escala,close=None):
        ''' retorna el rsi minimo local y el rsi actual
        '''
        if close is None:
            
            c = self.mercado.get_vector_np_close(escala)
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

    def rsi_contar_picos_minimos(self,escala,cvelas,menor_de):
        ''' cuanta la cantidad de picos minimos desde el final por cvelas 
        para rsi menor que el param menor_de'''    
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 60) #self.velas[escala].panda_df(cvelas + 60)
        rsi = df.ta.rsi()

        l=len(rsi)
        lneg = l * -1
        picos = 0
        
        
        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if rsi.iloc[i]<menor_de and self.hay_minimo_en(rsi,i):
                print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                picos +=1
        return picos        
    

    def volumen_por_encima_media(self,escala,cvelas,xvol = 1):
        ''' suma el volumen de las ultimas cvelas multipolicado por xvol
         y lo compara con el volumen promedio si es mayor
         retorna verdadero '''  
        if cvelas == 0:
            return False

        df=self.mercado.get_panda_df(self.par, escala, cvelas + 25)
        
        vol_ma =ta.ma('ma',df['Volume'],length=20)
        
        #ultimas dos velas
       
        #cvelas_encima_de_la_media 
        vo_ma=0
        vo_velas = 0

        for i in range(-cvelas,0):
            vo_velas += Vela(df.iloc[i]).volume
            vo_ma    += vol_ma.iloc[i]

        self.log.log(f'{vo_velas/cvelas * xvol} > {vo_ma / cvelas}')

        return vo_velas/cvelas * xvol > vo_ma / cvelas    

    def ultima_vela_cerrada(self,escala):
        df=self.mercado.get_panda_df(self.par, escala, 3)
        #print(df['closed'])
        print(df.iloc[-1]['closed'])

        if df.iloc[-1]['closed']:
            v = Vela(df.iloc[-1])
        else:
            v = Vela(df.iloc[-2])
        return v    

    def hay_minimo_en(self,df,p,entorno=5):
        lado_uno=False
        fin = -1
        i=p+1
        c_entorno=0
        while i <= fin and c_entorno < entorno:
            if df.iloc[p] < df.iloc[i]:
                lado_uno=True
                break
            elif df.iloc[p] > df.iloc[i]:
                break
            i +=1
            entorno +=1

        lado_dos=False
        ini = len(df) * -1
        i=p-1
        c_entorno=0
        while ini <= i and c_entorno < entorno:
            if df.iloc[p] < df.iloc[i]:
                lado_dos=True
                break
            elif df.iloc[p] > df.iloc[i]:
                break
            i -=1
            entorno +=1

        return lado_uno and lado_dos    

    def rsi_contar_picos_maximos(self,escala,cvelas,mayor_de):
        ''' cuanta la cantidad de picos maximo desde el final por cvelas 
        para rsi mayor que el param mayor_de'''    
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 60) #self.velas[escala].panda_df(cvelas + 60)
        rsi = df.ta.rsi()

        l=len(rsi)
        lneg = l * -1
        picos = 0
        
        
        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
            if rsi.iloc[i]>mayor_de and self.hay_maximo_en(rsi,i):
                
                picos +=1
        return picos        

    def hay_maximo_en(self,df,p,entorno=5):
        lado_uno=False
        if p > -1: #posicion de p en forma positiva
            ini = 0
            fin = len(df)-1
        else:
            ini = (len(df)-1) * -1
            fin = -1
        i=p+1
        c_entorno=0
        while i <= fin and c_entorno < entorno:
            if df.iloc[p] > df.iloc[i]:
                lado_uno=True
                break
            elif df.iloc[p] < df.iloc[i]:
                break
            i +=1
            entorno +=1

        lado_dos=False
        i=p-1
        c_entorno=0
        while ini <= i and c_entorno < entorno:
            if df.iloc[p] > df.iloc[i]:
                lado_dos=True
                break
            elif df.iloc[p] < df.iloc[i]:
                break
            i -=1
            entorno +=1

        return lado_uno and lado_dos    


    def rsi_minimo_y_pos(self,escala,cvelas):
        ''' retorna el rsi minimo de las c velas, su posición y el rsi actual
        '''
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 90) #self.velas[escala].panda_df(cvelas + 60)
        rsi = df.ta.rsi()
      
        minimo = 100
        l=len(rsi)
        mi = 0
        
        try:
            lneg = l * -1
            i = -1
            minimo = rsi.iloc[-1]
            mi = 1
            cvel = 1
            # print(f'if {rsi.iloc[-2]} < {rsi.iloc[-1]}:')
            while i > lneg:
                i -= 1
                cvel += 1
                if cvel > cvelas:
                    break
                # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
                if rsi.iloc[i] < minimo:
                    mi = i
                    minimo = rsi.iloc[i]
            
        except Exception as e:
            self.log.log(str(e)) 

        ret =  (minimo,mi*-1,rsi.iloc[-1])    
        self.cache_add( (escala,cvelas),ret )

        return    ret
    
    def volumen_calmado(self,escala):
        ''' considera calmado al volumen de ultima vela cerrada
            si se encuentra por debajo del promedio
        '''
        df=self.mercado.get_panda_df(self.par, escala, 90) #self.velas[escala].panda_df(cvelas + 60)
        df_ema=ta.ma('ma',df['Volume'],length=20)
        
        if df.iloc[-1]["closed"]:
            i = -1
        else:
            i= -2
        ret =  df.iloc[i]["Volume"] < df_ema.iloc[i]

        #self.log.log(f'vol {df.iloc[i]["Volume"]} < ema-vol {df_ema.iloc[i]}') 
        return ret
        


    def sar(self,escala,vela_ini=0):
        h=self.mercado.get_vector_np_high(self.par,escala) #   self.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(self.par,escala)  #     self.get_vector_np_low(escala)
        vsar=talib.SAR(h,l, acceleration=0.02, maximum=0.2)
        vela = -1 + vela_ini * -1

        return float(vsar[vela]) # -2 es la ultima vela cerrada -1 vela en desarrollo 


    
    def macd(self,escala):
        
        close = self.mercado.get_vector_np_close(escala)
        
        r_macd, r_macdsignal, r_macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        l=len(r_macd)-1
        
        return [r_macd[l], r_macdsignal[l], r_macdhist[l]]

    def macd_analisis(self,escala,cvelas):
        
        close = self.mercado.get_vector_np_close(escala)
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

        
        close = self.mercado.get_vector_np_close(escala)
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

        
        close = self.mercado.get_vector_np_close(escala)
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
        
        close = self.mercado.get_vector_np_close(escala)
        _, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.mercado.get_vector_np_low(escala)
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
        
        close = self.mercado.get_vector_np_close(escala)
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

        
        hist,sqz = self.sqzmon_lb(escala)
        low  = self.mercado.get_vector_np_low(escala)
        high = self.mercado.get_vector_np_high(escala)
        close = self.mercado.get_vector_np_close(escala)

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
        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.mercado.get_vector_np_low(escala)
        high = self.mercado.get_vector_np_high(escala)
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

        
        close = self.mercado.get_vector_np_close(escala)
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
            vi: Vela = self.mercado.velas[escala].get_vela(imin)
            vf: Vela = self.mercado.velas[escala].ultima_vela()

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
            #vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 10) 
            close = self.mercado.get_vector_np_close(self.par,escala)
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
 

    

    
                    
    def busca_rsi_menor(self,escala,rsi_menor,cant_velas):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
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


          

    

    
    
    def tres_emas_favorables2(self,escala,per1=9,per2=20,per3=55):
        '''
          Saca las tres emas y si están ordenadas y al mismo tiempo la distancia entre ellas 
          es menor a pchica retorna verdadero
        '''
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per3 +10) 
        
        ordenadas= False
        positivas = False
        sar_ok = True

        vema1=talib.EMA(vector, timeperiod=per1)
        if vema1[-1] > vema1[-2] and vema1[-1]>vema1[-3] and vema1[-1]>vema1[-4] and vema1[-1]>vema1[-5]:
            vema2=talib.EMA(vector, timeperiod=per2)
            if vema2[-1] > vema2[-2] and  vema2[-1]>vema2[-3]:
                vema3=talib.EMA(vector, timeperiod=per3)
                if vema3[-1] > vema3[-2]:
                    positivas = True

        if positivas:            
            ema1=vema1[-1]
            ema2=vema2[-1]
            ema3=vema3[-1]
            
            # uv:Vela = self.mercado.par_escala_ws_v[self.par][escala][1].ultima_vela()
            # vela_corta_ema3 = uv.signo ==1 and uv.open < ema3 < uv.close
                


            if ema1 > ema3 and  ema2 > ema3 : # las dos emas rápidas mayor que la lenta
                ordenadas=True
                sar = self.sar(escala)
                px = self.precio_mas_actualizado()
                if sar < px:
                    sar_ok = True

                # p1=self.pendientes(escala,vema1[-2:],1)[0]  
                # p2=self.pendientes(escala,vema2[-2:],1)[0] 
                # p3=self.pendientes(escala,vema3[-2:],1)[0] 

                # vema4=talib.EMA(vector, timeperiod=55)
                # p4=self.pendientes(escala,vema4[-2:],1)[0]
                

                # self.log.log('ang,p1--->',self.angulo_de_dos_pendientes(0,p1))
                # self.log.log('ang,p2--->',self.angulo_de_dos_pendientes(0,p2))
                # self.log.log('ang,p3--->',self.angulo_de_dos_pendientes(0,p3))
                # self.log.log('ang,p4--->',self.angulo_de_dos_pendientes(0,p4))
                # dfin=vema1[-1]-vema2[-1]
                # dini=vema1[-3]-vema2[-3]
                # ampliandose = dfin >0 and dini>0 and dfin>dini
                #ampliandose = self.distancia_entre_emas_ampliandose(self.g.zoom_out(escala,1),per1,per2,3)
        
        return (positivas and ordenadas and sar_ok) #and ampliandose)

    def dos_emas_favorables(self,escala,per1=9,per2=20):
        '''
          Saca las dos emas si la rápida > que lenta y sar por debajo del precio, ok

        '''
        rsi = self.rsi_vector(escala,cvelas=5)
        if not ( rsi[-1] > rsi[-2] and rsi[-1]>rsi[-3] and rsi[-1]>rsi[-4] ) :
            return False

        vector=self.mercado.get_vector_np_close(self.par,escala,per2 +30) 
        
        ordenadas= False
        positivas = False
        sar_ok = True

        vema1=talib.EMA(vector, timeperiod=per1)
        if vema1[-1] > vema1[-2] and vema1[-1]>vema1[-3] and vema1[-1]>vema1[-4] and vema1[-1]>vema1[-5]:
            vema2=talib.EMA(vector, timeperiod=per2)
            if vema2[-1] > vema2[-2] and  vema2[-1]>vema2[-3]:
                positivas = True

        if positivas:            
            ema1=vema1[-1]
            ema2=vema2[-1]
            
            # uv:Vela = self.mercado.par_escala_ws_v[self.par][escala][1].ultima_vela()
            # vela_corta_ema3 = uv.signo ==1 and uv.open < ema3 < uv.close

            if ema1 > ema2:
                ordenadas=True

                sar = self.sar(escala)
                px = self.precio_mas_actualizado()
                if sar < px:
                    sar_ok = True

                
        return (positivas and ordenadas and sar_ok)

    
    def distancia_entre_emas_ampliandose(self,escala,rapida,lenta,velas_de_distancia):
        vector=vector=self.mercado.get_vector_np_close(self.par,escala,lenta +30)
        vema_rap=talib.EMA(vector, timeperiod=rapida)
        vema_len=talib.EMA(vector, timeperiod=lenta)
        iantes = velas_de_distancia * -1
        distancia_ahora = vema_rap[-1] - vema_len[-1]
        distancia_antes = vema_rap[iantes] - vema_len[iantes]
        if distancia_ahora > 0 and distancia_antes > 0 and distancia_antes > distancia_ahora:
            return True
        else:
            return False    


    def angulo_de_dos_pendientes(self,m1,m2):
        '''
        m1 es la pendiente mas suave
        m2 la mas rápida
        '''
        return degrees(atan( abs(m2-m1)/abs(1+m1*m2)  ) )

    #retorna verdadero si la ema rápida está por debajo de la lenta
    def ema_rapida_menor_lenta(self,escala,per_rapida,per_lenta):
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 10) 
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)
        r = emar[-1]
        l = emal[-1]
        self.log.log('ema_rapida_menor_lenta',r,l)
        return r < l



    #retorna verdadero si la ema rápida está por encima de la
    def ema_rapida_mayor_lenta(self,escala,per_rapida,per_lenta,diferencia_porcentual_minima=0):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es mayor diferencia_porcentual_minima, retora verdadero'''
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        df_emar=ta.ema(df['Close'],length=per_rapida) 
        df_emal=ta.ema(df['Close'],length=per_lenta)  

        #print(df)
        #print(df_emal.to_list())
        #print(df_emal.iloc[-1])

        r = df_emar.iloc[-1] 
        l = df_emal.iloc[-1] 

        try:
            diferencia_porcentual= (( r / l ) -1 )  * 100
        except:
            diferencia_porcentual= -100

        #if diferencia_porcentual_minima >0:
        self.log.log(f'l {l},r {r},dif%  {diferencia_porcentual}, dif%min{diferencia_porcentual_minima}') 

        return diferencia_porcentual > diferencia_porcentual_minima

    def ema(self,escala,periodos):
        
        df=self.mercado.get_panda_df(self.par,escala,periodos+100)
        df_ema=ta.ema(df['Close'],length=periodos) 
        ret = df_ema.iloc[-1]

        self.cache_add( (escala,periodos),ret  )
        
        return ret

    def ema_rapida_mayor_lenta2(self,escala,per_rapida,per_lenta,diferencia_porcentual_minima=0,pendientes_positivas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es mayor diferencia_porcentual_minima o las pendientes
        de ambas emas son positivas  retorna True, tambien retorna datos para log..
        si pendientes_positivas=True exige que las pendientes sean positivas al mismo tiempo que se de la diferencia porcentual''' 
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        df_emar=ta.ema(df['Close'],length=per_rapida) 
        df_emal=ta.ema(df['Close'],length=per_lenta)  

        # r = df_emar.iloc[-1] 
        # l = df_emal.iloc[-1] 
        r = self.ema(escala,per_rapida)
        l = self.ema(escala,per_lenta)

        pend_r=self.pendientes(escala,df_emar.to_list(),1)[0] * 100
        pend_l=self.pendientes(escala,df_emal.to_list(),1)[0] * 100

        try:
            diferencia_porcentual= round((( r / l ) -1 )  * 100 ,2)
        except:
            diferencia_porcentual= -100

        if pendientes_positivas:
            emas_ok = diferencia_porcentual > diferencia_porcentual_minima and (pend_r >0 and pend_l>0)
        else:    
            emas_ok = diferencia_porcentual > diferencia_porcentual_minima or (pend_r >0 and pend_l>0)

        ret = (   emas_ok, diferencia_porcentual,round(pend_r,2),round(pend_l,2)   )

        self.cache_add( (escala,per_rapida,per_lenta,diferencia_porcentual_minima,pendientes_positivas),ret  )
          
        return ret


    def emas_ordenadas(self,escala,per_ema1,per_ema2,per_ema3):
        ''' True cuando ema1> ema2 > ema3''' 
        df=self.mercado.get_panda_df(self.par,escala,per_ema3+50)
        

        df_ema1=ta.ema(df['Close'],length=per_ema1) 
        df_ema2=ta.ema(df['Close'],length=per_ema2)

        ret = False  
        if df_ema1.iloc[-1] > df_ema2.iloc[-1]:
            df_ema3=ta.ema(df['Close'],length=per_ema3)
            if  df_ema2.iloc[-1] > df_ema3.iloc[-1]:
                ret = True
        return ret

    def _deprecated_ema_rapida_menor_lenta_2(self,escala,per_rapida,per_lenta,diferencia_porcentual_maxima=0,pendientes_negativas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es menor diferencia_porcentual_maxima o las pendientes
        de ambas emas son negativa  retorna True, tambien retorna datos para log..
        si pendientes_negativas=True exige que las pendientes sean negativas al mismo tiempo que se de la diferencia porcentual''' 
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 50) 
        
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        r = emar[-1] 
        l = emal[-1] 

        pend_r=round(self.pendientes(escala,emar,1)[0] * 100,4)
        pend_l=round(self.pendientes(escala,emal,1)[0] * 100,4)

        try:
            diferencia_porcentual= round(    (( r / l ) -1 )  * 100       ,2)
        except:
            diferencia_porcentual= -100

        if pendientes_negativas:
            emas_ok = diferencia_porcentual < diferencia_porcentual_maxima and (pend_r <0 and pend_l <0)
        else:    
            emas_ok = diferencia_porcentual < diferencia_porcentual_maxima or (pend_r <0 and pend_l<0)

        return emas_ok, diferencia_porcentual,round(pend_r,2),round(pend_l,2)

 

    def ema_rapida_menor_lenta2(self,escala,per_rapida,per_lenta,diferencia_porcentual_maxima=0,pendientes_negativas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es menor diferencia_porcentual_maxima o las pendientes
        de ambas emas son negativa  retorna True, tambien retorna datos para log..
        si pendientes_negativas=True exige que las pendientes sean negativas al mismo tiempo que se de la diferencia porcentual''' 
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        df_emar=ta.ema(df['Close'],length=per_rapida) 
        df_emal=ta.ema(df['Close'],length=per_lenta)  

        #print(df)
        #print(df_emal.to_list())
        #print(df_emal.iloc[-1])

        r = df_emar.iloc[-1] 
        l = df_emal.iloc[-1] 

        pend_r=self.pendientes(escala,df_emar.to_list(),1)[0] * 100
        pend_l=self.pendientes(escala,df_emal.to_list(),1)[0] * 100

        try:
            diferencia_porcentual= round(    (( r / l ) -1 )  * 100       ,2)
        except:
            diferencia_porcentual= -100

        if pendientes_negativas:
            emas_ok =  (  diferencia_porcentual < diferencia_porcentual_maxima and  pend_r <0 and pend_l <0    )
        else:    
            emas_ok =  ( diferencia_porcentual < diferencia_porcentual_maxima      )

        return emas_ok, diferencia_porcentual,pend_r,pend_l 

    def ema_vector_completo(self,escala,periodos):
        
        vector=self.mercado.velas[escala].valores_np_close()
        ema=talib.EMA(vector, timeperiod=periodos)
        return ema  

    def precio_vector_completo(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
        return vector    


    def coeficiente_ema_rapida_lenta(self,escala,per_rapida,per_lenta):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        return float(round ( (1 - emal[emal.size-1] / emar[emar.size-1] )*100,2))
        
 
    def sombra_sup_grande_en_ultima_vela(self,escala,coeficiente,pos):
        
        vela=self.mercado.velas[escala].get_vela_desde_ultima(pos)
        
        ret=False
        nz=0.00000000001

        v=round(vela.sombra_sup() / (vela.cuerpo()+nz) ,2)

        if v>=coeficiente:
            ret= True
        
        return [ ret , v]    

        
    
    def rsi_mom(self,escala):
        
        

        vector=self.mercado.velas[escala].valores_np_close()

        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        rsi=vrsi[vrsi.size-1]
        mom=vmom[vmom.size-1]
     

        return [rsi,mom]


    def rsi(self,escala,vela=0):
        
        df=self.mercado.get_panda_df(self.par, escala, 60) #self.velas[escala].panda_df(cvelas + 60)
        df_rsi = df.ta.rsi()
        rsi= round( df_rsi.iloc[-1]   ,2     )

        return rsi

    def rsi_vector(self,escala,cvelas=5):

        
        vector=self.mercado.get_vector_np_close(self.par,escala,40)
        vrsi=talib.RSI(vector, timeperiod=14)
        v = cvelas * -1
        return vrsi[v:] 

    def mfi_vector(self,escala,cvelas=5):

        
        high=   self.mercado.get_vector_np_high(self.par,escala,40)
        low=    self.mercado.get_vector_np_low(self.par,escala,40)
        close=  self.mercado.get_vector_np_close(self.par,escala,40)
        volume= self.mercado.get_vector_np_volume(self.par,escala,40)

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        v = cvelas * -1
        return mfi[v:]   


    def precio_de_rsi(self,escala,rsi_buscado):
        ''' retorna el precio (mas bajo) para llegar al ris
            indicado como parámetro de las escala en que se busca.
        '''
        
        
        vector=self.mercado.get_vector_np_close (self.par,escala)
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
        
        close=self.mercado.velas[escala].valores_np_close(50)
        vrsi=talib.RSI(close, timeperiod=14)
        l=vrsi.size
        ret=[]
        for i in range( l - cant_rsi , l):
            #print(vema[i], vema[i-1],vema[i] - vema[i-1])
            diferencia = vrsi[i] - vrsi[i-1]
            ret.append( diferencia ) 
        
        return ret    



    def mfi(self,escala):
        
        
        
        high=  self.mercado.velas[escala].valores_np_high(40)
        low=   self.mercado.velas[escala].valores_np_low(40)
        close= self.mercado.velas[escala].valores_np_close(40)
        volume=self.mercado.velas[escala].valores_np_volume(40)

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        
        return round(float(mfi[mfi.size-1]),2)



    def mom(self,escala):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        mom=vmom[vmom.size-1]
        

        return mom

    def momsube(self,escala,x_mas_de_la_ema):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        vema=talib.EMA(vmom  , timeperiod=10)
       
        mom=vmom[vmom.size-1]
        ema=vema[vema.size-1]

        return [mom > ema * x_mas_de_la_ema,mom,ema]    
    
    #vector de momentums, retorna un vector con los tres ultimos momentums
    def vmom(self,escala,periodos):
        
        vector=self.mercado.get_vector_np_close(escala)
        vmom=talib.MOM(vector, timeperiod=periodos)

        return [ vmom[vmom.size-3],vmom[vmom.size-2] , vmom[vmom.size-1] ]

    

    def esta_subiendo4(self,escala):

        
        uv   =self.mercado.velas[escala].ultima_vela()
        close=self.mercado.velas[escala].valores_np_close()
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
        df=self.mercado.get_panda_df(self.par,escala,periodos+50)
        df_ema=ta.ema(df['Close'],length=periodos) 
        

        pend=round( self.pendientes(escala,df_ema.to_list(),1)[0] * 100,9 )
        
        return pend >0 






    def ema_minimos(self,escala,periodos):
        
        low=self.mercado.get_vector_np_low ( self.par,escala,periodos + 10 )
        vemas=talib.EMA(low, timeperiod=periodos)
        return vemas[vemas.size-1]

    def minimo_en_ma(self,escala,periodos,datos='close',cvelas=3):
        '''retorna un minimo en la media movil y su posicion'''

        df=self.mercado.get_panda_df(self.par,escala,periodos+50)
        df_ema=ta.ma('ma',df[datos],length=periodos)
        i=-1
        l=len(df_ema)
        lneg = l * -1
        cvel =1
        minimo = 0
        while i > lneg: #encontrar un minimo
            i -= 1
            cvel += 1
            
            if self.hay_minimo_en(df_ema,i,5):
                minimo = cvel
                break

            if cvel > cvelas:
                break

        #a partir del minimo contar cuantas velas ha descendido
        #desde el minimo hacia la izquierda
        cvelas_bajada=0
        while i > lneg:
            i -= 1
            cvelas_bajada +=1
            print(    df_ema.iloc[i-1], df_ema.iloc[i]    )
            if self.hay_maximo_en(df_ema,i,5):
                break
            #if df_ema.iloc[i-1] < df_ema.iloc[i]:

        return minimo,cvelas_bajada    

    def maximo_en_ema(self,escala,periodos,datos='close',cvelas=3):
        df=self.mercado.get_panda_df(self.par,escala)
        df_ema=ta.ema(df[datos],length=periodos)
        i=-1
        l=len(df_ema)
        lneg = l * -1
        cvel =1
        maximo = 0
        while i > lneg: #encontrar un maximo
            i -= 1
            cvel += 1
            
            if self.hay_maximo_en(df_ema,i,5):
                maximo = cvel
                break

            if cvel > cvelas:
                break

        #a partir del maximo contar cuantas velas ha subido
        #desde el maximo hacia la izquierda
        cvelas_subida=0
        while maximo>0 and i > lneg:
            i -= 1
            cvelas_subida+=1
            print(    df_ema.iloc[i-1], df_ema.iloc[i]    )
            if self.hay_minimo_en(df_ema,i,5):
                break
            #if df_ema.iloc[i-1] < df_ema.iloc[i]:
                
                


        return maximo,cvelas_subida

        

    def variacion_px_actual_px_minimo(self,escala,periodos):
        
        low=self.mercado.get_vector_np_low ( self.par,escala,periodos)
        low.sort()
        precio = self.precio_mas_actualizado()
        
        return variacion_absoluta(low[0],precio)

    def periodos_ema_minimos(self,escala,cvelas):
        '''
        busca los periodos para la ema de escala indicada
        en lo que los mínimos de las cvelas son superiores 
        a la ema de esos periodos
        '''
        periodos=9
        
        low=self.mercado.get_vector_np_low(escala)
        
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
        
        low=self.mercado.get_vector_np_low(escala)
        
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
        
        low=self.mercado.get_vector_np_low(escala)
        px = self.mercado.velas[escala].ultima_vela().close
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
        
        precio=self.mercado.get_vector_np_close(escala)
        vemas=talib.EMA(precio, timeperiod=periodos)

        ret=True
        for  i in range(vemas.size-cant_velas,vemas.size):
            
            if precio[i] * (1+ porcentaje_mayor/100) < vemas[i]: #subo el precio un porcentje extra pra seguir comprando en esa ema
                ret=False
                break 
        return ret
    

    def pendientes_ema(self,escala,periodos,cpendientes):
        
        ret=[]
        try:
            close=self.mercado.get_vector_np_close (self.par,escala,max(periodos,cpendientes) + 10 )
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
    
    def pendientes(self,escala,lista,cpendientes):
        ret=[]
        try:
            # print(lista)
            l=len(lista)
            unidad = self.g.escala_tiempo[escala]
            #print(unidad)
            for i in range(l-cpendientes,l):
                m= (lista[i] - lista[i-1]) / unidad 
                ret.append(m) 

        except Exception as e: 
            self.log.err(str(e))       
        #print('pendientes', ret)
        return ret

    def diff_vectores(self,lista_superior,lista_inferior):
        ret=[]
        try:
            # print(lista)
            l=len(lista_superior)
            for i in range(0,l):
                diff=lista_superior[i] - lista_inferior[i] 
                ret.append(diff) 
        except Exception as e: 
            self.log.err(str(e))       
        #print('pendientes', ret)
        return ret    

    def compara_emas1(self,escala,periodos,cant_emas):
        ''' retorna un vector con la diferencias de la ema actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        
        close=self.mercado.velas[escala].valores_np_close()
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
        
        close=self.mercado.velas[escala].valores_np_close(periodos * 3)
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
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)
        v=talib.ADX(h,l, c, timeperiod=14)
        l=v.size

        ret=[]
        for i in range( l - cant , l):
            diferencia = v[i] - v[i-1]
            ret.append( diferencia ) 
        return ret    

   





    #busca que existan cpendientes con un coeficiente mayor al dado
    def pendientes_ema_mayores(self,escala,periodos,cpendientes,coeficiente):
        
        close=self.mercado.velas[escala].valores_np_close()
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
        
        

        c=self.mercado.get_vector_np_close(self.par,escala)
        h=self.mercado.get_vector_np_high(self.par,escala)
        l=self.mercado.get_vector_np_low(self.par,escala)
        
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
        
        c=self.mercado.get_vector_np_close(self.par,escala)
        h=self.mercado.get_vector_np_high(self.par,escala)
        l=self.mercado.get_vector_np_low(self.par,escala)
        
        vvol=self.mercado.get_vector_np_volume(escala)

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
        

        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        vatr = talib.ATR(h, l, c, timeperiod=14)
        
        v=vatr.size - 1

        print (vatr)
        return vatr[ vatr.size - velas : vatr.size ]   


    def vprecio(self,escala,velas=5):
        

        p=self.mercado.get_vector_np_close(escala)
        
        return p[ p.size - velas : p.size ]   

    def vvolumen(self,escala,velas=5):
        

        vector=self.mercado.velas[escala].valores_np_volume()
        
        return vector[ vector.size - velas :vector.size ]        
              
    def vp(self,escala,cvelas=None):
        
        df=self.mercado.velas[escala].panda_df(cvelas)
        vp = df.ta.vp()
        
        return vp


    def volume(self,escala):

        vector=self.mercado.velas[escala].valores_np_volume()


        avg=np.average(vector)
        v2=vector[vector.size-1]
        v1=vector[vector.size-2]
        v0=vector[vector.size-3]

        return [ v0<v1 and v1>avg*1.1, v0, v1 ,v2]

    def volumen_porcentajes(self,escala):

        
        vector=self.mercado.get_vector_np_volume(self.par,escala,50)

        vemavol=talib.EMA(vector, timeperiod=20)

        ret=[]
        for i in range(-10,0):
            ret.append(  round( vector[i]/vemavol[i] ,2)  )

        pend = self.pendientes('1m',vector,10)    

        return {'%':ret,'p':pend}




    def volumen_proyectado(self,escala):
        
        p=self.mercado.velas[escala].porcentaje_ultima_vela()
        v=self.mercado.velas[escala].ultima_vela().volume
        return round(  v/p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo

    def volumen_proyectado_moneda_contra(self,escala):
        
        p=self.mercado.velas[escala].porcentaje_ultima_vela()
        v=self.mercado.velas[escala].ultima_vela().volume
        precio = self.precio(escala)
        return round(  v * precio  /p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo    
    


    def volumen_creciente(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return ( vc[l-3]<vc[l-2]  and vc[l-2]<vc[l-1] and vc[l-2]>0.9 and vc[l-1]>1 )


    def volumen_bueno5(self,escala,coef):
        
        vector_volumenes=self.mercado.velas[escala].valores_np_volume()
        vemavol=talib.EMA(vector_volumenes, timeperiod=20) #20 periodos es lo que usa tradingview por defecto para mostral el promedio del volumen
        ultima_vela=len(vector_volumenes)-1
        
        ret=( vector_volumenes[ultima_vela]   > vemavol[ultima_vela]   * coef or \
                 vector_volumenes[ultima_vela-1] > vemavol[ultima_vela-1] * coef   )
        return {'resultado':ret,'vol':[round(vector_volumenes[ultima_vela-1],2) , round(vector_volumenes[ultima_vela],2) ],'ema':[round(vemavol[ultima_vela-1],2) , round(vemavol[ultima_vela],2) ]  }

    def volumen_moneda_contra(self,escala): #entrega el volumen expresado en la moneda contra
        
        vector=self.mercado.velas[escala].valores_np_volume()
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
        
        vector=self.mercado.velas[escala].valores_np_volume()
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
        
    


                  





    

    def volumen_mayor_al_promedio(self,escala):

        
        vector=self.mercado.velas[escala].valores_np_volume()

        

        avg=np.average(vector)
        v=vector[vector.size-1]

        
        
        return v>avg     

    def la_ultima_vela_es_linda(self,escala):
        

        vela=self.mercado.velas[escala].ultima_vela()
        
        cuerpo=1-vela.open/vela.close # en porcentaje

        if cuerpo>0.03:
           return True
        else:
           return False

    def aumento_ultima_vela(self,escala):
        

        vela=self.mercado.velas[escala].ultima_vela()
        
        cuerpo=1-vela.open/vela.close # en porcentaje

        return round(cuerpo * 100,2)

    
    def la_ultima_vela_es_positiva(self,escala):
        
        vela=self.mercado.par_escala_ws_v[self.par][escala][1].ultima_vela()

        return (vela.signo==1)

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
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        

        return (r0<r1 and m0<m1 and self.volumen_mayor_al_promedio(escala))  # rsi sube, momento sube, y hay volumen

    

    def esta_subiendo2(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
        uvela=self.mercado.velas[escala].ultima_vela()
        #self.log.log("Precios",escala,vector[vector.size-3],vector[vector.size-2],vector[vector.size-1])
        if uvela.open<uvela.close and ( (vector[vector.size-3]<=vector[vector.size-2] and  vector[vector.size-2]<=vector[vector.size-1] ) or vector[vector.size-3]<vector[vector.size-1]):
            return True
        else:     
            return False

    
    
    

    def precio(self,escala):
        try:
            vs: VelaSet = self.mercado.get_velaset(self.par,escala)
            px = vs.ultima_vela().close
        except Exception as ex:
            self.log.log(str(ex))
            px = -1
        return px   

    # def control_de_inconsistemcias(self,escala):
    #     self.log.log('ini inconsistencia',self.par)
    #     ifea = self.mercado.par_escala_ws_v[self.par][escala].inconsistencias()
    #     if ifea > -1:
    #         hora_fea = self.mercado.par_escala_ws_v[self.par].[escala].df.index[ifea]
    #         print('---> inconsitencai:',hora_fea)
    #         self.log.log('inconsistencia',self.par)
    #         self.actualizado[escala] = hora_fea /1000 -1
    #         self.carga_de_actualizacion_escala(escala)

    #     return ifea         

    # cuando el momentum pierde fuerza, la diferencia entre el momento actual y el aterior se hace cada vez mas chica
    # eso indica que la velocidad de subia está disminuyendo,la curva de aplana y muy posiblemente comience a bajar
    # entonces esta funciona de True cuando NO pierde fuerza.
    def mom_bueno(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
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
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        
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
        

        vela=self.mercado.velas[escala].ultima_vela_cerrada()
        pp=( vela.high + vela.low + vela.close) / 3 # PP (P) = (H + L + C) / 3
        r2= pp + (vela.high - vela.low)
        r1= pp + (pp - vela.low)
        s1= pp - (vela.high - pp)
        s2= pp - (vela.high - vela.low)

        return [s2,s1,pp,r1,r2]

    def puntos_pivote_fibo(self,escala):
        
        vela=self.mercado.velas[escala].ultima_vela_cerrada()
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
        
        ot=self.mercado.velas[escala].ultima_vela().open_time
        o =self.mercado.velas[escala].ultima_vela().open
        h =self.mercado.velas[escala].ultima_vela().high
        l =self.mercado.velas[escala].ultima_vela().low
        c =self.mercado.velas[escala].ultima_vela().close  

      
        p=self.diff_porcentaje(o,h,l,c)

        #print (69,datetime.utcfromtimestamp(int(ot)/1000).strftime('%Y-%m-%d %H:%M:%S'),o,h,l,c,p)


        if ( abs(p) > porcentaje ):
            ret=[True,p,-1,ot]
        else:
            ret=[False,p,-1,'-']
            
            fin =len(self.mercado.velas[escala].velas)-2
            ini = fin - cvelas +1
            for i in range(fin,ini,-1):

                ot=self.mercado.velas[escala].velas[i].open_time
                o =self.mercado.velas[escala].velas[i].open
                h =self.mercado.velas[escala].velas[i].high
                l =self.mercado.velas[escala].velas[i].low
                
                
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
        

        vc=self.mercado.get_vector_np_close(self.par,escala,velas_desde_fin+ 10) 
        #vc=self.mercado.velas[escala].valores_np_close(velas_desde_fin) # solo los ultimos <velas_desde_fin> elementos
        bs, bm, bi = talib.BBANDS(vc, timeperiod=periodos, nbdevup=desviacion_standard, nbdevdn=desviacion_standard, matype=0)

        return float(  bs[-1]  ),float(  bm[-1]  ),float(  bi[-1]  )
    

    #trata de determinar el precio donde hubo la menor volatilidad posible
    #entorno a un vela dada 
    #para ello saca la diferencia entre la banda superior y la inferior de bollinger
    #donde la diferencia es menor, tomamos el precio cierre redondeado como precio de rango
    def rango_por_bollinger(self,escala,velas_desde_fin):
        
        vc=self.mercado.velas[escala].valores_np_close() #vector close
        #vo=self.mercado.velas[escala].valores_np_open()  #vector open
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
        
        df=self.mercado.velas[escala].panda_df(cvelas)
        sqz = df.ta.squeeze( lazybear = True)
        histo=[]
        sqz_on=[]
        for _,i in sqz.iterrows():
            histo.append(i['SQZ_20_2.0_20_1.5_LB'])
            sqz_on.append(i['SQZ_ON'])
        
        return histo,sqz_on


    def sqzmon_lb_df(self,escala,cvelas=None):
        
        df=self.mercado.velas[escala].panda_df(cvelas)
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
            df = self.sqzmon_lb_df(escala,50)
        
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




    #entrega una lista las emas solicitadas en {'1h':50,escala:periods,....}
    def lista_emas(self,dic_escalas):
        listaemas=[]
        for escala in dic_escalas:
           
            listaemas.append (self.ema(escala,dic_escalas[escala]))
        return listaemas    



    #
    def max_y_luego_min(self,escala,periodos_hacia_max=200,periodos_hacia_min=199):
        
        vmax=self.mercado.velas[escala].valores_np_high()
        vmin=self.mercado.velas[escala].valores_np_low()
        #precio=self.mercado.velas[escala].ultima_vela().close
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
        
        cuerpos=self.mercado.velas[escala].valores_np_cuerpo(cvelas)
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
        
        vmax=self.mercado.velas[escala].valores_np_high()
        
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
        
        vmin=self.mercado.velas[escala].valores_np_low()
        
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
        
        ret = 0
        
        vmaxmin=self.mercado.velas[escala].valores_np_maxmin(cvelas)
        
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
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

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
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

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
        
        valores=self.mercado.get_vector_np_volume(escala)

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
    
    
    def precio_en_rango(self,escala,pmin,pmax,total_velas=30):
        '''
            retorna la cantidad de velas que el precio se encuentra entre pmax y pmin
        '''    
        
        close = self.mercado.velas[escala].valores_np_close(total_velas)

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
        
        vclose = self.mercado.velas[escala].valores_np_close()

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
        
        
        vopen  = self.mercado.velas[escala].valores_np_open()
        vclose = self.mercado.velas[escala].valores_np_close()

        lx = vopen.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        #contruyo lista de rangos 
        vrangos=[]
        px = self.mercado.velas[escala].ultima_vela().close
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
    
    

    
    

    def sentido_vela(self,escala,vela_desde_ultima=0):
        
        v: Vela = self.mercado.velas[escala].get_vela_desde_ultima(vela_desde_ultima)
        return v.sentido() 







    
                
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
        actualizado={}
        for esc in self.mercado.par_escala_ws_v[self.par].keys():
            actualizado[esc]=self.mercado.par_escala_ws_v[self.par][esc][1].actualizado

        mas_actualizado = sorted(actualizado.items(), key=lambda x: x[1] ,reverse=True   )[0]

        return self.precio(mas_actualizado[0]) #retorno el precio del mas actualizado


    
    
    def cuatro_emas_ordenadas(self,escala,per1,per2,per3,per4):
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per4+10)
        ema1=talib.EMA(vector, timeperiod=per1)[-1]
        ema2=talib.EMA(vector, timeperiod=per2)[-1]
        ret = False
        if ema1 > ema2:
            ema3=talib.EMA(vector, timeperiod=per3)[-1]
            if ema2 > ema3:
                ema4=talib.EMA(vector, timeperiod=per4)[-1]
                if ema3 > ema4:
                    ret = True
        return ret  
    
    

if __name__=='__main__':
    from variables_globales import VariablesEstado
    from gestor_de_posicion import Gestor_de_Posicion
    from binance.client import Client #para el cliente
    from pws import Pws
    #from acceso_db_conexion_mysqldb import Conexion_DB
    from acceso_db_conexion import Conexion_DB
    
    from logger import Logger
    from acceso_db import Acceso_DB
    
    log=Logger(f'test_indicadores.log')
    pws=Pws()
 
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn.pool)

    client = Client(pws.api_key, pws.api_secret)
    p = Gestor_de_Posicion(log,client,conn)
    g = VariablesEstado(p)
    
    un_minuto = timedelta(minutes=1)
    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    fecha_fin =  strtime_a_obj_fecha('2021-08-06 21:00:00-03:00')
    fin_test  =  strtime_a_obj_fecha('2021-08-06 23:03:00-03:00')
    pares=['BTCUSDT']
    observaciones='  test '
    escalas = ['1m','5m','15m','30m','1h','2h','4h','1d','1w']
    #escalas = ['1m','5m','15m','30m','1h']
    par=pares[0]

    m=Mercado_Back_Testing(log,g,db)
    m.inicar_mercados(fecha_fin,250,pares,escalas)
    ind = Indicadores(par,log,g,m)
    
    for _ in range (14):
       txtf = m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')
       
       #print(txtf,ind.detectar_patrones('1m',10))
       #print(ind.rsi_contar_picos_maximos('1m',3,50))
       #print(ind.cuatro_emas_ordenadas('1m',9,20,50,200))
       log.log(txtf,'********')
       #log.log('Low',ind.minimo_en_ema('1m',7,'Low')  )
       #log.log('Close',ind.minimo_en_ema('1m',10,'Close').tail(5)  )
       #log.log('-->',ind.ema_rapida_menor_lenta3('1m',20,40,diferencia_porcentual_maxima=0,pendientes_negativas=False)  )
       log.log( ind.ultima_vela_cerrada('1m') )
       #log.log( ind.ema_rapida_mayor_lenta2('1m',10,50,0.1))
       log.log( 'Cache',ind.cache_txt())

       m.avanzar_tiempo(un_minuto)
       m.actualizar_mercados()


    