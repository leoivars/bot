# # -*- coding: UTF-8 -*-
import time



#de un maket profile debe indicar si ha habido un pump o no
#si hubo pump sugerir precios de compra por retroceso fibo
#si no hubo pump sugerir precio de compra de parte baja del perfil

class Analizador_MinMax:       

    def __init__(self, ind,propiedades_par): #ind...>indicadores previamente instanciado y funcionando
        self.ind=ind 
        self.propiedades_par=propiedades_par
    

    
    def calcular_gi_gs_tp(self,precio_compra,escala,periodos):
        ''' calcula gi (ganancia_infima) gs(ganancia_segura) y tp (tomar perdidas)
        en funciona de un precio de compra y teniendo en cuenta el market profile de 
        dos meses apra atras
        '''
        fibos=[21.4,38.2,50,61.8,76.4,100,161.8,261.8,423.6]
        mm= self.ind.minmax(escala,periodos)

        #print ('mm',mm)
        
        gs = 0  #max
        for fib in fibos:
            gs=mm[0] * ( 1 + fib /100)
            variacion = ( 1 - precio_compra / gs) * 100 
            #print (variacion)
            if variacion > 7:
                break

        if variacion < 7:
            gs = precio_compra * 1.07

        gi = precio_compra + (gs - precio_compra) * 0.214

        tp = mm[0]
        if tp * 1.0764 > precio_compra:
            tp = precio_compra / 1.0764

        pgi = round(float( (1 - precio_compra / gi) * 100 ),2)
        pgs = round(float( (1 - precio_compra / gs) * 100 ),2) 
        ptp = round(float( (1 - precio_compra / tp) * 100 ),2)   

        return {'gi':pgi,'gs':pgs,'tp':ptp}     


    def _deprecated_calcular_gi_gs_tp(self,precio_compra,escala,periodos):
        ''' calcula gi (ganancia_infima) gs(ganancia_segura) y tp (tomar perdidas)
        en funciona de un precio de compra y teniendo en cuenta el market profile de 
        dos meses apra atras
        '''
        #fibo=[76.4,61.8,50,38.2,21.4,0]
        mm= self.ind.minmax(escala,periodos)

        print ('mm',mm)
        
        gs = mm[1]  #max
        if mm[3] > -7 :    # precio_compra: # llego a ganar ni un 7%
            gs = precio_compra * 1.07

        gi = precio_compra + (gs - precio_compra) * 0.214

        tp = mm[0]
        if tp * 1.0764 > precio_compra:
            tp = precio_compra / 1.0764

        pgi = round(float( (1 - precio_compra / gi) * 100 ),2)
        pgs = round(float( (1 - precio_compra / gs) * 100 ),2) 
        ptp = round(float( (1 - precio_compra / tp) * 100 ),2)   

        return {'gi':pgi,'gs':pgs,'tp':ptp} 

       