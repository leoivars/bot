# # -*- coding: UTF-8 -*-
import time
from indicadores2 import Indicadores


#de un maket profile debe indicar si ha habido un pump o no
#si hubo pump sugerir precios de compra por retroceso fibo
#si no hubo pump sugerir precio de compra de parte baja del perfil

class Analizador_Altos_Bajos:       

    def __init__(self, ind,propiedades_par): #ind...>indicadores previamente instanciado y funcionando
        self.ind: Indicadores = ind
        self.propiedades_par=propiedades_par
    

    
    def calcular_gi_gs_tp(self,precio_compra,escala='1d'):
        ''' calcula gi (ganancia_infima) gs(ganancia_segura) y tp (tomar perdidas)
        en funciona de un precio de compra y teniendo en cuenta los promedios de altos y bajos
        '''
                
        
        gs, ptp_gs = self.calcular_ganancia_perdidas_ptomar_perdidas(precio_compra,escala,90)
        gi, ptp_gi = self.calcular_ganancia_perdidas_ptomar_perdidas(precio_compra,escala,7)

        
        pgi = round(float( (1 - precio_compra / gi) * 100 ),2)  #calculo desde el precio hacia arriba
        pgs = round(float( (1 - precio_compra / gs) * 100 ),2)  #calculo desde el precio hacia arriba
        

        if pgi<0:
           pgi = 2

        if pgs < pgi:
           pgs = round( pgi * 1.5,2)    




        riesgo_beneficio_gi=round(abs(pgi/ptp_gi),2)
        riesgo_beneficio_gs=round(abs(pgs/ptp_gs),2)
    
        return {'gi':pgi,'gs':pgs,'tp_gi':ptp_gi,'tp_gs':ptp_gs,'rb_gi':riesgo_beneficio_gi,'rb_gs':riesgo_beneficio_gs}     


    def calcular_ganancia_perdidas_ptomar_perdidas(self,precio_compra,escala,dias):
        tp  = self.ind.promedio_de_bajos(escala,int(dias/10),dias) #60 dias
        ptp = round(float( (tp / precio_compra -1 ) * 100 ),2)  #calculo desde el precio hacia abajo   
        
        while ptp >0: # si es positivo itero hasta encontrar un negativo, no puede ser positivo
            dias = dias + 20
            tp  = self.ind.promedio_de_bajos(escala,int(dias/10),dias) #60 dias
            ptp = round(float( (tp / precio_compra -1 ) * 100 ),2)  #calculo desde el precio hacia abajo
            if dias > 160: #maxima cantidad de dias almacenados
                break
        if ptp >0: #si da positivo quiere decir que el precio está por dabjo del promedio de bajos calculado, o sea no tenemos piso, estamo en el vacío mismo 
            ptp = ptp * -5 # fijo un ptp negativ
        
        if ptp==0:
            ptp = 0.00000001

        gs = self.ind.promedio_de_altos(escala,int(dias/10)+1,dias) 

        

        return gs, ptp    

       