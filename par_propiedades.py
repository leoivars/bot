# # -*- coding: UTF-8 -*-
import time
class Par_Propiedades:       

    def __init__(self, par,client,log): #ind...>indicadores previamente instanciado y funcionando
        self.cant_moneda_precision=0
        self.tickSize=0
        self.min_notional=0
        self.client=client
        self.log=log
        self.par=par
        self.moneda_precision=0
        
        self.tomar_info_par()

    def __del__(self):    
        del self.cant_moneda_precision
        del self.tickSize
        del self.min_notional
        del self.client
        del self.log
        del self.par
        del self.moneda_precision

    def tomar_info_par(self): 
        #obtengo info de la moneda y fijo los paramentro necesarios por ahora solo la presicion de la cantidad
        #esto sirve para que se pueda realizar cualquier tipo de orden usado lo que pide el exchange
        
        intentos=20
        ejecutado= False
        while intentos>0 and not ejecutado:
            try:
                
                info = self.client.get_symbol_info(self.par)
                #print(info)
                for f in (info['filters']):
                    if f['filterType']=='LOT_SIZE':
                       #print('stepSizef',f['stepSize'])
                       self.cant_moneda_precision=int((f['stepSize']).find('1'))-1
                       if self.cant_moneda_precision==-1: self.cant_moneda_precision=0
                       #self.log.log(  'stepSize',f['stepSize'],self.cant_moneda_precision )

                    if f['filterType']=='PRICE_FILTER':

                        self.moneda_precision=int((f['tickSize']).find('1'))-1
                        if self.moneda_precision==-1: self.moneda_precision=0
                        #self.log.log(  'tickSize',f['tickSize'], self.moneda_precision )
                        self.tickSize=float(f['tickSize'])# este valor parece ser la minima unidad aceptada de incremento/decremento

                    if  f['filterType']=='MIN_NOTIONAL':
                        self.min_notional=float(f['minNotional']) # es el valor minimo que debe tener una orden en moneda_contra
                        

                ejecutado= True
            except Exception as e:
                self.log.log( e,self.par, "Error de tomar_info_par, reintento en 15 seg.")
                time.sleep(15)
            intentos-=1    
        return ejecutado          