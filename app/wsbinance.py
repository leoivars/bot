import time
from websocket import create_connection
import json
from threading import Thread#, Lock

class WS_binance(Thread):
    subscripciones={}
    def __init__(self,vpar):
        Thread.__init__(self)
        self.activo = False
        self.id = 1
        self.espera=2
        self.time_conexion=0
        self.time_ultima_recepcion=0
        self.vpar=vpar
  
    def run(self):    
        try:
           self.ws = create_connection("wss://stream.binance.com:9443/ws")   #,enable_multithread=True
           self.activo = True
           self.time_conexion = time.time()
           while self.activo:
               #print('.')
               result =  self.ws.recv()
               self.procesar_recibido(result)
               
               time.sleep(self.espera)
        except Exception as e:
            print(str(e)) 
    

    def renovar_conexion(self):
        #print('----------------renovar-------------conexion-----------')
        ws_nuevo = create_connection("wss://stream.binance.com:9443/ws")
        self.renovar_suscribir(ws_nuevo)
        time.sleep( 1 + len(self.subscripciones) )
        ws_viejo=self.ws
        self.ws=ws_nuevo
        ws_viejo.close()

    
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
    
    def suscribir(self,par,escala):
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

        else: 
            print('no se puede desuscribir...')        

    def __ajustar_espera(self): 
        espera = 1.8 / (len (self.subscripciones) +1)   
    
    def __enviar(self,mensaje,ws=None):
        if ws is None:
            ws = self.ws
        #print('__enviar',mensaje)     
        #self.ws.lock.acquire(True)
        
        try:
            
            ws.send( str(      json.dumps(mensaje)    )     )
        except Exception as e:
            print('---------0000000000000000000000000000-------->',e)

        #self.ws.lock.release()
        time.sleep(0.001)
        ##print('__enviar release')     

    def __recibir(self):
        ret = None
        #print('__recibir acquire')
        #self.lock_ws.acquire(True)
        try:
            ret = self.ws.recv()
        except Exception as e:
            print(e)

        #self.lock_ws.release()
        time.sleep(0.001)
        #print('__recibir release')

        return ret
    
    
    def procesar_recibido(self,result):
        jresult=json.loads(result)
        ##print('-->', result)
        ##print('jj>', jresult)
        #if 'e' in jresult:
        #    if  jresult['e']=='kline':
                #print (jresult['s'])
                ##print (jresult['k'])

        ##print(result)


    #{'e': 'kline', 'E': 1621565351925, 's': 'BTCUSDT', 'k': {'t': 1621565100000, 'T': 1621565399999, 's': 'BTCUSDT', 'i': '5m', 'f': 855298743, 'L': 855303322, 'o': '41240.01000000', 'c': '41205.84000000', 'h': '41373.48000000', 'l': '41176.63000000', 'v': '173.64903400', 'n': 4580, 'x': False, 'q': '7163749.40667776', 'V': '81.53978200', 'Q': '3363836.13903928', 'B': '0'}}
             
    
if __name__=='__main__':
    ws = WS_binance()
    ws.start()
    time.sleep(5)
    ws.suscribir('ASTBTC','5m')
    ws.suscribir('BTCUSDT','5m')
    ws.suscribir('WAVESUSDT','5m')
    ws.suscribir('BTCUSDT','15m')
    ws.suscribir('BTCUSDT','1h')

    for i in range(60):
        time.sleep(1)
        ##print(ws.ws.lock.locked(),ws.ws.readlock.locked())

    #print ('----------------------------------------------------------------------')    

    
    
    
    ws.renovar_conexion()
    
    
    
    
    for i in range(60):
        time.sleep(1)
        ##print(ws.ws.lock.locked(),ws.ws.readlock.locked())


    ws.desuscribir('ASTBTC','5m')
    ws.desuscribir('BTCUSDT','5m')
    ws.desuscribir('WAVESUSDT','5m')
    ws.desuscribir('BTCUSDT','15m')
    ws.desuscribir('BTCUSDT','1h')    

    for i in range(30):
        time.sleep(1)
        #print('=========------->',i)


    ws.activo = False
    ws.join()
    #print('fin')      
