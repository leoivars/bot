# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member
import time


class Controlador_De_Tiempo:
    def __init__(self,intervalo): 
        self.inicio = time.time()
        self.intervalo = intervalo

    def tiempo_cumplido(self):
        ahora = time.time()
        ret = False
        if ahora - self.inicio >= self.intervalo:
            ret = True
            self.inicio = ahora
        return ret

    def reiniciar(self):
        self.inicio = time.time()

    def set_intervalo(self,intervalo):
        self.inicio = time.time()
        self.intervalo = intervalo
        

class Crontraldor_Calculo_Px_Compra(Controlador_De_Tiempo):
    intervalo_escala  ={'1m':30 ,'5m': 60 ,'15m':90,'30m':100,'1h':150,'2h':180,'4h':240,'1d':300,'1w':600,'1M':1200}
    def __init__(self,escala):
        intervalo=self.intervalo_escala[escala]
        super().__init__(intervalo)        





