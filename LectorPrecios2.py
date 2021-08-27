# # -*- coding: UTF-8 -*-
import time
import sys

class LectorPrecios:
    pares=[[ 'BTCUSDT',[] ],[ 'BNBUSDT',[] ],[ 'BNBBTC',[] ] ]
    cantidad_de_muestras=50
    precios=''
    client=''
    operando=False
    actualizado=0

    def __init__(self, client): 
        self.client=client
        

    def leerprecios(self): 
        #print "leerprecios()"
        ahora=time.time()
        if self.operando or ahora - self.actualizado<21: #está operando o ha sido actualizado hace menos de 21 segundos
            return self.precios
        
        self.operando=True    

        intentar= True
        while intentar:
            try:
                self.precios = self.client.get_all_tickers()
                intentar= False
            except Exception as e:
                print ( e )
                print ( "Error en lectura de precios: reintento en 5s" )

            time.sleep(5)  

        self.operando=False

        return self.precios

    def tomar_precios_de_pares(self):
        for p in (self.pares):
            muestras=len(p[1])
            if muestras>self.cantidad_de_muestras: # elimino primer muestra para mantener una cantidad razonable
                p[1].pop(0)
            #print p[0]    
            p[1].append(self.tomar_precio(p[0])) # tomo el precio del par


    def tomar_precio(self,par):
        precio=-1    
        for px in (self.precios):
            if px['symbol']==par:
                precio=float(px['price'])
                break
        return precio

        

    def  valor_usdt(self, cantidad,par):

        pxpar=self.tomar_precio(par)
        if par.endswith('USDT'):
            px=1
        elif par.endswith('BTC'):
            px=self.tomar_precio('BTCUSDT')
        elif par.endswith('BNB'):    
            px=self.tomar_precio('BNBUSDT')
        elif par.endswith('ETH'):    
            px=self.tomar_precio('ETHUSDT')
 
        return cantidad*pxpar*px    

    def  valor_btc(self, cantidad,par):

        pxpar=self.tomar_precio(par)
        if par.endswith('BTC'):
            px=1
        elif par.endswith('USDT'):
            px=1/self.tomar_precio('BTCUSDT')
        elif par.endswith('BNB'):    
            px=self.tomar_precio('BNBBTC')
        elif par.endswith('ETH'):    
            px=self.tomar_precio('ETHBTC')

        return cantidad*pxpar*px    




    def usdt_cantidad(self,monto,par):
        pxunidad=self.valor_usdt(1,par)
        cant=self.redondear_unidades(monto/pxunidad)
        return cant 

    def unidades_posibles(self,cant_en_moneda_contra,par):
        pxpar=self.tomar_precio(par)
        unidades=self.redondear_unidades(cant_en_moneda_contra/pxpar)
        return unidades

    def redondear_unidades(self,unidades):
        cant=unidades
        if  0 < cant <1:
            cant=round(cant,4)
        elif 1 <= cant <9:
            cant=round(cant,2)
        else:
           cant=int(cant)
        return cant   

    
    # def imprimir_promedios(self):
    #     for p in (self.pares):
    #         print "Par:", p[0],"Promedio:",self.promedio(p[1])

    def promedio(self,muestras):
        suma=0
        for m in (muestras):
            suma+=m;
        return suma / len (muestras)        
        
