# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from velaset import VelaSet
from binance.client import Client
import time
import pandas as pd
from  variables_globales import VariablesEstado
from funciones_utiles import variacion,compara,signo
from mercado_actualizador_socket import Mercado_Actualizador_Socket

class Mercado:
    '''
    Contenedor de los datos del mercado y coordinador entre el actualizador_rest y el actualizador_socket
    '''
    #usar_sokcet={'1m':False,'5m':True,'15m':True,'30m':True,'1h':True,'2h':False,'4h':True,'1d':True,'1w':True,'1M':False}
        
    def __init__(self,log,estado_general,cliente):
        pd.set_option('mode.chained_assignment', None)

        self.g:VariablesEstado = estado_general
        self.log=log
        self.cliente = cliente
        
        self.par_escala_ws_v={} # en que soket está el par escala self.par_escala_ws[par][escala]=[ws,Velaset]
        self.sockets=[] # lista de socket abiertos
        
        self.max_suscripciones_por_ws = 1 # hasta 1024 #hay que encontrar un nro que se a posible de procesar al tiempo que no me llene d esockets abiertos

       # self.actualizador_rest= Actualizador_rest(par,log,estado_general,cliente,self.velas,self.actualizado,self.lock_actualizado)    

        # carga inicial
        #self.actualizador_rest.actualizar_velas(escala)

        #inicio del actualización via socket

    def suscribir(self,par,escala):
        ws=self.get_ws(par,escala)
        if ws is  None:
            ws = self.encontrar_socket_libre()  

        self.registrar_ws(ws,par,escala)  
        ws.suscribir(par,escala)

    def get_ws(self,par,escala):
        ''' obtiene el ws de la estructura self.par_escala_ws_v si no lo encuentra retorna None'''
        try:
            ws=self.par_escala_ws_v[par][escala][0]
        except:
            ws=None
        return ws    

    def registrar_ws(self,ws,par,escala):
        if par in self.par_escala_ws_v:
            self.par_escala_ws_v[par][escala]=[ws,None]
        else:
            self.par_escala_ws_v[par] = {escala : [ws,None]}

    def eliminar_ws(self,par,escala):
        if len(self.par_escala_ws_v[par]) == 1:
            del self.par_escala_ws_v[par]
        else:
            del self.par_escala_ws_v[par][escala] 
    
    def desuscribir_todas_las_escalas(self,par):
        pass

    def agregar_nuevo_socket(self):
        sock =  Mercado_Actualizador_Socket(self.log,self.g,self.par_escala_ws_v,self.cliente) 
        self.sockets.append(sock)
        sock.start()
        #esparear hasta que se establezca la conexión
        while not sock.activo:
            time.sleep(1)
        return sock

    def encontrar_socket_libre(self):
        libre  = None
        for sock  in self.sockets:
            if len( sock.subscripciones ) < self.max_suscripciones_por_ws:
                libre = sock
                break

        if libre is None: #no hay libres, creo uno nuevo
            libre = self.agregar_nuevo_socket()
        
        return libre

    def detener_sockets(self):
        for ws in self.sockets:
           ws.detener()

    def get_vector_np_open(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.valores_np_open(cant_valores)

    def get_vector_np_close(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.valores_np_close(cant_valores)

    def get_vector_np_high(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.valores_np_high(cant_valores)

    def get_vector_np_low(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.valores_np_low(cant_valores)

    def get_vector_np_volume(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.valores_np_volume(cant_valores)
    
    def get_panda_df(self,par,escala,cant_valores=None):
        vs: VelaSet = self.get_velaset(par,escala)
        return vs.panda_df(cant_valores)

    def get_velaset(self,par,escala):
        ''' asegura que un velaset esté suscripto y si no es así, lo susbribe'''
        if par in self.par_escala_ws_v:
            if escala in self.par_escala_ws_v[par]:
                suscribir = False
            else:
                suscribir = True
        else:
            suscribir = True

        if suscribir:
            self.suscribir(par,escala)

        vs = self.par_escala_ws_v[par][escala][1]

        return vs
            







    
        