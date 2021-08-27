# # -*- coding: UTF-8 -*-
from binance.enums import * #para  create_order
class Par:
    client=''
    empCount = 0
    ultima_orden=''
    moneda_contra='' #moneda contra la que se tradea
    moneda='' #moneda que se tiene
    moneda_precision=8 #cantidad de digitos para calcular precios dela moneda
    
    
    par=''
    precio=0
    
    cant_moneda=0 #cantidad de moneda existente
    cant_moneda_stoploss=0 #cantidad de moneda que se proteje con el stoploss
    cant_moneda_precision=8 #es la presiscion que acepta el exchange en las ordenes
    _sumaprecios=0 # para calcular precio promedio
    _cantprecios=0 # para calcular precio promedio
    _stoplossActual=0
   # _stoplossActual_string=''
    fee=0 #lo que cobra el exchange por cada operacion
    pstoploss=0 #porcentaje para calcular stoploss
    
    estado=0# 0 solo mirar , 1 protejer con stoploss
    


    

    def __init__(self, client,fee,pstoploss,moneda,moneda_contra): # este método se llama cuando se inicia una clase
        self.client=client
        self._fee=fee
        self.pstoploss=pstoploss
        self.moneda=moneda
        self.moneda_contra=moneda_contra
        self.par=moneda+moneda_contra

        #obtengo info de la moneda y fijo los paramentro necesario por ahora solo la presicion de la cantidad
        info = client.get_symbol_info(self.par)
        for f in (info['filters']):
            if f['filterType']=='LOT_SIZE':
               self.cant_moneda_precision=int((f['stepSize']).find('1'))-1
               if self.cant_moneda_precision==-1: self.cant_moneda_precision=0
               print 'stepSize',f['stepSize'],self.cant_moneda_precision

            if f['filterType']=='PRICE_FILTER':
                self.moneda_precision=int((f['tickSize']).find('1'))-1
                if self.moneda_precision==-1: self.moneda_precision=0
                print 'tickSize',f['tickSize'], self.moneda_precision
    


    #en agunas ocasiones se busca protejer menos cantidad del total
    # como en el caso de BNB que se deja algo para que las comisiones 
    # salgan mas baratas    
    def set_cant_moneda_stoploss(self,cantidad): 
            self.cant_moneda_stoploss=cantidad

    #retorna la cantidad de moneda válida para una orden de stoploss
    #redondeada a los digitos que pide binance
    def get_cant_moneda_stoploss(self):
        if self.cant_moneda_stoploss <= self.cant_moneda:
            return self.cant_moneda_stoploss
        else:
            return self.cant_moneda

    def tomar_precio(self,precios):
        precio=-1    
        for px in (precios):
            if px['symbol']==self.par:
                self.precio=float(px['price'])
                break
        #datos para el precio promedio        
        self._sumaprecios+=self.precio
        self._cantprecios+=1

    def precio_promedio(self):
        return  self._sumaprecios/self._cantprecios    
    
    def calcular_stoploss(self):
        st=self.precio_promedio()/(1+self.pstoploss/100)
        return round(st,self.moneda_precision)
    
    def ajustar_stoploss(self,nuevo_stoploss):
        if self._stoplossActual != nuevo_stoploss: #actualizo el stoploss
            self._stoplossActual=nuevo_stoploss
            self.realizar_stoploss()
            
    def realizar_stoploss(self):
        #eliminar cualquier orden activa del par 
        ordenes = self.client.get_open_orders(symbol=self.par)
        for orden in (ordenes):
            self.cancelar_orden(orden['orderId'])
        #se crea orden de stoploss
        self.crear_stoploss(self.get_cant_moneda_stoploss(),self._stoplossActual)
            
    def tomar_cantidad(self,parametro_asset):
        balance = self.client.get_asset_balance(asset=parametro_asset)
        ret=float(balance['free'])
        #print "Cantidad:",parametro_asset, ret
        return ret 

    def format_valor_truncando(self,valor,digitos_decimales):
        if digitos_decimales>0:
            svalor='{0:.8f}'.format(valor)
            punto=svalor.find('.')
            dec=len(svalor[ punto+1:])
            if dec>digitos_decimales: dec=digitos_decimales
            return svalor[0:punto+1+dec]+"0"*(digitos_decimales-dec)
        else:
            return str(int(valor))

    def crear_stoploss(self,cantidad,precio):

        #print "precision moneda:", self.moneda_precision
        #print "precision cant:", self.cant_moneda_precision

        #print "Orden Stoploss cantidad:",cantidad," precio:", cantidad

        sprecio=self.format_valor_truncando(precio,self.moneda_precision)
        squantity=self.format_valor_truncando(cantidad,self.cant_moneda_precision)

        
        print "Orden Stoploss cantidad:",squantity," precio:", sprecio
       
        self.ultima_orden = self.client.create_order(
            symbol=self.par,
            side=SIDE_SELL,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC, #Good Till Cancelled
            quantity=squantity,
            stopPrice=sprecio,
            price=sprecio  )
        print "crear_stoploss orderId:", self.ultima_orden['orderId']

    def cancelar_ultima_orden(self):
        #previo a cancelar hay que ver si no se ha ejecutado 
        #porque podría haberse disparado ante una baja        
        self.cancelar_orden(self.ultima_orden['orderId'])
        #print "cancelar_ultima_orden_stop_loss orderId: ",result['orderId']
        
    def cancelar_orden(self,orderId):
        result = self.client.cancel_order(
            symbol=self.par,
            orderId=orderId)
        self.cant_moneda=self.tomar_cantidad(self.moneda)
        print "Cancelar Orden  orderId: ",result['orderId']
        
    def crear_orden_compra_limit(self,cantidad,precio):
        self.ultima_orden = self.client.order_limit_buy(
            symbol=self.par,
            quantity="{0:.8f}".format(cantidad),
            price="{0:.8f}".format(precio))
        print "crear_orden_compra_limit:", (self.ultima_orden)        
        
    #se supone que un precio está bajando
    #y calcula a cuanto tendría que bajar
    # asegurando una ganancia
    #basánsose en el precio actual
    def precio_de_recompra_minimo(self,pganancia):
        coef=(1+self._fee)/(1-self._fee)
        ret=self.precio/coef/(1+pganancia/100)
        return ret
    
    def mostrar_estado(self):    
        print self.par,'Estado:',self.estado, '{0:.8f}'.format(self.precio), \
        '{0:.8f}'.format(self.precio_promedio()),'{0:.9f}'.format(self._stoplossActual)      
    
    def accion(self): 
        self.mostrar_estado()
        if self.estado==0:    
            self.estado_0_accion()
        elif self.estado==1:
            self.estado_1_accion()       
            
    def estado_0_inicio(self):
        self.estado=0  
    def estado_0_accion(self):
        self.mostrar_estado()
    
    def estado_1_inicio(self):
        self.estado=1
        #1) el precio se ha cargado con bucle que gobierna al objeto
        # la cantidad da protejer o cantidad actual 
        self.cant_moneda=self.tomar_cantidad(self.moneda)
                
        #calculo el stoploss y pongo la orden
        self.ajustar_stoploss(self.calcular_stoploss())

    def estado_1_accion(self):
        
        if self.precio<=self._stoplossActual:
            print self.par," tocó stoploss ",self._stoplossActual," go estado 0"
            self.estado_0_inicio()
            #lo ideal sería pasar a estado 2 que sería recomprar moneda, por 
            #ahora solo se observa
        else:
            nuevo_stoploss=self.calcular_stoploss()    
            if nuevo_stoploss >self._stoplossActual:
               print 'nuevo_stoploss!' 
               self.ajustar_stoploss(nuevo_stoploss)
 
       
