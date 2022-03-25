# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from vela import Vela
from velaset import VelaSet
from binance.client import Client
import time
import pandas as pd
from  variables_globales import Global_State
from funciones_utiles import variacion,compara,signo
from mercado_actualizador_socket import Mercado_Actualizador_Socket

class Mercado:
    '''
    Contenedor de los datos del mercado y coordinador entre el actualizador_rest y el actualizador_socket
    '''
    #usar_sokcet={'1m':False,'5m':True,'15m':True,'30m':True,'1h':True,'2h':False,'4h':True,'1d':True,'1w':True,'1M':False}
        
    def __init__(self,log,estado_general,cliente):
        pd.set_option('mode.chained_assignment', None)

        self.g:Global_State = estado_general
        self.log=log
        self.cliente = cliente 
        
        self.max_suscripciones_por_ws = 1 # hasta 1024 #hay que encontrar un nro que se a posible de procesar al tiempo que no me llene d esockets abiertos
        self.par_escala_ws_v={} # en que soket está el par escala self.par_escala_ws[par][escala]=[ws,Velaset]
        self.sockets=[] #   sockets abiertos
       
    def __suscribir(self,par,escala):
        ws=self.get_ws(par,escala)
        if ws is  None:
            ws = self.__encontrar_socket_libre()  

        self.__agregar_ws(ws,par,escala)  
        ws.suscribir(par,escala)

    def __desubribir(self,par,escala):
        ws:Mercado_Actualizador_Socket = self.get_ws(par,escala)
        if ws:
            ws.desuscribir(par,escala)
            self.__eliminar_ws(par,escala)
            if self.get_suscripciones(ws) == 0:
                ws.detener()
                while ws.vivo:
                    time.sleep(.25)

    def desuscribir_todas_las_escalas(self,par):
        if par in self.par_escala_ws_v:
            escalas=[] # cargo las escalas en un vector porque, desuscribir modifica a self.par_escala_ws_v[par]
            for esc in self.par_escala_ws_v[par]:
                escalas.append(esc)
            for esc in escalas:
                self.__desubribir(par,esc)


    def get_ws(self,par,escala):
        ''' obtiene el ws de la estructura self.par_escala_ws_v si no lo encuentra retorna None'''
        try:
            ws=self.par_escala_ws_v[par][escala][0]
        except:
            ws=None
        return ws    

    def __agregar_ws(self,ws,par,escala):
        if par in self.par_escala_ws_v:
            self.par_escala_ws_v[par][escala]=[ws,None]
        else:
            self.par_escala_ws_v[par] = {escala : [ws,None]}

    def __eliminar_ws(self,par,escala):
        if len(self.par_escala_ws_v[par]) == 1:
            del self.par_escala_ws_v[par]
        else:
            del self.par_escala_ws_v[par][escala] 

    def get_suscripciones(self,ws:Mercado_Actualizador_Socket):
        cant=0
        for p in self.par_escala_ws_v:
            for e in self.par_escala_ws_v[p]:
                if ws==self.par_escala_ws_v[p][e][0]:
                    cant += 1
        return cant

    def agregar_nuevo_socket(self):
        sock =  Mercado_Actualizador_Socket(self.log,self.g,self.par_escala_ws_v,self.cliente) 
        sock.start()
        #esparear hasta que se establezca la conexión
        while not sock.activo:
            time.sleep(1)
        return sock

    def __encontrar_socket_libre(self):
        libre  = None
        sockets= self.__get_sockets_abiertos()
        for ws  in sockets:
            if sockets[ws] < self.max_suscripciones_por_ws:
                libre = ws
                break

        if libre is None: #no hay libres, creo uno nuevo
            libre = self.agregar_nuevo_socket()
        
        return libre
    
    def __get_sockets_abiertos(self):
        sockets={}
        for p in self.par_escala_ws_v:
            for e in self.par_escala_ws_v[p]:
                ws = self.par_escala_ws_v[p][e][0]
                if ws in sockets:
                    sockets[ws] += 1
                else:
                    sockets[ws] = 1

        return sockets




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
            self.__suscribir(par,escala)

        vs = self.par_escala_ws_v[par][escala][1]

        return vs
            
    def precio(self,par,escala):
        try:
            vs: VelaSet = self.get_velaset(par,escala)
            px = vs.ultima_vela().close
        except:
            px = -1
        return px 

    def vela(self,par,escala,posicion):
        try:
            vs: VelaSet = self.get_velaset(par,escala)
            ret:Vela = vs.get_vela(posicion)
        except:
            ret = None
        return ret    






    
        