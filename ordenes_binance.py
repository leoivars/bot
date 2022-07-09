# # -*- coding: UTF-8 -*-
#from binance.enums import * #para  create_order
from binance.client import Client # Cliente python para acceso al exchangue
from binance.enums import *
from indicadores2 import Indicadores #Clase que toma datos de las velas del exchange y produce información (la version1 deprecated)
from logger import Logger #clase para loggear

#from termcolor import colored #para el libro de ordenes
import sys
import time
#from rsi0 import *
#import traceback
import json
from formateadores import format_valor_truncando
from cola_de_uso import Cola_de_uso, Promediador_de_tiempos

class OrdenesExchange:
        
    def __init__(self,client,par,log,estado_general): #ind...>indicadores previamente instanciado y funcionando
        self.client=client
        self.log=log
        self.cola = Cola_de_uso(log,estado_general)
        self.par = par

        self.ultima_orden=None
        self._stoplossActivo=False
        
        self.referencia='O_'+self.par

        self.cant_moneda_precision=None
        self.moneda_precision=None
        self.min_notional=None
        self.tickSize=None
        self.multiplierUp = 100
        self.prioridad = 2
        self.tomar_info_par()
        self.tiempos_exchange = Promediador_de_tiempos()
        

    def __del__(self):
        del self.client
        del self.log


    def __empezar(self,ref=''):
        
        self.cola.acceso_pedir(ref+self.referencia,self.prioridad) # todas las ordenes son prioritarias a las consultas
        self.cola.acceso_esperar_mi_turno()
        self.__inicio_ocupando_turno = time.time()
        
        
    def __terminar(self):
        #control de rendimiento
        demora=time.time() - self.__inicio_ocupando_turno
        self.cola.acceso_finalizar_turno(demora)
 
            
    def tomar_cantidad(self,parametro_asset):
        #self.log.log( 'tomar cantidad',parametro_asset)
        ret=0
        ejecutado=False
        while not ejecutado:
            self.__empezar('tomar_cantidad')
            try:
                balance = self.client.get_asset_balance(asset=parametro_asset)
                ret=float(balance['free'])+float(balance['locked'])
                ejecutado=True
            except Exception as e:
                ret=0
                txt_error = str(e)
                self.log.err('Error tomar_cantidad',parametro_asset,txt_error)
                
                #error de límite de uso alcanzado
                if 'APIError(code=-1003)' in txt_error:
                    time.sleep(60)

            self.__terminar()
        return ret
    
    def tomar_cantidad_disponible(self,parametro_asset):
        
        ret=0
        ejecutado=False
        while not ejecutado:
            self.__empezar('tomar_cantidad_disponible')
            try:
                balance = self.client.get_asset_balance(asset=parametro_asset)
                ret=float(balance['free'])
                ejecutado=True
            except Exception as e:
                self.log.err( e )
                self.log.err('Error tomar_cantidad_disponible, esperando 10 segundos.')
                time.sleep(10)
            self.__terminar()
        
        return ret  

    
    def tomar_info_par(self): 
        #obtengo info de la moneda y fijo los paramentro necesarios por ahora solo la presicion de la cantidad
        #esto sirve para que se pueda realizar cualquier tipo de orden usado lo que pide el exchange
        intentos=20
        ejecutado= False
        info = None
        while intentos>0 and not ejecutado:
            self.__empezar('tomar_info_par')
            try:
                info = self.client.get_symbol_info(self.par)
                #self.log.log(info)
                ejecutado= True
            except Exception as e:
                self.log.err( str(e),self.par, "Error de tomar_info_par")

            self.__terminar()    
            intentos-=1

        self.parse_info_par(info) 

    def parse_info_par(self,info):

        for f in (info['filters']):
            if f['filterType']=='LOT_SIZE':
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

            if  f['filterType']=='PERCENT_PRICE':
                self.multiplierUp=float(f['multiplierUp']) # maximo valor al que se puede poner una orde de venta
                

    def info_par(self):
        return {'cant_moneda_precision':self.cant_moneda_precision,\
                'moneda_precision':self.moneda_precision,\
                'tickSize':self.tickSize,\
                'min_notional':self.min_notional,\
                'multiplierUp':self.multiplierUp}           
     
    
    def consulta_ordenes_activas(self):
        
        intentos=3
        ejecutado= False
        while intentos>0 and not ejecutado:
            self.__empezar('consulta_ordenes_activas')
            try:
                #eliminar cualquier orden activa del par 
                ordenes = self.client.get_open_orders(symbol=self.par)
                ejecutado = True

            except Exception as e:
                ordenes=[]
                err=str(e)
                self.log.log( err )
                self.log.err( "Error get_open_orders()",self.par)
                if 'APIError(code=-2011)' in err:
                    self.__terminar()    
                    break
            self.__terminar()
            intentos-=1    
        return ordenes
    
    def cancelar_todas_las_ordenes_activas(self):
        
        intentos=20
        ejecutado= False
        while intentos>0 and not ejecutado:
            self.__empezar('cancelar_todas_las_ordenes_activas')
            try:
                #eliminar cualquier orden activa del par 
                ordenes = self.client.get_open_orders(symbol=self.par)

                #self.log.log('------> lista de ordenes activas',ordenes)
                if len(ordenes)==0: # no hay mas ordenes activas
                    ejecutado = True

            except Exception as e:
                err=str(e)
                self.log.log( err )
                self.log.err( "Error get_open_orders()",self.par)
                if 'APIError(code=-2011)' in err:
                    self.__terminar()    
                    break

            self.__terminar()    
            intentos-=1 
        
            try:
                if len(ordenes)>0:
                    for orden in (ordenes):
                        #self.log.log(orden)
                        self.log.log( "Cancelando-->",orden['orderId'])
                        self.cancelar_orden(orden['orderId'])
            except Exception as e: 
                err=str(e)
                self.log.log( err )       

        return ejecutado

    def cancelar_orden(self,orderId):
        #self.log.log("Cancelar Orden: ", orderId )
        intentos=20
        ejecutado= False
        orden_resultado={'orderId':0}
        while intentos>0 and not ejecutado:
            self.__empezar('cancelar_orden')
            try:
                #self.log.log( "Cancelar",orderId)
                orden_resultado = self.client.cancel_order(symbol=self.par,orderId=orderId)
                #self.log.log('ORDEN_CANCELADA',orden_resultado)
                #self.log.log( "Orden Cancelada: ",result['orderId']  )
                #self.cant_moneda=self.tomar_cantidad(self.moneda) # esto lo saqué porque no tiene nada que ver tomar la cantidad de moneda disponible despues de cancelar una orden.
                ejecutado= True
                #self.log.log( "Cancelar resultado",result) #result es una orden, el estado que quedó.
            except Exception as e:
                err=str(e)
                orden_resultado={'orderId':0} #orden nula
                self.log.log( err )
            self.__terminar() 
            time.sleep(1)   
            intentos-=1  
        
        if ejecutado:
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)   

        return orden_resultado    

    def crear_stoploss(self,cantidad,precio):
        ret='ERROR'

        sprecio   =format_valor_truncando(precio , self.moneda_precision)
        stopPrice =format_valor_truncando(precio + self.tickSize   ,self.moneda_precision)

        squantity=format_valor_truncando(cantidad,self.cant_moneda_precision)
        
        self.log.log('creando stoploss cant,',squantity,'precio',sprecio,'stopPrice',stopPrice)

        intentos=3
        
        abortar= False
        ejecutado = False
        orden_resultado={ 'orderId' : 0}
        while intentos>0 and not ejecutado:
            self.__empezar('crear_stoploss')
            try:
                orden_resultado = self.client.create_order(
                symbol=self.par,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC, #Good Till Cancelled
                quantity=squantity,
                stopPrice=stopPrice,
                price=sprecio  )
                self.log.log( "crear_stoploss orderId:", orden_resultado['orderId'] )
                ret='OK'
                ejecutado=True
            except Exception as e:
                txte=str(e)
                orden_resultado={'orderId':0} #orden nula
                abortar = False
                self.log.log( "Error crear_stoploss",self.par,cantidad,precio,txte )
                if 'PERCENT_PRICE' in txte:
                    ret='PERCENT_PRICE'
                    abortar = True
                if 'iwould trigger immediately' in txte: 
                    ret='STOP_SOBRE_PRECIO'
                    abortar = True    
                if 'insufficient balance' in txte: 
                    ret='SIN_FONDOS'
                    abortar = True    
                else:
                    abortar= True
            
            self.__terminar()                          
            
            if abortar:
                orden_resultado={'orderId':0}#orden nula    
                break  
            
            intentos-=1

        if ret=='OK': # duerme un ratito para evitar consultar rápido el estado y caer en un error
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)

        return ret,orden_resultado   


    def crear_orden_compra_limit(self,cantidad,precio):
        ret='ERROR'

        sprecio=format_valor_truncando(precio,self.moneda_precision)
        squantity=format_valor_truncando(cantidad,self.cant_moneda_precision)

        intentos=2
        ejecutado= False
        while intentos>0 and not ejecutado:
            self.__empezar('crear_orden_compra_limit')
            try:
                orden_resultado = self.client.order_limit_buy(
                    symbol=self.par,
                    quantity=squantity,
                    price=sprecio)
                if orden_resultado['orderId']>0: 
                    ejecutado=True 
                    ret='OK'
            except Exception as e:
                orden_resultado={'orderId':0}#orden nula 
                ret =   str(e)
                self.log.err( ret )
                self.log.err( "Error crear_orden_compra_limit ",self.par,cantidad,precio )

            self.__terminar()    
            intentos-=1

        if ret=='OK': # duerme un ratito para evitar consultar rápido el estado y caer en un error
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)    
        
        return ret, orden_resultado 


    def crear_orden_venta_limit(self,cantidad,precio):
        ret='ERROR'

        sprecio=format_valor_truncando(precio,self.moneda_precision)
        squantity=format_valor_truncando(cantidad,self.cant_moneda_precision)

        self.log.log(  "crear_orden_venta_limit:",squantity,sprecio )
        intentos=3
        ejecutado= False
        abortar=False
        while intentos>0 and  not ejecutado:
            self.__empezar('crear_orden_venta_limit')            
            try:
                
                orden_resultado = self.client.order_limit_sell(
                    symbol=self.par,
                    quantity=squantity,
                    price=sprecio)
                if orden_resultado['orderId']>0: #cadena vacia
                    #self.log.log( "crear_orden_venta_limit:", orden_resultado )
                    ejecutado=True 
                    ret='OK'
            
            except Exception as e:
                abortar = False
                orden_resultado={'orderId':0} #orden nula
                self.log.log( "Error crear_orden_venta_limit ",self.par,sprecio,squantity,str(e),orden_resultado )
                if 'PERCENT_PRICE' in str(e):
                    ret=str(e)
                    abortar = True
                elif 'APIError(code=-1013)' in str(e): # mercado cerrado
                    ret=str(e)
                    abortar = True
                else: 
                    self.log.log( "reintento",intentos)
                
            self.__terminar()                          
            
            if abortar:
                break

            intentos-=1
            #self.log.log('self.ultima_orden:',self.ultima_orden)
        if ret=='OK': # duerme un ratito para evitar consultar rápido el estado y caer en un error
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)
        return ret, orden_resultado  

    #order = client.order_market_buy(   ##### todavía no implementada la orden de compra market
    #    symbol='BNBBTC',
    #    quantity=100)


    def crear_orden_venta_market(self,cantidad):
        ret='ERROR'

        squantity=format_valor_truncando(cantidad,self.cant_moneda_precision)

        self.log.log(  "crear_orden_venta_market:",squantity )
        intentos=3
        ejecutado= False
        abortar=False
        while intentos>0 and  not ejecutado:
            self.__empezar('crear_orden_venta_market')            
            try:
                orden_resultado = self.client.order_market_sell(
                    symbol=self.par,
                    quantity=squantity)
                                        
                if orden_resultado['orderId']>0: #cadena vacia
                    ejecutado=True 
                    ret='OK'
            
            except Exception as e:
                abortar = False
                orden_resultado={'orderId':0} #orden nula
                self.log.log( "Error crear_orden_venta_market ",self.par,squantity,str(e),orden_resultado )
                
                if 'APIError(code=-1013)' in str(e): # mercado cerrado
                    ret=str(e)
                    abortar = True
                else: 
                    self.log.log( "reintento",intentos)
                
            self.__terminar()                          
            
            if abortar:
                break

            intentos-=1
            #self.log.log('self.ultima_orden:',self.ultima_orden)
        if ret=='OK': # duerme un ratito para evitar consultar rápido el estado y caer en un error
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)
        
        return ret, orden_resultado  


    def crear_orden_compra_market(self,cantidad):
        ret='ERROR'

        squantity=format_valor_truncando(cantidad,self.cant_moneda_precision)

        self.log.log(  "crear_orden_compra_market:",squantity )
        intentos=3
        ejecutado= False
        abortar=False
        while intentos>0 and  not ejecutado:
            self.__empezar('crear_orden_compra_market')            
            try:
                orden_resultado = self.client.order_market_buy(
                    symbol=self.par,
                    quantity=squantity)
                                        
                if orden_resultado['orderId']>0: #cadena vacia
                    ejecutado=True 
                    ret='OK'
            
            except Exception as e:
                abortar = False
                orden_resultado={'orderId':0} #orden nula
                self.log.log( "Error crear_orden_compra_market ",self.par,squantity,str(e),orden_resultado )
                
                if 'APIError(code=-1013)' in str(e): # mercado cerrado
                    ret=str(e)
                    abortar = True
                else: 
                    self.log.log( "reintento",intentos)
                
            self.__terminar()                          
            
            if abortar:
                break

            intentos-=1
            #self.log.log('self.ultima_orden:',self.ultima_orden)
        if ret=='OK': # duerme un ratito para evitar consultar rápido el estado y caer en un error
            ret = self.consultar_estado_hasta_que_aparezca(orden_resultado)
            
        return ret, orden_resultado    

    def consultar_estado_hasta_que_aparezca(self,orden):
        '''
        Cuando se crea una orden, esta no aparece inmediatamente para consulta,
        Esta rutinta se encarga de esperar hasta que apareza y no se produzcan errores por consultarla 
        demasiado pronto.
        '''

        ret = 'ERROR'

        if 'orderId' in orden:
            if orden['orderId'] == 0:
                return ret

        orderId = orden['orderId']
        intentos=5
        xtiempo=1
        time.sleep( self.cola.tiempo_espera_total_estimado() )
        ti = time.time()
        if orderId != 0:
            while intentos>0:
                orden_resultado = self.consultar_estado_orden(orden)
                intentos -= 1
                if orderId == orden_resultado['orderId']:
                    ret = 'OK'
                    break
                tiempo_espera = self.cola.tiempo_espera_total_estimado() + xtiempo 
                self.log.log( 'esperando para consultar..',tiempo_espera )
                time.sleep( tiempo_espera )
                xtiempo += 1

        tf =  time.time() - ti       
        self.tiempos_exchange.agregar_tiempo( tf ) 

        return ret

        #self.log.log('tiempo aparicion-->',tf,'tiempo promedio-->',self.tiempos_exchange.demora_promedio)


    def consultar_estado_orden(self, orden):

        if orden['orderId'] ==0: # no preguntemos boludeces..
            orden['estado']='NO_EXISTE'
            orden['precio']=0
            orden['ejecutado']=0
            return orden

        exito= False
        estado_orden='NO_SE_PUDO_CONSULTAR'
        precio=0
        ejecutado=0
        orderId = orden['orderId']
        intentos=0
        order={}
        texchange = self.tiempos_exchange.demora_promedio

        while intentos < 10 and  not exito:
            err=False
            self.__empezar('consultar_estado_orden')
            try:
                order = self.client.get_order(symbol=self.par,orderId=orderId)
                estado_orden=str(order['status'])
                
                ejecutado=float(order['executedQty'])
                
                #precio
                if order['type']== 'MARKET': # la ordek market no lleva precio, lo calculo a precio promedio asi:
                    tot=float(order['cummulativeQuoteQty'])
                    precio= tot / ejecutado
                else: #sino saco el dato de la orden
                    precio=float(order['price'])
                exito=True

                #self.log.log(  "consultar_estado_orden=", estado_orden,'ejecutado',ejecutado )
            except Exception as e:
                se = str(e)
                self.log.err( 'ERROR,consultar_estado_orden', se ,orderId )
                err=True
                order={'orderId':0} #orden nula
                if 'APIError(code=-2013)' in se:
                    estado_orden='NO_EXISTE'
            
            intentos += 1   
            self.__terminar() 
            if err:
                #self.log.err(  "Error en consultar_estado_orden(): reintento en ", str(int(t))  ," segundos" )
                res_ordenes = self.consultar_ordenes(self.par,10)
                if self.buscar_orden(res_ordenes,orderId):
                    self.log.log(self.par,orderId,'está!')
                else:    
                    t = texchange  + self.cola.tiempo_espera_total_estimado()
                    time.sleep( t )

        
        order['estado']=estado_orden
        order['precio']=precio
        order['ejecutado']=ejecutado

        return order
    
    def consultar_ordenes(self, par,plimit=500):
        exito= False
        intentos = 1
        while intentos>0 and  not exito:
            self.__empezar('consultar_ordenes')
            try:
                ordenes = self.client.get_all_orders(symbol=par,limit=plimit)
                exito=True
            except Exception as e:
                ordenes =[]
                self.log.err( 'ERROR,consultar_ordenes', str(e) )
                self.log.err(  "Error en consultar_estado_orden():, reintento en 15 seg." )

            intentos -= 1   
            self.__terminar() 

        return ordenes    

    def buscar_orden(self,ordenes,order_id):
        encontrado = False
        for o in ordenes:
            if o['orderId'] == order_id:
                encontrado = True
                break
        return encontrado


