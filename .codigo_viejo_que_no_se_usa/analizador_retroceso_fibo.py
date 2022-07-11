# # -*- coding: UTF-8 -*-
import time
from par_propiedades import *


#de un maket profile debe indicar si ha habido un pump o no
#si hubo pump sugerir precios de compra por retroceso fibo
#si no hubo pump sugerir precio de compra de parte baja del perfil

class Analizador_Retroceso_Fibonacci:       

    def __init__(self, ind, propiedades_par): #ind...>indicadores previamente instanciado y funcionando
        self.ind=ind 
        self.propiedades_par=propiedades_par

        self.tiempo_actualizacion= 60
        self.ultima_actualizacion=time.time() - self.tiempo_actualizacion - 1
        self.precio=0
        
        self.temporalidades={'1h':50,'4h':200}
        
    def retroceso(self,escala,sensibilidad=1,soporte=1):
        #averiguar si ha habido un pump
    
        fibo=[50, 61.8 ,76.8 , 100]
        lista_slices=self.ind.mp_slices_progresivos(escala,self.propiedades_par.tickSize)
        ultimo=len(lista_slices)-1
        p=0
        
        minimo=lista_slices[ultimo][0]
        maximo=lista_slices[ultimo][2]
        
        for i in range (ultimo-1,0,-1):
            p=p+1
            var_anterior=lista_slices[i+1][3] 
            var_actual  =lista_slices[i  ][3] 
            diff_var=abs(var_actual-var_anterior)
            
            print(p,diff_var,lista_slices[i][0],lista_slices[i+1][2],lista_slices[i+1][3],lista_slices[i][3],)
            if diff_var > sensibilidad:
                print('-------->',p)
                minimo=lista_slices[i][0]
                maximo=lista_slices[i+1][2]
                break
            

        return  maximo - (maximo-minimo) * fibo[soporte]  / 100     
                









