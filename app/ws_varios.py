


from logger import Logger
import time
from velaset import VelaSet
from websocket import create_connection
from threading import Thread
import json
from mercado_actualizador_rest import Actualizador_rest
from variables_globales import Global_State
import traceback


class WS_stream(Thread):
    ''' web socket para suscribir informacion varia  <symbol>@forceOrder  '''

    
    def __init__(self,log,estado_general):
        Thread.__init__(self)
        self.subscripciones={}
        
        self.id = 1
        self.espera=1
        self.time_conexion=0
        self.time_ultima_recepcion=0
        self.activo = False
        
        self.g:Global_State = estado_general
        self.log=log
        
        self.buy=[]
        self.sell=[]
  
    def run(self):  
        try:
           self.ws = create_connection("wss://fstream.binance.com/ws")   #,enable_multithread=True
           self.activo = True
           self.time_conexion = time.time()
           while self.activo:
               result =  self.ws.recv()
               self.procesar_recibido(result)
               
               time.sleep(self.espera)
           self.ws.close    
        except Exception as e:
            print('Error,run()',str(e)) 
            tb = traceback.format_exc()
            print(tb)

    def detener(self):
        self.activo = False        

    def renovar_conexion(self):
        print('----------------renovar-------------conexion-----------')
        ws_nuevo = create_connection("wss://stream.binance.com:9443/ws")
        self.renovar_suscribir(ws_nuevo)
        time.sleep( 1 + len(self.subscripciones) )
        ws_viejo=self.ws
        self.ws=ws_nuevo
        ws_viejo.close()

    
    def renovar_suscribir(self,ws):
        for stream in self.subscripciones:
            suscribirse = {
                    "method": "SUBSCRIBE",
                    "params":
                        [
                        stream
                        ],
                        "id": self.subscripciones[stream]
                }
            self.__enviar(suscribirse,ws)
    
   


    def suscribir(self,stream):
        #self.crear_velaset(par,escala)  contenedor de datos
        if stream not in self.subscripciones:
            suscribirse = {
                "method": "SUBSCRIBE",
                "params":
                    [
                    stream
                    ],
                    "id": self.id
            }
            self.__enviar(suscribirse)
            self.subscripciones[stream]=self.id
            self.id  += 1
            #self.__ajustar_espera()
        else:
            print( stream,'ya estaba suscripto')    
    
    def desuscribir(self,stream):
        
        if stream  in self.subscripciones:
            desuscribirse = {
                "method": "UNSUBSCRIBE",
                "params":
                    [
                    stream
                    ],
                    "id": self.subscripciones[stream]
            }
            self.__enviar(desuscribirse) 
            del self.subscripciones[stream]
            #self.__ajustar_espera()   

        else: 
            print('no se puede desuscribir...')        

    def __ajustar_espera(self): 
        self.espera = 1.8 / (len (self.subscripciones) +1)   
    
    def __enviar(self,mensaje,ws=None):
        if ws is None:
            ws = self.ws
        try:
            
            ws.send( str(      json.dumps(mensaje)    )     )
        except Exception as e:
            print('Error al enviar:',e)

        #self.ws.lock.release()
        time.sleep(0.25)
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
    
    
    def procesar_recibido(self,result):
        #print('-->', result)
        try:
            if result:
                jresult=json.loads(result)
                #print(jresult)
                if jresult['o']['S']=='BUY':
                    self.agregar(self.buy, jresult['E']  )
                elif jresult['o']['S']=='SELL':
                    self.agregar(self.sell, jresult['E']  )
            
            self.imprimir_listas()
               

                #print(jresult["S"],jresult["o"],float(jresult["q"]) *  float(jresult["p"]),'q',jresult["q"],'p',jresult["p"],'ap',jresult["ap"] )
                #{"e":"forceOrder","E":1625030771364,"o":{"s":"BTCUSDT","S":"SELL","o":"LIMIT","f":"IOC","q":"0.029","p":"34603.03","ap":"34738.38","X":"FILLED","l":"0.023","z":"0.029","T":1625030771359}}
        except Exception as ex:
            print(str(ex))
            print('-->', result)
            pass
            
    def agregar(self,lista,str_even_time):
        event_time=int(str_even_time)/1000
        lista.append(event_time)
        

    def eliminar_viejos(self,lista):
        time_conservar = time.time()- 120 # 2 minutos
        while len(lista)>0 and lista[0] < time_conservar:
            lista.pop(0)

    def imprimir_listas(self):
        self.eliminar_viejos(self.buy)
        self.eliminar_viejos(self.sell)
        print('buy',len(self.buy),'sell',len(self.sell) )  

    


        # except Exception as e:
        #     print('Error en procesar_recibido:',str(e))  
        #     tb = traceback.format_exc()
        #     print(tb) 
        #     print(f'--->{result}<---')         
        # 
        # 
if __name__=='__main__':
    from acceso_db_conexion import Conexion_DB
    from acceso_db_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB
    from binance.client import Client
    from pws import Pws

    pws=Pws()
    client = Client(pws.api_key, pws.api_secret)
    log=Logger('Test_WS_stream.log')
    
    conn=Conexion_DB(log)                          
    fxdb=Acceso_DB_Funciones(log,conn.pool)        
    db = Acceso_DB(log,fxdb)   
    
    globales = Global_State()

    ws = WS_stream(log,globales)
    ws.start()
    while not ws.activo:
        time.sleep(1)

    #ws.suscribir('btcusdt@forceOrder')
    ws.suscribir('!forceOrder@arr')

