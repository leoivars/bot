# # -*- coding: UTF-8 -*-
import time



#de un maket profile debe indicar si ha habido un pump o no
#si hubo pump sugerir precios de compra por retroceso fibo
#si no hubo pump sugerir precio de compra de parte baja del perfil

class Analizador_Market_Profile:       

    def __init__(self, ind,propiedades_par): #ind...>indicadores previamente instanciado y funcionando
        self.ind=ind 
        self.propiedades_par=propiedades_par

        self.tiempo_actualizacion= 60
        self.ultima_actualizacion=time.time() - self.tiempo_actualizacion - 1
        self.precio=0
        
        self.temporalidades={'1h':50,'4h':200}
        

    def analizar_mktp(self,escala):
        #averiguar si ha habido un pump
        pass
    
    def precio_compra(self,inc_horas=24,tot_horas=720): #por defecto mira un mes cada 24 horas
        
        precio=self.ind.precio('1h')
        pocs = self.preparar_dic_pocs(inc_horas,tot_horas)
        
        #print ('------------------------')
        lista = sorted(pocs.keys())

        pcompra=0
        difp_min=100
        for p in lista:
            difp = -1
            if p != 0 and pocs[p][2] != 0:
                dif = round( (precio/p -1)*100,2)
                difp = round( dif / pocs[p][2],2)  #diferencia con peso   #revisar algun dia si pocs[p][2] no debería ser pocs[p][1]
            
            if difp > 0 and difp < difp_min:
                difp_min = difp
                pcompra = p
            
            #print (p,dif,difp ,pocs[p])
        #print ('------------------------')
        #print ('precio compra=',pcompra)
        #print ('------------------------')
        return pcompra
    
    def preparar_dic_pocs(self,inc_horas,tot_horas):
        
        pocs={}

        tiempo = inc_horas
        
        #recoleccion de datos
        while True:
            poc= self.ind.mp_slice(tiempo,self.propiedades_par.tickSize)

            if poc[1] not in pocs:
                pocs[ poc[1] ]=[ poc[0], poc[2], 1 ]
            else:
                pocs[ poc[1] ] [2] += 1 
          
                if pocs[ poc[1] ] [0] > poc[0]:
                    pocs[ poc[1] ] [0] = poc[0]
          
                if pocs[ poc[1]  ] [1] < poc[2]:
                    pocs[ poc[1] ] [1] = poc[2]
                
            if  tiempo > tot_horas: 
                 break
            
            tiempo += inc_horas

        return pocs    


  
    def precio_venta(self,inc_horas=24,tot_horas=720): #por defecto mira un mes cada 24 horas
        
        pocs = self.preparar_dic_pocs(inc_horas,tot_horas)
        lista = sorted(pocs.keys())
        
        #busco el que mas soporte tiene
        peso=0
        pventa=0
        for p in lista:
            if peso <  pocs[p][2] and pventa < pocs[p][1]:
                peso = pocs[p][2]
                pventa=pocs[p][1]
            
            print (peso,peso ,pocs[p])
        #print ('------------------------')
        #print ('precio compra=',pcompra)
        #print ('------------------------')
        return pventa

    def precio_tomar_perdidas(self,inc_horas=24,tot_horas=720): #por defecto mira un mes cada 24 horas
        
        pocs = self.preparar_dic_pocs(inc_horas,tot_horas)
        lista = sorted(pocs.keys(),reverse = True) #reverse = True
        
        #busco el que mas soporte tiene
        peso=0
        px=pocs[ lista[0] ] [0] # el mayor de todos
        dif_extremos=1
        dif_ex=0
        for p in lista:
            if pocs[p][1] >0:
                dif_ex =pocs[p][0]/pocs[p][1]
                if dif_extremos > dif_ex and   peso <  pocs[p][2]: #busco el menor con mas peso
                    peso = pocs[p][2]
                    px=pocs[p][0]
                    dif_extremos = dif_ex
            
            #print (peso,px, dif_ex,dif_extremos,pocs[p])
        #print ('------------------------')
        #print ('precio compra=',pcompra)
        #print ('------------------------')
        return px  


    def calcular_gi_gs_tp(self,precio_compra,inc_horas=24,tot_horas=720):
        ''' calcula gi (ganancia_infima) gs(ganancia_segura) y tp (tomar perdidas)
        en funciona de un precio de compra y teniendo en cuenta el market profile de 
        dos meses apra atras
        '''
        
        try:
            pgs=self.precio_venta(inc_horas,tot_horas)
        except Exception as e:
            print('precio_venta',str(e))
            pgs=0

        try:
            ptp=self.precio_tomar_perdidas(inc_horas,tot_horas * 2)
        except Exception as e:
            print('precio_tomar_perdidas',str(e))
            ptp=precio_compra+1    
            
        #correcciones en caso de malos calculos
        if pgs < precio_compra:
            pgs=precio_compra * 1.1
        if ptp > precio_compra or ptp==0:
            ptp= precio_compra  / 1.05
        gs=round( (1-precio_compra/pgs)*100,2)
        if gs < 3:
            gs =3.3 

        tp=round( (1-precio_compra/ptp)*100,2)
        variacion_tick=round(self.propiedades_par.tickSize/precio_compra*100,8)
        gi=round(1 + gs/5 + variacion_tick ,2)

        return {'gi':float(gi),'gs':float(gs),'tp':float(tp)} 

           