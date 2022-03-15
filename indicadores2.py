# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member
#import talib as ta
from math import atan, degrees, fabs
from pymysql.constants.ER import NO
#from pandas.core.missing import pad_2d
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
    escala_siguiente   ={'1m':'3m','3m':'5m','5m':'15m','15m':'30m','30m':'1h','1h':'2h','2h':'4h','4h':'1d','1d':'1w','1w':'1M'}
    tiempo_actualizar  ={'1m':30,  '3m':45,  '5m':90,   '15m':100,  '30m':110, '1h':120, '2h':150, '4h':120, '1d':600, '1w':600,'1M':600}
    var_velas          ={'1m':5,   '3m':6,   '5m':7,    '15m':9,    '30m':11,  '1h':13,  '2h':15,  '4h':17,  '1d':19,  '1w':30,' 1M':50}
    var_velas_seguidas ={'1m':9,   '3m':10,  '5m':11,   '15m':13,   '30m':15  ,'1h':17,  '2h':19,  '4h':21,  '1d':27,  '1w':30, '1M':70}
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

        self.actualizado={'1m':0,'3m':0,'5m':0,'15m':0,'30m':0,'1h':0,'2h':0,'4h':0,'1d':0,'1w':0,'1M':0}
        self.g:VariablesEstado = estado_general
        self.velas={}
        for k in self.actualizado:
            self.velas[k]=None
        
        
        self.par=par
        self.log:Logger = log
        self.retardo=5
        self.errores=0
        self.tiempo_actualizacion=25
        self.incremento_volumen_bueno=1.5
        
        #self.client = cliente
        
        #self.lock_actualizador= Lock()
        self.prioridad = 0
        
        self.mercado:Mercado = mercado

        self.cache={}

    def cache_add(self,parametros,valor):
        funcion_que_me_llamo = inspect.stack()[1][3] 
        fxfirma = self.firma(funcion_que_me_llamo,parametros)
        self.cache[fxfirma] =(time.time(),valor)

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
        precio=self.precio(escala)
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

    def no_sube(self,escala):

        ema,px = self.ema_px(escala,7)

        if px > ema:
            return False
        
        v1:Vela = self.mercado.vela(self.par,escala,-1)
        v0:Vela = self.mercado.vela(self.par,escala,-2)
        ret = False
        if not v0 is None and not v1 is None:
            #self.log.log(f'v0 close {v0.close} high {v0.high} | v1 close {v1.close} high {v1.high} ')
            ret = v0.close > v1.close and v0.high > v1.high      # v0 penútima v1 ultima

        return ret    

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

    def lista_picos_minimos_x_vol(self,escala,cvelas,vela_ini=1):
        ''' entrega lista de picos minimos desde el final por cvelas
            y una ponderación  de volumen( i-2 ,i-1 + i ) * minimo * posicion 
        '''    
        df=self.mercado.get_panda_df(self.par, escala,cvelas+vela_ini+2 ) #self.velas[escala].panda_df(cvelas + 60)
        low = df['low']
        lista=[]

        l=len(low)
        lneg = l * -1
        
        lneg = l * -1
        cvel = 1
        i=-1 * vela_ini
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_minimo_en(low,i):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                pos=l-i
                vol = df.iloc[i-2]['volume'] + df.iloc[i-1]['volume'] + df.iloc[i]['volume']  # volumen de al vela + volumen de las dos anteriores
                lista.insert(0,[ pos , df.iloc[i]['low'],  df.iloc[i]['low'] /(vol*pos)  ])
                
        return lista

    def lista_picos_maximos_x_vol(self,escala,cvelas,vela_ini=1):
        ''' entrega lista de picos minimos desde el final por cvelas
            y una ponderación  de volumen( i-1 + i +i+1) * minimo * posicion 
        '''    
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 60) #self.velas[escala].panda_df(cvelas + 60)
        high = df['high']

        lista_max=[]
        l=len(high)
        lneg = l * -1
        cvel = 1
        i=-1 * vela_ini
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_maximo_en(high,i):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                pos=l-i
                vol = df.iloc[i-1]['volume'] + df.iloc[i]['volume'] + df.iloc[i+1]['volume']
                lista_max.insert(0,[ pos , df.iloc[i]['high'],  vol * pos * df.iloc[i]['high']  ])        
        return lista_max

    def minimo_x_vol(self,escala,cvelas=100,cminimos=3,vela_ini=1):    
        lista=self.lista_picos_minimos_x_vol(escala,cvelas,vela_ini)
        minimos = sorted(lista, key=lambda x: x[2]  ) # ordno por la ponderacion
        return self.calc_top(minimos,cminimos)  

    def maximo_x_vol(self,escala,cvelas=100,cant_maximos=3,vela_ini=1):    
        lista=self.lista_picos_maximos_x_vol(escala,cvelas)
        maximos = sorted(lista, key=lambda x: x[2] ,reverse=True )
        return self.calc_top(maximos,cant_maximos)

    def calc_top(self,lista,top):
        l=len(lista)
        suma=0
        cant=0
        i=0
        while i < top and  i<l:
            suma += lista[i][1] 
            cant += 1 
            i+=1
        if i>0:
            ret = suma/cant
        else:
            ret = None
        return ret    

    def velas_imporantes(self,escala,cvelas,top_velas):
        '''  
           obtiene las las velas mas importantes de las ultimas cvelas 
           y retorna las top_cvelas
        '''    
        df=self.get_df(self.par,escala)
        df['importancia'] = (df.high - df.low)  * df.volume

        lista=[]

        l=len(df) 

        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
        
            lista.append([ i*-1 , round(df.iloc[i]['importancia'],2) ,Vela(df.iloc[i]) ]) 
        
        lista.sort(key=lambda x: x[1] ,reverse=True)
        top = lista[0:top_velas]
        top.sort()
       
        return top       
        

    def minimo_maximo_por_rango_velas_imporantes(self,escala,cvelas):
        '''  
           obtiene las las velas mas importantes de las ultimas cvelas 
           y retorna el mínimo y maximo del rango determinado
        '''    
        df=self.get_df(self.par,escala)
        df['importancia'] = (df.high - df.low)  * df.volume

        lista=[]

        l=len(df) 

        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            lista.append([ i*-1 , df.iloc[i]['importancia']  ]) 
        
        lista.sort(key=lambda x: x[1] ,reverse=True)
        top = lista[0:int(cvelas/5)]
        top.sort(reverse=True)
        inicio_rango = top[0][0]

        df1 = df.iloc[ -inicio_rango: ]

        
        #print (des)
        #print(    (des['min']+des['25%']) /2   )
        #print(    des['mean'] - des['std'] * 2    )
       
        minimo = df1['low'].quantile(.05)
        maximo = df1['high'].quantile(.95)
       
        return minimo,maximo       


    def lista_picos_minimos_ema(self,escala,periodos,cvelas,origen='close',izquierda=5,derecha=2):
        ''' entrega lista de picos minimos desde el final por cvelas
            para la ema origen 
        '''    
        df=self.get_df(self.par,escala)
        ema = ta.ema(df[origen],length=periodos) 
        
        lista=[]

        l=len(ema)
                
        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_minimo_en(ema,i,izquierda,derecha):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                lista.append([ i*-1 , ema.iloc[i]  ])
                
        return lista 

    def lista_picos_maximos_ema(self,escala,periodos,cvelas,origen='close',izquierda=5,derecha=2):
        ''' entrega lista de picos maximo desde el final por cvelas
            para la ema valor('close' u otras) 
        '''    
        df=self.get_df(self.par,escala)
        ema = ta.ema(df[origen],length=periodos) 
        
        lista=[]

        l=len(ema)
        lneg = l * -1
        
        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_maximo_en(ema,i,izquierda,derecha):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                lista.append([ i*-1 , ema.iloc[i]  ])
                
        return lista

    def lista_picos_maximos(self,df,izquierda=2,derecha=2):
        ''' entrega lista de picos maximos de un df 
        '''    
        lista=[]
        l=len(df)
        lneg = l * -1
        i= -1 
 
        while i > lneg:
            i -= 1
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_maximo_en(df,i,izquierda,derecha):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                lista.append([ i*-1 , df.iloc[i]  ])
        return lista    
    
    def cruce_de_emas(self,escala,per_rapida,per_lenta,cvelas):
        '''  
           busca un cruce de emas y retorna posición
           cruce = 1  ema rapida cruza lenta de abajo hacia arriba
           cruce = -1 ema rapida cruza hacia arriba a lenta
           cruce = 0 no hay cruce
           pos = -1 no hay cruce 

        '''    
        df=self.get_df(self.par,escala)
        df_emar=ta.ema(df['close'],length=per_rapida) 
        df_emal=ta.ema(df['close'],length=per_lenta)  

        l = len(df) 

        y_ant = signo( df_emar.iloc[-1] - df_emal.iloc[-1] )
        cruce = 0
        pos = -1

        lneg = l * -1
        cvel = 2
        i=-2
        while i > lneg:
            y =  signo( df_emar.iloc[i] - df_emal.iloc[i] )

            if y != y_ant:
                cruce = y_ant
                pos = -i -1
                break

            y_ant = y
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break 

        return cruce,pos
        

    def rsi_lista_picos_minimos(self,escala,cvelas):
        ''' entrega lista de picos minimos desde el final por cvelas 
        para rsi menor que el param menor_de'''    
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 60) #self.velas[escala].panda_df(cvelas + 60)
        rsi = df.ta.rsi()
        lista=[]

        l=len(rsi)
        lneg = l * -1
        
        lneg = l * -1
        cvel = 1
        i=-1
        while i > lneg:
            i -= 1
            cvel += 1
            if cvel > cvelas:
                break
            # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
            if self.hay_minimo_en(rsi,i):
                #print(    strtime_a_fecha(  df.iloc[i]['close_time'] )   )
                lista.insert(0,[l-i,rsi.iloc[i],df.iloc[i]['low']])
                
        return lista 

    def minimo_por_rsi(self,escala,cvelas=100,cminimos=3):    
        lista=self.rsi_lista_picos_minimos(escala,cvelas)
        minimos = sorted(lista, key=lambda x: x[2]  )
        l=len(minimos)
        suma=0
        cant=0
        i=0
        while i < cminimos and  i<l:
            suma += minimos[i][2] * minimos[i][0] 
            cant += minimos[i][0] 
            i+=1
        if i>0:
            ret = (suma/cant)
        else:
            ret = -1
        return ret                       
   
    def volumen_por_encima_media(self,escala,cvelas,xvol = 1,vela_ini=0):
        ''' suma el volumen de las ultimas cvelas multipolicado por xvol
         y lo compara con el volumen promedio si es mayor
         retorna verdadero 
         xvol > 1 aumenta el volumen medio para detectar volumenes mayores
         xvol < 1 disminuye el volumen y la detección es mas sensible
         '''  
        if cvelas == 0:
            return False

        df=self.mercado.get_panda_df(self.par, escala, cvelas + 25)
        
        vol_ma =ta.ma('ma',df['volume'],length=20)
        
        suma_vol_medio = 0
        suma_vol_velas = 0

        fin = (cvelas+vela_ini) * -1
        ini = vela_ini * -1

        for i in range(fin,ini):
            suma_vol_medio += vol_ma.iloc[i]
            suma_vol_velas += df.iloc[i]['volume']

        coef = round(suma_vol_velas / suma_vol_medio,2)
        ret =  coef > xvol

        self.log.log(f'volumen_por_encima_media {ret} coef {coef}')

        return ret  

    def volumen_suma(self,escala,cvelas):
        ''' entrega la suma del volumen de las ultimas cvelas'''    
        df=self.mercado.get_panda_df(self.par, escala, cvelas) #self.velas[escala].panda_df(cvelas + 60)
        return df['volume'].sum()

    def ultima_vela_cerrada(self,escala):
        df=self.mercado.get_panda_df(self.par, escala, 3)
        #print(df['closed'])
        #print(df.iloc[-1]['closed'])

        if df.iloc[-1]['closed']:
            v = Vela(df.iloc[-1])
        else:
            v = Vela(df.iloc[-2])
        return v 

    def ultimas_velas(self,escala,cvelas,cerradas=True):  
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        #print(df['closed'])
        #print(df.iloc[-1]['closed'])

        if cerradas and not df.iloc[-1]['closed']:
            fin = -1         #no incluye vela abierta
        else:
            fin = 0          #incluye vela -1 como esté  

        ini = fin - cvelas 
        velas=[]
        for i in range(ini,fin):
            velas.append( Vela(df.iloc[i]) )

        return velas    

    def patron_verde_supera_roja(self,escala):
        velas = self.ultimas_velas(escala,cvelas=3,cerradas=False)
        roja:Vela  = velas[0]
        verde:Vela = velas[1]
        confirma:Vela = velas[1]
        ret = False        
        if roja.signo == -1 and verde.signo == 1 and confirma.signo == 1 and\
               roja.close > verde.open and roja.open < verde.close:
            if roja.cuerpo() > self.cuerpo_promedio(escala,100) * 1.5:
                ret = True
        return ret

    def patron_martillo_verde(self,escala):
        velas = self.ultimas_velas(escala,cvelas=2,cerradas=True)
        martillo:Vela  = velas[0]
        verde:Vela = velas[1]
        ret = False
        if martillo.martillo() == 1 and verde.signo == 1:    #la verde es verde y el martillo es martillo
            recorrido_minimo = self.recorrido_promedio(escala,50) * 2
            recorrido = martillo.high - martillo.low
            if recorrido > recorrido_minimo:
                ret = True
        return ret        

    def patron_frenada_de_gusano_en_desarrollo(self,escala):
        ''' en realidad es morning star https://youtu.be/I7azCpcVlAU?t=2087 
            pero para mi es una frenada de gusano
        '''
        velas = self.ultimas_velas(escala,cvelas=5,cerradas=False)
        roja_grande1:Vela  = velas[0]
        roja_grande2:Vela  = velas[1]
        frenada:Vela = velas[2]
        verde:Vela = velas[3]
        ret = False
        cuerpo_minimo = self.cuerpo_promedio(escala,100) * 3
        if roja_grande1.signo == -1 and roja_grande2.signo == -1:                                  #las rojas son rojas
            if roja_grande1.cuerpo() > cuerpo_minimo and roja_grande2.cuerpo() > cuerpo_minimo:    #las rojas tienen cumplen con un cuerpo minimo
                if roja_grande2.cuerpo() > frenada.cuerpo() * 4 and verde.signo == 1:
                    ret = True
        return ret

    
    def _____hay_velas_mayores_al_promedio(self,escala,cvelas,x_mayor_al_promedio=2):
        ''' bueca que todos los cuerpos de las cvelas no superen al 
            promedio multiplicado * x_mayor_al_promedio
        '''
        velas = self.ultimas_velas(escala,cvelas,cerradas=False)
        promedio = self.cuerpo_promedio(escala,100)
        ret = True
        for v in velas:
            if v.cuerpo() > promedio * x_mayor_al_promedio: 
                ret = False
                break
        return ret     

    def porcentaje_recorrido_del_rango(self,escala,cvelas):
        ''' retorna el porcentaje del recorrido del rango'''
        minimo,maximo = self.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
        #print(minimo,maximo)
        recorrido = round( (self.precio(escala) - minimo) / (maximo - minimo) * 100  ,2)
        return recorrido
    

    def no_hay_velas_mayores_al_promedio(self,escala,cvelas,x_mayor_al_promedio=2):
        ''' bueca que todos los cuerpos de las cvelas no superen al 
            promedio multiplicado * x_mayor_al_promedio
        '''
        velas = self.ultimas_velas(escala,cvelas,cerradas=False)
        promedio = self.cuerpo_promedio(escala,100)
        ret = True
        for v in velas:
            if v.cuerpo() > promedio * x_mayor_al_promedio: 
                ret = False
                break
        return ret     

    def cuerpo_promedio(self,escala,cvelas):
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        df['cuerpo'] = abs(df.open - df.close) 
        return df["cuerpo"].mean()

    def recorrido_promedio(self,escala,cvelas):
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        df['recorrido'] = df.high - df.low
        return df["recorrido"].mean()   

    def recorrido_maximo(self,escala,cvelas):
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        df['recorrido'] = df.high - df.low
        return df["recorrido"].max()

    def recorrido_minimo(self,escala,cvelas):
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        df['recorrido'] = df.high - df.low
        return df["recorrido"].min()

    def minimo(self,escala,cvelas):
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 1)
        return df["low"].min()    

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

    
# RESCRIBIR  hay maximo en   estableciendo un rango  y buscando el mayor del rango...
#   falso apenas aparezca uno mayor o igual==? pensar...

 #  luego probar lista de maximos y zona de volumen para corregir estrategias de compra  
    def hay_maximo_en(self,df,p,entorno_izq=5,entorno_der=5):

        ret = True
        
        primer_elemento = len(df) * -1
        ini = p - entorno_izq
        if ini < primer_elemento:
            ret = False

        if ret:
            fin = p + entorno_der +1
            if fin > 0:
                ret=False
            
        #self.log.log(p,ini,fin,primer_elemento)

        if ret:
            for i in range(ini,p):
                #self.log.log (i,df.iloc[i])
                if df.iloc[i] > df.iloc[p]:
                    ret = False
                    break

        if ret:
            for i in range(p-1 , fin) : 
                #self.log.log (i,df.iloc[i])      
                if df.iloc[i] > df.iloc[p]:
                    ret = False
                    break

        return ret            
    
    def hay_maximo_en___viejo__no__usar(self,df,p,entorno_izq=5,entorno_der=5):
        lado_uno=True
        fin = -1
        i=p+1
        c_entorno=0
        while i <= fin and c_entorno < entorno_der :
            if df.iloc[p] < df.iloc[i]:
                lado_uno=False
                break
            i +=1
            c_entorno +=1

        lado_dos=True
        ini = len(df) * -1
        i=p-1
        c_entorno=0
        while ini <= i and c_entorno < entorno_izq:
            if df.iloc[p] < df.iloc[i]:
                lado_dos=False
                break
            i -=1
            c_entorno +=1

        return lado_uno and lado_dos     

    def hay_minimo_en(self,df,p,entorno_izq=5,entorno_der=5):
        ret = True
        
        primer_elemento = len(df) * -1
        ini = p - entorno_izq
        if ini < primer_elemento:
            ret = False

        if ret:
            fin = p + entorno_der +1
            if fin > 0:
                ret=False
            
        #print(p,ini,fin,primer_elemento)

        if ret:
            for i in range(ini,p):
            #  print (i,df.iloc[i])
                if df.iloc[i] < df.iloc[p]: #and not self.hay_maximo_en(df.iloc[i],1,1):  hay que probar esto en las dos funciones..
                    ret = False
                    break

        if ret:
            for i in range(p-1 , fin) :       
                if df.iloc[i] < df.iloc[p]:
                    ret = False
                    break

        return ret 


    def firma(self,funcion,parametros):
        ret=funcion
        for p in parametros:
            ret+=str(p)
        return ret    

    def set_cache(self,funcion,parametros,dato):
        fxfirma=self.firma(funcion,parametros)
        #print('set_cache',fxfirma)
        self.cache[fxfirma]=(time.time(),dato)
        
    
    def get_cache(self,funcion,parametros):
        fxfirma=self.firma(funcion,parametros)
        #print(self.cache,fxfirma)
        if fxfirma in self.cache:
            datos = self.cache[fxfirma]
            antiguedad = time.time() - datos[0]
            #print('antiguedad',antiguedad)
            if antiguedad > 5:
                #print('ini vieja vieja vieja cache')
                ret = None
                del datos
                del self.cache[fxfirma]
                #print('fin vieja vieja vieja cache')
            else:
                #print('okokokokoko cache')
                ret = datos[1]
        else:
            #print('no en cache',fxfirma)
            #print(self.cache)
            ret = None

        return ret         

    def quitar_ultima_vela_abierta(self,df):
        if df.iloc[-1]['closed']==0:
            df.drop(df.index[-1], inplace=True)


    def rsi_minimo_y_pos(self,escala,cvelas,vela_ini=None):
        ''' retorna el rsi minimo de las c velas, su posición y el rsi actual
        cvelas= cantidad de velas a controlar
        vela_ini = vela a contar desde el final 1= la ultima 2 la penultima ...
        retorta rsi_minimo, posición, precio en la posicion, rsi actual
        '''
        velas_df =  cvelas + 150

        df =self.get_cache('mercado.get_panda_df',(self.par, escala, velas_df) )
        rsi=self.get_cache('mercado.get_panda_df.rsi',(self.par, escala, velas_df)  )
        
        if df is None or rsi is None:
            df=self.mercado.get_panda_df(self.par, escala, velas_df) #self.velas[escala].panda_df(cvelas + 60)
            self.quitar_ultima_vela_abierta(df)
            rsi = df.ta.rsi()
            #self.set_cache('mercado.get_panda_df'    ,(self.par, escala, velas_df), df   )
            #self.set_cache('mercado.get_panda_df.rsi',(self.par, escala, velas_df), rsi  )

        l=len(rsi) 
        
        if vela_ini is None:
            i = -1
        else:    
            i =  abs(vela_ini) * -1  

        mi=0
        minimo=101

        try:
            lneg = l * -1
            minimo = rsi.iloc[i]
            mi = i
            cvel = 1
            while i > lneg:
                i -= 1
                cvel += 1
                if cvel > cvelas:
                    break
                if rsi.iloc[i] < minimo:
                    mi = i
                    minimo = rsi.iloc[i]
            
        except Exception as e:
            self.log.log(str(e)) 

        if mi==0:
            low = -1
        else:
            low = df.iloc[mi]['low']

        ret =  (  round(minimo,2), mi*-1, low,  round(rsi.iloc[-1],2)    )    
        self.cache_add( (escala,cvelas),ret )

        return    ret
    
    def rsi_maximo_y_pos(self,escala,cvelas):
        ''' retorna el rsi maximo de las c velas, su posición y el rsi actual
        '''
        df=self.mercado.get_panda_df(self.par, escala, cvelas + 90) #self.velas[escala].panda_df(cvelas + 60)
        rsi = df.ta.rsi()
      
        maximo = 0
        l=len(rsi)
        mi = 0
        
        try:
            lneg = l * -1
            i = -1
            maximo = rsi.iloc[-1]
            mi = 1
            cvel = 1
            # print(f'if {rsi.iloc[-2]} < {rsi.iloc[-1]}:')
            while i > lneg:
                i -= 1
                cvel += 1
                if cvel > cvelas:
                    break
                # print(f'if {rsi.iloc[i-1]} > {rsi.iloc[i]}:')
                if rsi.iloc[i] > maximo:
                    mi = i
                    maximo = rsi.iloc[i]
            
        except Exception as e:
            self.log.log('Error rsi_maximo_y_pos', str(e)) 

        ret =  (round(maximo,2),mi*-1,round(rsi.iloc[-1],2))    
        self.cache_add( (escala,cvelas),ret )

        return    ret
    
    def volumen_calmado(self,escala,cvelas=1,coef_volumen=1):
        ''' considera calmado al volumen  de las ultimas cvelas cerradas
            si se encuentran por debajo del (promedio * coef_volumen)
            puedo usar a coef_volumen para disminuir aumentar el  promedio
        '''
        df=self.mercado.get_panda_df(self.par, escala, 90)     #self.velas[escala].panda_df(cvelas + 60)
        df_ema=ta.ma('ma',df['volume'],length=20)
        
        ivela = -1    #indice para recorrer en forma negativa
        ic=0          #velas cerradas
        calmado=True
        while ic < cvelas:
            if df.iloc[ivela]["closed"]:
                if df.iloc[ivela]["volume"] * coef_volumen > df_ema.iloc[ivela]:
                    calmado = False
                    break
                ic +=1    
            ivela -= 1
        
        return calmado

    def zona_de_alto_volumen(self,escala,vela_ini=-1,vela_fin=-20):
        ''' buaca un grupo de velas con volumen alto que indican una caía previa
        '''
        df=self.mercado.get_panda_df(self.par, escala)     #self.velas[escala].panda_df(cvelas + 60)
        df_ema=ta.ma('ma',df['volume'],length=15)
        
        lista=[]
              
        if vela_fin < -290:
            vela_fin = -290      

        ini_testigo = vela_fin - 10
        fin_testigo = vela_fin
        
        df_testigo=df_ema.iloc[ini_testigo:fin_testigo]
        df_zona = df_ema.iloc[vela_fin:vela_ini]
        df_actual = df_zona.iloc[-4:-1]
        
        vol_testigo = df_testigo.mean()
        vol_actual = df_actual.mean()

        lista=self.lista_picos_maximos(df_zona,5,2)

        if len(lista)>0:
            pos_pico = lista[0][0]
            vol_pico = lista[0][1]
        else:
            pos_pico = -1
            vol_pico = 0

        r_vol_pico = round( vol_pico /vol_testigo , 2 )    
        r_vol = round(vol_actual / vol_testigo, 2   )

        #calculo volumen/ema sobre al últimavela cerrada
        if df.iloc[-1]['closed']:
            i_cerrada = -1
        else:
            i_cerrada = -2
        vol_ema = df.iloc[i_cerrada]['volume'] / df_ema.iloc[i_cerrada]

        return pos_pico, r_vol_pico, r_vol, vol_ema

    def picos_de_alto_volumen(self,escala,vela_fin=-20):
        ''' busca picos de alto volumen
        '''
        df=self.mercado.get_panda_df(self.par, escala)     #self.velas[escala].panda_df(cvelas + 60)
        df_ema=ta.ma('ma',df['volume'],length=20)
              
        if vela_fin < -290:
            vela_fin = -290      

        df_zona = df['volume'].iloc[vela_fin:]
        
        lista_de_picos=self.lista_picos_maximos(df_zona,1,1)

        # elimino los picos bajos
        lista=[]
        for  pico in lista_de_picos:
            pos=pico[0]
            vol=pico[1]
            #self.log.log(pico,df_ema.iloc[-pos])
            if vol > df_ema.iloc[-pos] * 3:
                lista.append(pico)

        return lista

    def velas_de_impulso(self,escala,sentido=1,vela_fin=-20):
        ''' busca velas de alto volumen que provocan impulso
        '''
        df=self.mercado.get_panda_df(self.par, escala)     
        df_ma_vol=ta.ma('ma',df['volume'],length=20)

        cant_velas=len(df)      
        if vela_fin < -cant_velas+41:
            vela_fin = -cant_velas+41      

        lista=[]
        i= -1

        volumen_testigo = df_ma_vol.iloc[vela_fin -1]   #promedio del volumen anterior a la zona buscada
        if (volumen_testigo) >0:
 
            while i > vela_fin:
                i -= 1
                v:Vela = Vela(df.iloc[i])
                if v.sentido() == sentido:
                    x_vol = round( v.volume / volumen_testigo ,2)
                    if  x_vol > 3:   
                        lista.append([ i*-1, x_vol ])

        return lista  

    def xvolumen_de_impulso(self,escala,sentido=1,vela_fin=-20):
        ''' suma todo el volumen de impulso a la baja(sentido=-1) al alza(sentido=1) o todo(sentido=0) y lo devuelve comparado con 
            el volumen promedio
        '''
        df=self.mercado.get_panda_df(self.par, escala)     
        df_ma_vol=ta.ma('ma',df['volume'],length=20)

        cant_velas=len(df)      
        if vela_fin < -cant_velas+41:
            vela_fin = -cant_velas+41      

        i= -1
        xvol_impulso=0
        
        volumen_testigo = df_ma_vol.iloc[vela_fin -1]   #promedio del volumen anterior a la zona buscada
        sum_vol_impulso = 0
        if (volumen_testigo) >0:
            while i > vela_fin:
                i -= 1
                v:Vela = Vela(df.iloc[i])
                if sentido == 0:
                    sum_vol_impulso += v.volume 
                elif v.sentido() == sentido:
                    sum_vol_impulso += v.volume 
                     
            xvol_impulso =  round( sum_vol_impulso / volumen_testigo ,2)       
                    
        return xvol_impulso        


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

      

    
    
    
    
          

    

    
    


    def angulo_de_dos_pendientes(self,m1,m2):
        '''
        m1 es la pendiente mas suave
        m2 la mas rápida
        '''
        return degrees(atan( abs(m2-m1)/abs(1+m1*m2)  ) )

    #retorna verdadero si la ema rápida está por encima de la
    def ema_rapida_mayor_lenta(self,escala,per_rapida,per_lenta,diferencia_porcentual_minima=0):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es mayor diferencia_porcentual_minima, retora verdadero'''
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        df_emar=ta.ema(df['close'],length=per_rapida) 
        df_emal=ta.ema(df['close'],length=per_lenta)  

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
        #self.log.log(f'l {l},r {r},dif%  {diferencia_porcentual}, dif%min{diferencia_porcentual_minima}') 

        return diferencia_porcentual > diferencia_porcentual_minima

    def ema(self,escala,periodos):
        
        ret = self.get_cache('ema',(escala,periodos))
        if ret is None:
            df = self.get_df(self.par,escala)
            df_ema=ta.ema(df['close'],length=periodos) 
            ret = df_ema.iloc[-1]
            self.set_cache( 'ema',(escala,periodos),ret )

        return ret
    

    def get_df(self,par,escala):
        df =self.get_cache('get_panda_df',(par,escala))
        if df is None:
            df=self.mercado.get_panda_df(par,escala)
            self.set_cache( 'get_panda_df',(par,escala), df )
        return df    

    
    def ema_px(self,escala,periodos):
        ''' retorna la ema y el precio de cierre'''
        
        df=self.mercado.get_panda_df(self.par,escala,periodos+100)
        df_ema=ta.ema(df['close'],length=periodos) 
        
        ret = (df_ema.iloc[-1] ,df.iloc[-1]['close']  )
        
        return ret
    

    def ema_rapida_mayor_lenta2(self,escala,per_rapida,per_lenta,diferencia_porcentual_minima=0,pendientes_positivas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es mayor diferencia_porcentual_minima o las pendientes
        de ambas emas son positivas  retorna True, tambien retorna datos para log..
        si pendientes_positivas=True exige que las pendientes sean positivas al mismo tiempo que se de la diferencia porcentual''' 
        
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        try:
            df_emar=ta.ema(df['close'],length=per_rapida) 
            df_emal=ta.ema(df['close'],length=per_lenta)  
        except Exception as e:
            self.log.err('Error ema_rapida_mayor_lenta2',str(e)) 
            return (   False,0,0,0   )   

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
        

        df_ema1=ta.ema(df['close'],length=per_ema1) 
        df_ema2=ta.ema(df['close'],length=per_ema2)

        ret = False  
        if df_ema1.iloc[-1] > df_ema2.iloc[-1]:
            df_ema3=ta.ema(df['close'],length=per_ema3)
            if  df_ema2.iloc[-1] > df_ema3.iloc[-1]:
                ret = True
        return ret

    

    def ema_rapida_menor_lenta2(self,escala,per_rapida,per_lenta,diferencia_porcentual_maxima=0,pendientes_negativas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es menor diferencia_porcentual_maxima o las pendientes
        de ambas emas son negativa  retorna True, tambien retorna datos para log..
        si pendientes_negativas=True exige que las pendientes sean negativas al mismo tiempo que se de la diferencia porcentual''' 
        
        df=self.mercado.get_panda_df(self.par,escala,per_lenta+50)
        df_emar=ta.ema(df['close'],length=per_rapida) 
        df_emal=ta.ema(df['close'],length=per_lenta)  

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

   

    def precio_vector_completo(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
        return vector    

 
    def sombra_sup_grande_en_ultima_vela(self,escala,coeficiente,pos):
        
        vela=self.mercado.velas[escala].get_vela_desde_ultima(pos)
        
        ret=False
        nz=0.00000000001

        v=round(vela.sombra_sup() / (vela.cuerpo()+nz) ,2)

        if v>=coeficiente:
            ret= True
        
        return [ ret , v]    

    def rsi(self,escala,vela=0):
        
        df=self.mercado.get_panda_df(self.par, escala, 60) #self.velas[escala].panda_df(cvelas + 60)
        df_rsi = df.ta.rsi()
        rsi= round( df_rsi.iloc[-1]   ,2     )

        return rsi


    def pendiente_positiva_ema(self,escala,periodos):
        '''
        retorna True si la ultima dif entre la ultimaema y la anterior es positiva
        '''
        df=self.mercado.get_panda_df(self.par,escala,periodos+50)
        df_ema=ta.ema(df['close'],length=periodos) 
        

        pend=round( self.pendientes(escala,df_ema.to_list(),1)[0] * 100,9 )
        
        return pend >0 

    def pendientes_positivas_ema(self,escala,periodos,cpendientes=2):
        '''
        retorna True si las ultimas cpendientes son positivas
        '''
        df=self.get_df(self.par,escala)
        df_ema=ta.ema(df['close'],length=periodos) 
        
        pendientes = self.pendientes(escala,df_ema.to_list(),cpendientes)
        ret = True
        for p in pendientes:
            if p <0:
                ret =False
                break
        return ret

 
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
        precio = self.precio(escala)
        
        return variacion_absoluta(low[0],precio)
    
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

    def redondear_unidades(self,unidades):
        cant=unidades
        if  0 < cant <1:
            cant=round(cant,4)
        elif 1 <= cant <9:
            cant=round(cant,2)
        else:
           cant=int(cant)
        return cant 
                

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

    

    def precio(self,escala):
        try:
            vs: VelaSet = self.mercado.get_velaset(self.par,escala)
            px = vs.ultima_vela().close
        except Exception as ex:
            self.log.log(str(ex))
            px = -1
        return px   
    def diff_porcentaje(self,o,h,l,c):
        p0=1 - o/c
        p1=1 - h/l

        if abs(p0) > p1:
            return round( p0 * 100 ,2)
        else:
            return round( p1 * 100 ,2)    
        

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
        try:

            for esc in self.mercado.par_escala_ws_v[self.par].keys():
                
                actualizado[esc]=self.mercado.par_escala_ws_v[self.par][esc][1].actualizado

            mas_actualizado = sorted(actualizado.items(), key=lambda x: x[1] ,reverse=True   )[0]
            print(f'Escala_precio_mas_actualizado-->{mas_actualizado}')

            ret = self.precio(mas_actualizado[0]) #retorno el precio del mas actualizado

        except:
            ret = -1

        return ret       
    
    # def detectar_patrones(self,escala,cvelas):
        
    #     o = self.mercado.get_vector_np_open(self.par,escala,cvelas)
    #     h = self.mercado.get_vector_np_high(self.par,escala,cvelas)
    #     l = self.mercado.get_vector_np_low(self.par,escala,cvelas)
    #     c = self.mercado.get_vector_np_close(self.par,escala,cvelas)
    #     # recolecto todos los patrones que encuentro
         
    #     valor_patron={} # 1 sube, -1 baja
    #     valor_patron['CDLMATCHINGLOW']=1
        
    #     r_pos=0
    #     r_neg=0
    #     patrones=[]
    #     for f in talib.get_functions():
    #         if f.startswith('CDL'):
    #             func = getattr(talib, f)
    #             ret = func(o,h,l,c)
    #             #print(f,ret)
    #             if ret[-1]!=0:
    #                 patrones.append(f)
    #                 if ret[-1]>0:
    #                     r_pos += ret[-1]
    #                 else:
    #                     r_neg += ret[-1]    

    #     return {'alcista':r_pos,'bajista':r_neg,'patrones':patrones}         
    
    def el_precio_es_bajista(self,escala):
        ''' trato de definir si el precio es bajista cuando el precio es mayor que la ema de 50. 
        Tratando de evitar la que el resultado sea dudoso ante la compresión de emas (ema 20 muy cerca de ema50) para lo cual uso emas_ok.
        '''
        bajista = True
        if self.precio(escala) > self.ema(escala,50):
            emas_ok, _,_,pend_l = self.ema_rapida_mayor_lenta2(escala,20,50,0.5,True)
            if emas_ok and pend_l >0: 
                bajista = False
        
        return bajista

    # def precio_bajo_ema_importante(self,escala):
    #     ret = False
    #     emas_importantes=[('1d',20),('1d',50),('4h',20),('4h',50)]    
    #     for em in emas_importantes:
    #         escala=em[0]
    #         periodos=em[1]
    #         if self.precio_cerca_por_debajo(self.ema(escala,periodos)):
    #             self.log.log(f'precio bajo de ema{em}')
    #             ret = True
    #     return ret
    def precio_bajo_ema_importante(self,escala):
        ret = False
        periodos=[20,50]    
        for per in periodos:
            if self.precio_cerca_por_debajo_ema(escala,per):
                self.log.log(f'precio bajo de ema({per})')
                ret = True
        return ret

    def precio_cerca_por_debajo_ema(self,escala,per,porcentaje=0.30):
        ema=self.ema(escala,per)
        px = self.precio(escala)
        return ema < px and (px - ema) / ema *100 < porcentaje           
 

if __name__=='__main__':
    from variables_globales import VariablesEstado
    from binance.client import Client #para el cliente
    from pws import Pws
    #from acceso_db_conexion_mysqldb import Conexion_DB
    from acceso_db_conexion import Conexion_DB
    from acceso_db_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB
    
    from logger import Logger
    from no_se_usa.acceso_db import Acceso_DB
    
    log=Logger(f'test_indicadores.log')
    pws=Pws()
 
    conn=Conexion_DB(log)                          
    fxdb=Acceso_DB_Funciones(log,conn.pool)        
    db = Acceso_DB(log,fxdb)                       

    client = Client(pws.api_key, pws.api_secret)
    g = VariablesEstado()
    
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


    
