# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from acceso_db_conexion_mysqldb import Conexion_DB
from logger import Logger
from acceso_db_mysqldb import Acceso_DB
from os import register_at_fork
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
from datetime import datetime,timedelta

import pandas as pd
import pandas_ta as ta

from  variables_globales import VariablesEstado

from cola_de_uso import Cola_de_uso

from funciones_utiles import strtime_a_obj_fecha,timestampk_to_strtime

from mercado_actualizador_socket import Mercado_Actualizador_Socket

from datos_par import Datos_par

#from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager



class Mercado_Back_Testing:
    '''
    Contenedor de los datos del mercado extraídos de la base de datos
    '''
    #usar_sokcet={'1m':False,'5m':True,'15m':True,'30m':True,'1h':True,'2h':False,'4h':True,'1d':True,'1w':True,'1M':False}
        
    def __init__(self,log,estado_general,acceso_db):

        self.g:VariablesEstado = estado_general
        self.log=log
        self.par_escala_ws_v={} # en que soket está el par escala self.par_escala_ws[par][escala]=[ws,Velaset]
        self.db:Acceso_DB = acceso_db


    def inicar_mercados(self,fecha_fin,cvelas,lista_pares,lista_escalas):
        self.lista_pares=lista_pares
        self.lista_escalas=lista_escalas
        self.fecha_fin: datetime= fecha_fin
        for par in lista_pares:
            for esc in lista_escalas:
                self.registrar_df(par,esc)
                fecha_ini = fecha_fin - timedelta( seconds= self.g.escala_tiempo[esc] * (cvelas  ) ) #calculo fecha inicial en funcion de las velas solicitadas
                vs=VelaSet(None,cvelas)
                self.par_escala_ws_v[par][esc]=[None,vs]
                cursor = self.db.get_velas_rango(par,esc,fecha_ini.timestamp()*1000,fecha_fin.timestamp()*1000 )
                vs.poner_velas_db_en_df(cursor)


    def actualizar_mercados(self,nuevo=False):
        for par in self.lista_pares:
            for esc in self.lista_escalas:
                vsviejo:VelaSet=self.par_escala_ws_v[par][esc][1]
                cvelas = vsviejo.cvelas
                fecha_ini = self.fecha_fin - timedelta( seconds= self.g.escala_tiempo[esc] * (cvelas +1 ) ) #calculo fecha inicial en funcion de las velas solicitadas
                if nuevo:
                    vs=VelaSet(None,cvelas)
                    self.par_escala_ws_v[par][esc]=[None,vs]
                else:    
                    vs:VelaSet=self.par_escala_ws_v[par][esc][1]
                #print('FECHA_INI',  timestampk_to_strtime(fecha_ini),fecha_ini,self.fecha_fin.timestamp()*1000 )
                cursor = self.db.get_velas_rango(par,esc,fecha_ini.timestamp()*1000,self.fecha_fin.timestamp()*1000 )
                vs.poner_velas_db_en_df(cursor)
                

    def actualizar_mercados_a_vela(self,open_time):
        self.fecha_fin = datetime.fromtimestamp(open_time/1000)
        self.actualizar_mercados(nuevo=True)
    
    def avanzar_tiempo(self,delta_t):
        self.fecha_fin = self.fecha_fin + delta_t

    def avanzar_vela(self,par,escala,id_par_escala):
        '''
        ojo solo avanza una vela de un par en una escala 
        '''
        vs:VelaSet=self.par_escala_ws_v[par][escala][1]
        uv:Vela=vs.ultima_vela()
        cursor = self.db.get_vela_siguiente(id_par_escala,uv.open_time)
        if len(cursor)==0:
            ret = False
        else:    
            vs.poner_velas_db_en_df(cursor)
            uv1:Vela=vs.ultima_vela()
            self.fecha_fin_tsb = uv1.open_time
            ret = True
        return ret    
    # def avanzar_vela(self,par,escala):
    #     '''
    #     ojo solo avanza una vela de un par en una escala 
    #     '''
    #     vs:VelaSet=self.par_escala_ws_v[par][escala][1]
    #     uv:Vela=vs.ultima_vela()
    #     fecha_ini = uv.close_time
    #     fecha_fin = fecha_ini + self.g.escala_tiempo[escala]
    #     cursor = self.db.get_velas_rango(par,escala,fecha_ini,fecha_fin)
    #     vs.poner_velas_db_en_df(cursor)
    #     uv1:Vela=vs.ultima_vela()
    #     self.fecha_fin_tsb = uv1.open_time
    #     return uv.open_time != uv1.open_time

    def open_time_ultima_vela(self,par,esc):
        vs:VelaSet=self.par_escala_ws_v[par][esc][1]
        uv:Vela=vs.ultima_vela()
        return uv.open_time
    
    

    def registrar_df(self,par,escala):
        if par in self.par_escala_ws_v:
            self.par_escala_ws_v[par][escala]=[None,None]
        else:
            self.par_escala_ws_v[par] = {escala : [None,None]}            



    def get_vector_np_open(self,par,escala,cant_valores=None):
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.valores_np_open(cant_valores)

    def get_vector_np_close(self,par,escala,cant_valores=None):
        #print( '---------------------->', self.par_escala_ws_v[par][escala][1]   )
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.valores_np_close(cant_valores)
        
    def get_vector_np_high(self,par,escala,cant_valores=None):
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.valores_np_high(cant_valores)

    def get_vector_np_low(self,par,escala,cant_valores=None):
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.valores_np_low(cant_valores)

    def get_vector_np_volume(self,par,escala,cant_valores=None):
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.valores_np_volume(cant_valores)
    
    def get_panda_df(self,par,escala,cant_valores=None):
        vs: VelaSet = self.par_escala_ws_v[par][escala][1]
        return vs.panda_df(cant_valores) 

    def get_velaset(self,par,escala):
        vs = self.par_escala_ws_v[par][escala][1]

        return vs       


if __name__ == '__main__':
    from variables_globales import VariablesEstado
    from gestor_de_posicion import Gestor_de_Posicion
    from binance.client import Client #para el cliente
    from pws import Pws
    
    

    log=Logger('Test_mercado.log')
    pws=Pws()
    
    client = Client(pws.api_key, pws.api_secret)
    
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn)

    p = Gestor_de_Posicion(log,client,conn)
    globales = VariablesEstado(p)

    m=Mercado_Back_Testing(log,globales,db)

    fecha_fin =  strtime_a_obj_fecha('2021-07-18 20:00:00')
    un_minuto = timedelta(minutes=1)
    
    m.inicar_mercados(fecha_fin,200,['BTCUSDT'],['1m'])
    vs:VelaSet = m.par_escala_ws_v['BTCUSDT']['1m'][1]
    
    for _ in range(1,20):
        print(m.get_vector_np_close('BTCUSDT','1m',5))
        m.avanzar_tiempo(un_minuto)
        m.actualizar_mercados()
    


   

         



    
        