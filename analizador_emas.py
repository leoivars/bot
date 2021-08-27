# # -*- coding: UTF-8 -*-
import time
from par_propiedades import *

class Analizador_Emas:       

    def __init__(self, ind): #ind...>indicadores previamente instanciado y funcionando
        self.ind=ind 
        
        
        self.listaemas=[]
        self.tiempo_actualizacion= 60
        self.ultima_actualizacion=time.time() - self.tiempo_actualizacion - 1
        self.precio=0
        
        self.temporalidades={'1h':50,'4h':200}

    def __del__(self):
        for l in self.listaemas:
            l = None
        
        for l in self.temporalidades:
            l = None

        del self.listaemas 

       

    def set_temporalidades(self,temporalidades):
        self.ultima_actualizacion=time.time() - self.tiempo_actualizacion - 1
        self.temporalidades=temporalidades

    def actulizar_listaemas(self):
        ahora=time.time()
        if ahora - self.ultima_actualizacion > self.tiempo_actualizacion:
            
            self.listaemas=self.ind.lista_emas(self.temporalidades)
            self.precio=self.ind.precio('1h')
            self.ultima_actualizacion=ahora
            return True
        else:
            return False    

    def soporte(self,posicion=1):
        self.actulizar_listaemas() 
        #busco primer soporte
        self.listaemas.sort(reverse = True)
        print (self.listaemas)
        soporte=self.precio
        pos=0
        for p in self.listaemas:
            if p<soporte: #hemos encontrado un soporte
                pos+=1
                if pos==posicion: 
                    soporte=p
                    break
        
        if pos != posicion: #no encontró fondo
            soporte=self.soporte_fibo(posicion) #entregoun soporte fibo por fibonachi

        if soporte==self.precio:
            soporte=self.ind.retroceso_fibo(self.precio,posicion)

        return soporte    

    def soporte_fibo(self,posicion=1):
        pivotes=self.ind.puntos_pivote_fibo('4h')
        soporte=self.precio
        pos=0
        for p in pivotes:
            if p<soporte: #hemos encontrado un soporte
                pos+=1
                if pos==posicion: 
                    soporte=p
                    break

        return soporte
   