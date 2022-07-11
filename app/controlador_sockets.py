

import time
from threading import Thread
from variables_globales import Global_State
import traceback
from mercado_actualizador_socket import Mercado_Actualizador_Socket


class Controlador_Socket(Thread):
    
    def __init__(self,log,sockets):
        Thread.__init__(self)
        self.sockets = sockets
        self.activo =True
        self.log = log
        
    def run(self):  
        try:
            while self.activo:
               for ws:Mercado_Actualizador_Socket in self.sockets:
                   
               
               time.sleep(5)

        except Exception as e:
            print('Error,run()',str(e)) 
            tb = traceback.format_exc()
            print(tb)

    