# # -*- coding: UTF-8 -*-
import time
class Moneda_Propiedades:       

    def __init__(self, moneda,client,log): #ind...>indicadores previamente instanciado y funcionando
        self.moneda=moneda
        self.client=client
        self.log=log
        

    def tomar_cantidad(self):
        parametro_asset=self.moneda
        #self.log.log( 'tomar cantidad',parametro_asset)
        ret=0
        while True:
            try:
                balance = self.client.get_asset_balance(asset=parametro_asset)
                ret=float(balance['free'])+float(balance['locked'])
                
            except Exception as e:
                ret=-1
                self.log.log( e )
                self.log.log('Error Moneda_Propiedades.tomar_cantidad, esperando 10 segundos.')
                time.sleep(10)
        return ret
    
    def tomar_cantidad_disponible(self):
        parametro_asset=self.moneda
        ret=0
        while True:
            try:
                balance = self.client.get_asset_balance(asset=parametro_asset)
                ret=float(balance['free'])
                break
            except Exception as e:
                self.log.log( e )
                self.log.log('Error Moneda_Propiedades.tomar_cantidad_disponible, esperando 10 segundos.')
                time.sleep(10)
        
       # print parametro_asset,balance,ret
        return ret  