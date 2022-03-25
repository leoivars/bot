

import time
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
from variables_globales import Global_State
import threading
from mercado_actualizador_rest import Actualizador_rest
from wsbinance import WS_binance


class Actualizador_socket:
    ''' responsable de alctualizar via socket '''

    
    def __init__(self,log,estado_general,vpar,cliente,escala):
        
        self.g:Global_State = estado_general
        self.actualizador_rest= Actualizador_rest(log,estado_general,cliente)
        
        self.log=log
        self.ws = WS_binance(vpar)
        

    def detener(self):
        #stream_id= self.binance_websocket_api_manager.get_stream_id_by_label(self.par)
        #self.binance_websocket_api_manager.kill_stream(stream_id) 
        
        #self.binance_websocket_api_manager.unsubscribe_from_stream(self.stream_id, channels =[ self.channel   ] ) 
        #self.binance_websocket_api_manager.kill_stream(self.stream_id)
        #time.sleep(.25)
        
        self.desuscribir_canal()
        self.binance_websocket_api_manager.stop_stream(self.stream_id)
        time.sleep(1)
        self.worker_working = False

        
        
        #self.binance_websocket_api_manager.delete_listen_key_by_stream_id
        #time.sleep(1)
        
        #self.binance_websocket_api_manager.stop_stream_as_crash(self.stream_id)
        #time.sleep(1)

        #self.esperar_payload_vacio()



    def esperar_payload_vacio(self):
        while True:
            time.sleep(.25)
            info = self.binance_websocket_api_manager.get_stream_info( self.stream_id )
            try:
                if len(info['payload']) == 0:
                    break
            except Exception:
                break





        #self.binance_websocket_api_manager.get_stream_subscriptions(self.stream_id)
        
        # time.sleep(1)
        # for _ in range(5):
        #      info = self.binance_websocket_api_manager.get_stream_info( self.stream_id )
        #      print(info['status'],type(info['status']))
        #      time.sleep(5)
        #self.binance_websocket_api_manager.sto     
        
        #self.binance_websocket_api_manager.print_stream_info(self.stream_id)
        
        #time.sleep(3)
        
        #self.binance_websocket_api_manager.delete_stream_from_stream_list(self.stream_id)
        
        #self.stream_id=None

        

    def iniciar(self):
        self.worker_thread = threading.Thread(target=self.procesar_lo_que_llega)#, args=(binance_websocket_api_manager))
        self.worker_working = True
        self.worker_thread.start()

    def suscribir(self,par,escala):
        ''' Suscribe el par, escala a un stream existente o crea uno nuevo según corresponda '''
        
        
        if self.stream_id is None:
            self.stream_id = self.binance_websocket_api_manager.create_stream(  [self.channel], [par.lower()] ,output="UnicornFy") 
            print ( self.stream_id )
            time.sleep(.5)
        else:    
            info = self.binance_websocket_api_manager.get_stream_info( self.stream_id ) 
            if par.lower() in info['markets']: # está en el canal
                self.binance_websocket_api_manager.unsubscribe_from_stream(self.stream_id ,channels=[self.channel]  ,markets=[par.lower()] ) 
                time.sleep(.1) 
            self.binance_websocket_api_manager.subscribe_to_stream(self.stream_id, channels=[self.channel] , markets=[par.lower()])
            time.sleep(.1)

        self.esperar_payload_vacio()    
       

        if not self.worker_working:
            self.iniciar()    

        #comentado porque estoy haciendo el test pero hay que descomentar despues    
        #self.vpar[par][escala]=self.actualizador_rest.cargainicial(par,escala)
        
        
        self.binance_websocket_api_manager.print_stream_info(self.stream_id)

    

    def desuscribir(self,par):
        '''  quita el par de stream'''
       # kline = par.lower()+'@kline_'+escala
        if self.stream_id is None:
            print('No hay stream, no me puedo desuscribir')
        else:    
            self.binance_websocket_api_manager.unsubscribe_from_stream( self.stream_id, markets=[par.lower()]  )  
            
            self.binance_websocket_api_manager.print_stream_info(self.stream_id)
            time.sleep(1)

        self.esperar_payload_vacio()  

    def desuscribir_canal(self):
        '''  quita el par de stream'''
       # kline = par.lower()+'@kline_'+escala
        if self.stream_id is None:
            print('No hay stream, no me puedo desuscribir')
        else:    
            self.binance_websocket_api_manager.unsubscribe_from_stream( self.stream_id, channels=[self.channel]  )  
            
            self.binance_websocket_api_manager.print_stream_info(self.stream_id)
            time.sleep(1)

        self.esperar_payload_vacio()        

    
    
    def imprimir_info(self):
        self.binance_websocket_api_manager.print_stream_info(self.stream_id)

    def procesar_lo_que_llega(self):
        #print('Estoy mirando...')
        
        while self.worker_working:
            #print('procesar_lo_que_llega')

            try:
                
                buffer = self.binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
                #print(buffer)

                if buffer:
                    
                    #print(buffer)
                    par=buffer['symbol']
                    k = buffer['kline']
                    escala=k['interval']
                    v_open_time =  int(k['kline_start_time'])
                    v_close_time = int(k['kline_close_time'])   
                    v_is_closed = bool(k['is_closed'] )
                    v_open = float( k['open_price'] )
                    v_high = float( k['high_price']  )
                    v_low = float( k['low_price']  )
                    v_close = float( k['close_price'] )
                    v_volume = float( k['base_volume'] )
                    #print(k['is_closed'],is_closed,type(is_closed))
                    
                    self.vpar[par][escala].poner_vela_socket_en_df(v_open_time,v_open,v_high,v_low,v_close,v_volume,v_close_time,v_is_closed)
                    

            except Exception as e: 
                pass
                #print('err-->',str(e))

            time.sleep(.25)
            #self.control_socket()    

        print('ya me mori...')    

    def control_socket(self):
        print( self.binance_websocket_api_manager.get_binance_api_status)
        print( self.binance_websocket_api_manager.get_monitoring_status_icinga)
        print( self.binance_websocket_api_manager.get_reconnects)



            

