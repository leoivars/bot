from indicadores2 import Indicadores
from logger import Logger

class Volume_Profile():
    def __init__(self,ind:Indicadores,log:Logger,cvelas_vp=250):
        self.ind: Indicadores = ind
        self.log: Logger = log
        self.cvelas_vp = cvelas_vp
        self.escala_hora_actualizacion={}
        self.vp_min=None
        self.vp_med=None
        self.vp_max=None
        self.segundos_entre_actualizaciones = 600


    def __actualizar__(self,escala):
        try:
            ultima_actualizacion = self.escala_hora_actualizacion[escala]
        except:
            ultima_actualizacion = self.ind.ultima_vela_cerrada(escala).close_time/1000 - self.segundos_entre_actualizaciones -1 #le resto 1 para forzar actualizacion

        ahora = self.ind.ultima_vela_cerrada(escala).close_time/1000
        if  ahora - ultima_actualizacion > self.segundos_entre_actualizaciones:
            self.__actualizar_vp__(escala)
            self.escala_hora_actualizacion[escala] = ahora


    def __actualizar_vp__(self,escala):
        self.vp_min,self.vp_med,self.vp_max = self.ind.vp_min_med_max(escala,self.cvelas_vp)
        self.log.log(f'__actualizar_vp__ min {self.vp_min}, med {self.vp_med},max {self.vp_max} ')
    
    def min_med_max(self,escala):
        '''retorna el minimo la media y el maximo de volumen mas importante'''
        self.__actualizar__(escala)
        return self.vp_min,self.vp_med,self.vp_max




    
