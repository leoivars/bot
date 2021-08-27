# # -*- coding: UTF-8 -*-
from vela import Vela
import numpy as np
import pandas as pd
import time
from threading import Lock

class VelaSet:
    proxima_vela={}
    def __init__(self,set_velas_web=None,cvelas=200): # recibe un conjunto inicial de velas y la cantidad de velas a memorizar
        self.cvelas=cvelas
        self.acceso = Lock() #mientras se actualiza el mercado, se debe bloquear esete loc
        self.actualizado = 0
        
        self.nuevoset(set_velas_web)
            
        
    def nuevoset(self,set_velas_web):
        
        try:
            self.acceso.acquire(True)
            self.df=pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume','close_time','closed'] )   
            self.acceso.release()
            
            if set_velas_web:
                self.poner_velas_en_df(set_velas_web)

        except Exception as e:
            print(str(e))


    def actualizar_actualizado(self):
        self.acceso.acquire(True)
        self.actualizado = time.time() 
        self.acceso.release()

    

    def poner_velas_db_en_df(self,cursor):
        #self.acceso.acquire(True)
        for fila in cursor:
            
            
            # print('------> fila',fila)
            # fila (1,                        1       1624046880000,    2  35571.3,     3  35629.3,      4    35568.7,    5    35622.4,   6 79.2398,           7  1624046939999)
            # fila {'id_par_escala': 1, 'open_time': 1624058340000, 'open': 35448.8, 'high': 35448.8, 'low': 35411.7, 'close': 35415.3, 'volume': 7.53343, 'close_time': 1624058399999}
            v_open_time=int(fila[1])
            v_open=float(fila[2])
            v_high=float(fila[3])
            v_low=float(fila[4])
            v_close=float(fila[5])
            v_volume=float(fila[6])
            v_close_time=int(fila[7])
            self.df.loc[v_open_time] = [v_open ,v_high ,v_low ,v_close ,v_volume,v_close_time,1]

        self.actualizado = time.time()
        #self.acceso.release()

    def poner_velas_en_df(self,set_velas_web):
        self.acceso.acquire(True)

        for vela_web in (set_velas_web):
            #print('------> velaweb',vela_web)
            v_open_time=int(vela_web[0])
            v_open=float(vela_web[1])
            v_high=float(vela_web[2])
            v_low=float(vela_web[3])
            v_close=float(vela_web[4])
            v_volume=float(vela_web[5])
            v_close_time=int(vela_web[6])
            self.df.loc[v_open_time] = [v_open ,v_high ,v_low ,v_close ,v_volume,v_close_time,1]

        self.actualizado = time.time()
        self.acceso.release()

    def poner_vela_socket_en_df(self,v_open_time,v_open,v_high,v_low,v_close,v_volume,v_close_time,v_is_closed):
        
        #print ('poner_vela_socket_en_df',v_open_time,v_open,v_high,v_low,v_close,v_volume,v_close_time,v_is_closed)
        self.acceso.acquire(True)
        try:
         
            self.df.loc[v_open_time] = [v_open ,v_high ,v_low ,v_close ,v_volume,v_close_time,v_is_closed] 
            #elimina las velas exedids del máximo establecido en cvelas
            if v_is_closed:
                cvelas_exedidas = len(self.df) - self.cvelas
                if cvelas_exedidas > 0 :
                    self.df.drop( self.df.index[:cvelas_exedidas], inplace=True)

            self.actualizado = time.time()     

        except Exception as e:
            #pass
            print(str(e))
        
        self.acceso.release()    
        
    # def release_y_sleep(self):
    #     self.acceso.release()
    #     time.sleep(0.075)

    def actualizar(self,set_velas_web):

        
        try:
            #agrega las velas recuperadas
            self.poner_velas_en_df(set_velas_web)

            #elimina las velas exedids del máximo establecido en cvelas
            cvelas_exedidas = len(self.df) - self.cvelas
            if cvelas_exedidas > 0 :
                self.acceso.acquire(True)
                self.df.drop( self.df.index[:cvelas_exedidas], inplace=True)
                self.acceso.release()

        except Exception as e:
            print(str(e))
           

    def i_desde_final(self,cant_valores,signo = -1):
        if cant_valores is None:
            i =  (len(self.df)-1)
        elif cant_valores > len(self.df):
            i =  (len(self.df)-1)
        else:
            i =  cant_valores
        return i * signo   

    def valores_np_high(self,cant_valores=None):
        
        i = self.i_desde_final(cant_valores)
        ret = self.df['High'][i:].to_numpy()
           
        return ret

    
    def valores_np_low(self,cant_valores=None):
        
        i = self.i_desde_final(cant_valores)
        ret = self.df['Low'][i:].to_numpy()
           
        return ret


    def valores_np_open(self,cant_valores=None):
        
        i = self.i_desde_final(cant_valores)
        ret = self.df['Open'][i:].to_numpy()
           
        return ret


    def valores_np_close(self,cant_valores=None):
        
        i = self.i_desde_final(cant_valores)
        ret = self.df['Close'][i:].to_numpy()
           
        return ret

    def valores_np_volume(self,cant_valores=None):
        
        i = self.i_desde_final(cant_valores)
        ret = self.df['Volume'][i:].to_numpy()
           
        return ret

    def panda_df(self,pvelas=None):
        
        i = self.i_desde_final(pvelas,1)
        ret = self.df.tail(i)
           
        return ret

    
    def ultima_vela(self):
        
        v = Vela( self.df.iloc[ -1 ], self.df.index[-1] )
           
        return v

    def ultima_vela_cerrada(self):
        if self.df.iloc[-1]["closed"]:
            v = Vela( self.df.iloc[ -1 ], self.df.index[-1] )
        else:
                v = Vela( self.df.iloc[ -2 ], self.df.index[-2] )   
        
        return v
        
    def get_vela_desde_ultima(self,pos):
        
        v = Vela( self.df.iloc[ pos * -1 ] , self.df.index[ pos * -1] )
           
        return v

    def get_vela(self,pos):
        
        v = Vela( self.df.iloc[ pos ] ,self.df.index[pos] )
           
        return v

    
    def inconsistencias(self):
        i_inconsistente = -1
        for i in range(len(self.df)-1,0,-1) :
            ct_aterior = self.df.iloc[i-1]["close_time"]
            ot_actual = self.df.index[i]
            #print ('ct_aterior+1 != ot_actual',ct_aterior+1 , ot_actual, i,self.df.index[i], self.df.iloc[i]["close_time"] )
            if ct_aterior+1 != ot_actual:
             #   print ('asigno')
                i_inconsistente = i -1 
                break
        
        return i_inconsistente    

    

    # def tiempo_desactualizado(self):
    #     if self.df is None or len(self.df)==0:
    #         return 999999
    #     tiempo = 999999
    #     inicio = len(self.df)*-1
    #     for i in range(-1,inicio):
    #         if not self.df.iloc[-i]["closed"]:
    #             tiempo =  = self.df.index[i]



            



