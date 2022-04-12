

import time
from velaset import VelaSet
from websocket import create_connection,WebSocketTimeoutException,WebSocketConnectionClosedException
from threading import Thread
import json
from mercado_actualizador_rest import Actualizador_rest
from variables_globales import Global_State
import traceback


class Mercado_Actualizador_Socket(Thread):
    
    def __init__(self,log,estado_general,par_escala_ws_v,cliente):
        Thread.__init__(self)
        self.subscripciones={}
        self.id = 1
        self.espera=2
        self.time_conexion=0
        self.time_ultima_recepcion=0
        self.tiempo_ultimo_pong = time.time()
        self.tiempo_maximo_sin_recibir_datos=60
        
        self.activo = False
        self.vivo = True

        self.par_escala_ws_v=par_escala_ws_v
        self.g:Global_State = estado_general
        self.actualizador_rest= Actualizador_rest(log,estado_general,cliente)
        self.log=log
        self.ws = None

    def run(self):  
        try:
           self.ws =  self.conectar()
           self.activo = True
           self.time_conexion = time.time()
           while self.activo:
               self.recibir()
               self.renovar_conexion_fea()
               time.sleep(self.espera)

           self.ws.close
           self.vivo = False 
             
        except Exception as e:
            print('Error,run()',str(e)) 
            tb = traceback.format_exc()
            self.log.log(tb)

    def conectar(self):
        while True:
            try:
                ws = create_connection("wss://stream.binance.com:9443/ws")       
                ws.settimeout(300)
                #self.log.log('conectado',str(ws)) 
                break
            except Exception as e:
                self.log.log('Error en conectar()',str(e))
                time.sleep(5)
        return ws    

    def recibir(self):
        try:       
            result =  self.ws.recv()
            self.procesar_recibido(result) 
        except  Exception as e:
            #self.log.log('recibir()', str(e))
            self.renovar_conexion()

    def renovar_conexion_fea(self):
        
        if time.time() - self.time_ultima_recepcion > self.tiempo_maximo_sin_recibir_datos:
            self.renovar_conexion()
        else:
            if time.time() - self.time_conexion > 79200: #22 horas
                self.renovar_conexion()

    def mantener_vivo(self):
        ''' envía un pong cada 30 minutos 1 seg para mantener viva la conexion'''
        tp=time.time() - self.tiempo_ultimo_pong
        if tp > 1801:
            try:
                self.ws.pong()
                self.tiempo_ultimo_ping = time.time()
            except Exception as e:
                self.log.log('Error en mantener_vivo',str(e))
                if 'WebSocket' in str(e):
                    self.renovar_conexion()    
                

    def detener(self):
        self.activo = False        

    def renovar_conexion(self):
        #self.log.log('-------renovar_conexion----------')
        ws_nuevo = self.conectar()
        time.sleep(1)
        self.renovar_suscribir(ws_nuevo)
        time.sleep( 1 + len(self.subscripciones) )
        ws_viejo=self.ws
        self.ws=ws_nuevo
        self.time_conexion = time.time()
        self.time_ultima_recepcion= self.time_conexion
        try: 
            ws_viejo.close()
        except Exception as e:
            self.log.log('error renovar_conexion',str(e))    

    
    def renovar_suscribir(self,ws):
        for par_escala in self.subscripciones:
            suscribirse = {
                    "method": "SUBSCRIBE",
                    "params":
                        [
                        par_escala
                        ],
                        "id": self.subscripciones[par_escala]
                }
            self.__enviar(suscribirse,ws)
    
    def crear_velaset(self,par,escala):
        self.par_escala_ws_v[par][escala][1]=self.actualizador_rest.cargainicial(par,escala)
        #self.par_escala_ws_v[par][escala][1]=VelaSet()


    def suscribir(self,par,escala):
        
        self.crear_velaset(par,escala)
        par = par.lower()
        par_escala = f"{par}@kline_{escala}"
        if par_escala not in self.subscripciones:
            suscribirse = {
                "method": "SUBSCRIBE",
                "params":
                    [
                    par_escala
                    ],
                    "id": self.id
            }
            self.__enviar(suscribirse)
            self.subscripciones[par_escala]=self.id
            self.id  += 1
            self.__ajustar_espera()
            self.__tiempo_maximo_sin_recibir_datos_set()
        else:
            print( par_escala,'ya estaba suscripto')    
    
    def desuscribir(self,par,escala):
        par = par.lower()
        par_escala = f"{par}@kline_{escala}"
        if par_escala in self.subscripciones:
            desuscribirse = {
                "method": "UNSUBSCRIBE",
                "params":
                    [
                    par_escala
                    ],
                    "id": self.subscripciones[par_escala]
            }
            self.__enviar(desuscribirse) 
            del self.subscripciones[par_escala]
            self.__ajustar_espera()
            self.__tiempo_maximo_sin_recibir_datos_set()

        else: 
            print('no se puede desuscribir...')        

    def __ajustar_espera(self): 
        self.espera = 1.8 / (len (self.subscripciones) +1)   
    
    def __enviar(self,mensaje,ws=None):
        if ws is None:
            ws = self.ws
        try:
            msg = str( json.dumps(mensaje) )
            ws.send( msg    )
            #self.log.log(self.ws,msg)
            time.sleep(1)
        except Exception as e:
            print('Error al enviar:',e)

        #self.ws.lock.release()
        
        #print('__enviar release')     

    def __recibir(self):
        ret = None
        print('__recibir acquire')
        #self.lock_ws.acquire(True)
        try:
            ret = self.ws.recv()
        except Exception as e:
            print(e)

        #self.lock_ws.release()
        time.sleep(0.001)
        print('__recibir release')

        return ret

    def __tiempo_maximo_sin_recibir_datos_set(self):
        tiempo=3600
        for sub in self.subscripciones:
            escala=sub.split('_',1  )[1]
            t = self.g.escala_tiempo[escala]
            tiempo = min(t,tiempo)
        self.tiempo_maximo_sin_recibir_datos = tiempo    
        #self.ws.settimeout(tiempo * .9)

    def procesar_recibido(self,result):
        
        if result:
            self.time_ultima_recepcion = time.time()
            #print(result)
            jresult=json.loads(result)
            #print('-->', result)
            #print('jj>', jresult)
            if 'e' in jresult:
                if  jresult['e']=='kline':
                    #print (jresult['s'])
                    k = jresult['k']
                    par=k['s']
                    escala=k['i']
                    v_open_time =  int(k['t'])
                    v_close_time = int(k['T'])   
                    v_is_closed = int(k['x'] )
                    v_open = float( k['o'] )
                    v_high = float( k['h']  )
                    v_low = float( k['l']  )
                    v_close = float( k['c'] )
                    v_volume = float( k['v'] )
                    #print(k['is_closed'],is_closed,type(is_closed))
                        
                    self.par_escala_ws_v[par][escala][1].poner_vela_socket_en_df(v_open_time,v_open,v_high,v_low,v_close,v_volume,v_close_time,v_is_closed)
                    
                    #if v_is_closed:
                        #print(par,escala,v_volume)
            else:
                print('-no-k->',jresult)            
        # except Exception as e:
        #     print('Error en procesar_recibido:',str(e))  
        #     tb = traceback.format_exc()
        #     print(tb) 
        #     print(f'--->{result}<---')             

