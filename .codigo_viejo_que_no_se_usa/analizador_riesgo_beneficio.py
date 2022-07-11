# # -*- coding: UTF-8 -*-
import time
from par_propiedades import *

class Analizador_Riesgo_Beneficio:       

    def __init__(self, ind,propiedades_par): #ind...>indicadores previamente instanciado y funcionando
        self.ind=ind 
        self.propiedades_par=propiedades_par
        self.listapocs=[]
        self.listaemas=[]
        self.tiempo_actualizacion= 150
        self.ultima_actualizacion=self.__forzar_actualizacion()
        self.precio=0
        self.poc=1 # 0---> mp_slice.value_area[0]     1---> mp_slice.poc_price   --->2 mp_slice.value_area[1])
        #self.temporalidades=['1m','5m','15m','1h','2h','4h']
        self.tiempos=[8,16,24,48,80,160]
        self.riesgo_beneficio=0
    
    def __forzar_actualizacion(self):
        return time.time() - self.tiempo_actualizacion - 10

    def set_poc(self,poc):
        if poc!=self.poc:
            self.ultima_actualizacion=self.__forzar_actualizacion()
            self.poc=poc

    def set_tiempos(self,tiempos):
        self.ultima_actualizacion=self.__forzar_actualizacion()
        self.tiempos=tiempos

    def actulizar_listapocs(self):
        ahora=time.time()
        if ahora - self.ultima_actualizacion > self.tiempo_actualizacion:
            #print('utilizo poc',self.poc)
            self.listapocs=self.ind.lista_pocs(self.tiempos,self.poc,self.propiedades_par.tickSize)
            self.precio=self.ind.precio('1h')
            self.ultima_actualizacion=ahora
            return True
        else:
            return False    

    def soporte(self,posicion=1,px_inicial=0):
        self.actulizar_listapocs() #actualiza porque tambien la llamo para hacer compras eslcalping
        #busco primer soporte
        self.listapocs.sort(reverse = True)
        #print (self.listapocs)
        if px_inicial==0: # con esto tengo la oportunidad de entregar un precio inicial, para explorar la posibilidad de buscar soporte partiendo de precios iniciales mas bajos
            px_inicial=self.precio
        soporte=px_inicial
        pos=0
        #print('soporte',soporte,self.listapocs)
        for p in self.listapocs:
            #print('p,soporte',p,soporte)
            if p<soporte: #hemos encontrado un soporte
                pos+=1
                if pos==posicion: 
                    soporte=p
                    break
        
        if pos != posicion or soporte==px_inicial: #no encontró fondo
            soporte=self.ind.retroceso_fibo_mm('1h',50, posicion)
            print('#######--->no encontré soporte',soporte,pos)
            if soporte >= px_inicial:
                soporte=self.soporte_fibo(posicion+1) #entregoun soporte fibo por fibonachi

        #if soporte==self.precio:
        #    soporte=self.ind.retroceso_fibo_mm('1h',50, posicion)
            #soporte=self.ind.retroceso_fibo(self.precio,posicion)

 
    
        return soporte    

    def soporte_fibo(self,posicion=1):
        pivotes=self.ind.puntos_pivote_fibo('4h')
        soporte=self.precio
        pos=0
        for p in pivotes:
            print ('p,soporte',p,soporte)
            if p < soporte: #hemos encontrado un soporte
                soporte=p
                pos+=1
                if pos==posicion: 
                    break

        return soporte
        


        

    def primer_resistencia(self):
        self.set_poc(1)
        self.actulizar_listapocs() #actualiza porque tambien la puedo llamar
        #busco la primer resistencia
        resistencia=self.precio
        for p in self.listapocs:
            if p>resistencia: #hemos encontrado la resistencia
                resistencia=p
                break
        return  resistencia   

    def primer_resistencia_porcentaje(self):
        r=self.primer_resistencia()
        return round((1-self.precio/r) * 100  ,2)    

    def relacion_riesgo_beneficio(self,px=0):
        
        self.set_poc(1)# hago los cálculos con poc
        self.actulizar_listapocs()
        
        if px==0:
            px=self.precio

        soporte=self.soporte(1)
        if soporte==px: #no encontró soporte
            soporte-=self.ind.atr('30m',1)

        soporte-=-self.propiedades_par.tickSize - self.ind.atr('15m',1)

        self.tomar_perdidas=round(((1-px/soporte)*100),2) 

        resistencia=self.primer_resistencia()
        if resistencia==px: #no encontró resistencia
            self.ganancia_segura=2
        else:  #hay una resistencia
            self.ganancia_segura=round((1-px/resistencia)*100,2) 

        if self.ganancia_segura<2: # menos d 2% en ganancia segura es demasiado poco
            self.ganancia_segura=2


        self.ganancia_infima=self.ganancia_segura/2

        if self.tomar_perdidas < -7: #no encontró soporte o el soporte es demasiado bajo
            baja_estimada=px - self.ind.atr('4h',1)  - self.propiedades_par.tickSize
            self.tomar_perdidas=round((1-px/baja_estimada)*100,2)

        if self.tomar_perdidas > -2:    
        #else: # al soporte encontrado le agregamos  el atr de 4h para dar posibilidad a que se mueva el precio.
            atr=self.ind.atr('4h',1)  + self.propiedades_par.tickSize
            print('atr',atr)
            adision_al_soporte_encontrado=round((atr/px)*100,2) * 2
            #print('adision_al_soporte_encontrado',adision_al_soporte_encontrado)
            #print('tomar_perdidas',self.tomar_perdidas)
            self.tomar_perdidas-=adision_al_soporte_encontrado
               
        self.riesgo_beneficio_natural=round(abs(self.ganancia_segura/self.tomar_perdidas),2)
        self.riesgo_beneficio        =round(abs(self.ganancia_infima/self.tomar_perdidas),2)

        self.ganancia_infima=float(self.ganancia_infima)
        self.ganancia_segura=float(self.ganancia_segura)
        self.tomar_perdidas=float(self.tomar_perdidas)
        self.riesgo_beneficio=float(self.riesgo_beneficio)
        self.riesgo_beneficio_natural=float(self.riesgo_beneficio_natural)  
    
        


        print (self.ganancia_infima,self.ganancia_segura,self.tomar_perdidas,self.riesgo_beneficio,self.riesgo_beneficio_natural )       

    
