from indicadores2 import Indicadores
from logger import Logger

class Rango():
    def __init__(self,ind:Indicadores,log:Logger,cvelas_rango=400):
        self.ind: Indicadores = ind
        self.log: Logger = log
        self.cvelas_rango = cvelas_rango
        self.escala_hora_actualizacion={}
        self.minimo=None
        self.maximo=None
        self.segundos_entre_actualizaciones = 600


    def __actualizar__(self,escala):
        try:
            ultima_actualizacion = self.escala_hora_actualizacion[escala]
        except:
            ultima_actualizacion = self.ind.ultima_vela_cerrada(escala).close_time/1000 - self.segundos_entre_actualizaciones -1 #le resto 1 para forzar actualizacion

        ahora = self.ind.ultima_vela_cerrada(escala).close_time/1000
        if  ahora - ultima_actualizacion > self.segundos_entre_actualizaciones:
            self.__actualizar_rango__(escala)
            self.escala_hora_actualizacion[escala] = ahora


    def __actualizar_rango__(self,escala):
        self.minimo,self.maximo = self.ind.minimo_maximo_por_rango_velas_imporantes(escala,self.cvelas_rango)
        self.log.log(f'__actualizar_rango__ minimo {self.minimo} maximo{self.maximo}')
    
    def min_max(self,escala):
        '''retorna el minimo y el maximo por velas importantes'''
        self.__actualizar__(escala)
        return self.minimo,self.maximo

    def posicion_precio(self,escala,precio):
        self.__actualizar__(escala)
        rango = self.maximo - self.minimo
        return  (precio - self.minimo) / rango



    
