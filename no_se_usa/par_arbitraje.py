# # -*- coding: UTF-8 -*-
#from binance.enums import * #para  create_order
from binance.client import Client # Cliente python para acceso al exchangue
from logger import Logger #clase para loggear
from correo import Correo
from datetime import datetime, timedelta
from ordenes_binance import OrdenesExchange

from funciones_utiles import memoria_consumida,cpu_utilizada,calc_tiempo_segundos,strtime_a_fecha,strtime_a_time,variacion,variacion_absoluta
from controlador_de_tiempo import *
from no_se_usa.par_arbitraje import  Global_State
from pool_indicadores import Pool_Indicadores
from error_recuperable import Error_recuperable
import random
import sys
import time
#from rsi0 import *
import traceback

class Par_arbitraje:
    #variables de clase
    client=''
    correo=None 

    def __init__(self, client,moneda,moneda_contra, obj_global,cantidad,porcentaje_compra,porcentaje_pventa):
        #variables de instancia
 
        self.g: Global_State = obj_global
        
        self.estoy_vivo=True # Se usa para detectar cuando la instancia no tiene nada mas que hacer, se elimina de la memoria.
        self.ultima_orden={'orderId':0}
        self.moneda_contra = None
        self.moneda = None
        self.moneda_precision=8 #cantidad de digitos para calcular precios dela moneda

        self.porcentaje_compra = porcentaje_compra
        self.porcentaje_pventa = porcentaje_pventa

        self.precio=0
        self.precio_compra=0
        self.precio_salir_derecho=0
        self.precio_objetivo=0

        self.cantidad_abitraje = cantidad


        self.cant_moneda=0 #cantidad de moneda existente
        self.cant_moneda_compra=0 #cantidad de moneda que se pretende comprar
       
        self.cant_moneda_precision=8 #es la presiscion que acepta el exchange en las ordenes
        self.tickSize=0.00000001 #el minimo incremento/decremento que acepta el exchange
        self.tickSize_proteccion=0 # un minimo incremento calculado en funcion de self.tickSize y de precio actual. La idea es que cuando se produce una variacion muy grande tieda a cero
        self.min_notional=0 # es el valor minimo que debe tener una orden (total de compra o venta) en moneda_contra (varia de para par y se fija en tomar_info_par())
                            # 3/10/2018 encontré un caso en que tomar_info_par() brinda datos erroneos: min_notional que al cumplirlo da error
                            # entonces agrego un campo en min_notional la tabla pares. Si pares.min_notional==0 uso lo obtenido en tomar_info_par()
                            # redondeando pares.min_notional>0 manda sobre tomar_info_par()
        self.min_notional_compra=0 # min notional para comprar
        
        self.estado=-1
        self.estado_anterior=0
       
        self.cant_moneda_venta=0# se calcula a media que se vaya vendiendo.
        self.precio_venta=0# para realizar venta
       
        self.log='' #objeto de log que se crean en init

        #comienzo de __init__
        self.client=client
        self.moneda=moneda #moneda que se quiere comprar o vender
        self.moneda_contra=moneda_contra #moneda contra la que se quiere operar 
        self.par=moneda+moneda_contra

        self.log=Logger(self.par.lower()+'.log') #objeto para loguear la salida de esta clase a un archivo específico como es multihilo por separado
        self.log.loguear=True #False-->solo loguea log.err 

        
        self.errr = Error_recuperable(self.log,3600)

        self.tiempo_reposo=600 

        self.trabajando=True

        # reset es una mandera que obliga al par
        # a recargar todos sus parametros y comenzar otra vez
        self.reset=False

        self.oe = OrdenesExchange(self.client,self.par,self.log,obj_global)
        
        

    def set_log_level(self,log_level):
        self.log.set_log_level(log_level)

    def cargar_parametros_iniales(self):
        self.oe.tomar_cantidad(self.moneda)
        self.set_estado(-1)

    
    def set_estado(self,pestado_nuevo):
        
        if pestado_nuevo == -1:
            estado_nuevo = 21 # comprar en arbitraje
        else:
            estado_nuevo = pestado_nuevo    

        self.estado_anterior=self.estado
        
        self.estado_bucles=0


    def iniciar(self):
        self.iniciar_estado(21)

        


    def iniciar_estado(self,pestado):
       
        if pestado>=0:
            self.set_estado(pestado)
        #se quiere cambiar al mismo estado en el que estaba, haría un bucle infinito entonce reiniciamos la funcion.
        elif pestado==self.estado and pestado==self.estado_anterior:
            pestado==21
        else: #un parámetro negativo hace que el estado se quede en el mismo lugar si ejecutar set_estado que memoriza el estado anterior, esto es para quedarse en el mismo estado recordando cual era el estado anteror
            pestado=self.estado

        self.log.log('iniciando estado',pestado)
        #para asegurarnos que no quede nada abierto
        self.cancelar_todas_las_ordenes_activas()

        # variables que deben ser reiniciadas en todo estado
        self.tiempo_reposo=0 # anulamos todo reposo porque estamos cambiando de estado
        self.ultima_orden={'orderId':0}
        self.fecha_trade=datetime.now().replace(microsecond=0) #una fecha de incio de estado para todos pero luego otros otros estados como el 3 la pueden corregir con los datos previamente guardados
        
        estado_reconocido=True
        self.log.log('---> Iniciando Estado =',pestado)

        if pestado==31:
            self.estado_31_inicio()
        elif pestado==21:
            self.estado_21_inicio()            
        else:
            estado_reconocido=False

        if estado_reconocido:
            self.estado_anterior = pestado    

        return estado_reconocido    


    def estado_siguiente(self):
        ret = 0
        if self.estado == 21:
            return 31
        else:    
            return 21
        
        
    def ganancias(self):
        ''' ganancia representada en porcentaje '''
        comision=self.precio_compra*self.g.fee
        comision+=self.precio*self.g.fee
        
        gan= self.precio - self.precio_compra - comision 
        if self.precio!=0:
            return round(gan/self.precio*100,2)
        else:
            return -0.000000001    
    
    def calculo_ganancias(self,pxcompra,pxventa):  #esta es la funcion definitiva a la que se tienen que remitir el resto.
        comision=pxcompra*self.g.fee
        comision+=pxventa*self.g.fee
        gan=pxventa - pxcompra - comision #- self.tickSize
        return round(gan/pxcompra*100,3)          

    def ganancia_total(self,cant=1):
        ''' ganancia representana en moneda contra '''
        comision=self.precio_compra*cant*self.g.fee
        comision+=self.precio*cant*self.g.fee
        
        gan= self.precio * cant - self.precio_compra * cant - comision 
        
        return gan

    def calculo_precio_de_venta(self,ganancias):
        comision=self.precio_compra*self.g.fee
        vta= self.precio_compra * (1+ganancias/100)
        comision+=self.precio*self.g.fee
        return vta + comision




    #retorna el precio al que hay que vender para obtener pganancia       
    def calc_precio(self,pganancia):
        return ( -self.precio_compra - self.precio_compra*self.g.fee) / ( pganancia/100 -1 + self.g.fee)


    def tomar_info_par(self): 
        #obtengo info de la moneda y fijo los paramentro necesarios por ahora solo la presicion de la cantidad
        #esto sirve para que se pueda realizar cualquier tipo de orden usado lo que pide el exchange
                
        info = self.oe.info_par()
        
        self.cant_moneda_precision = info['cant_moneda_precision']
        self.moneda_precision      = info['moneda_precision']
        self.tickSize              = info['tickSize']
        self.min_notional          = info['min_notional']
        self.multiplierUp          = info['multiplierUp']

        

        return ( info !=None )    

    
    def set_cantidad_moneda_compra(self,cantidad):
        self.log.log('cantidad_moneda_compra=',cantidad)
        self.cant_moneda_compra=cantidad

    def set_precio_venta(self,px):
        self.precio_venta=px
    
    def operacion_empezar(self):
        self.operando=True

    def operacion_terminar(self):
        self.operando=False    
    

    def format_valor_truncando(self,valor,digitos_decimales):
        if digitos_decimales>0:
            svalor='{0:.9f}'.format(valor)
            punto=svalor.find('.')
            dec=len(svalor[ punto+1:])
            if dec>digitos_decimales: dec=digitos_decimales
            return svalor[0:punto+1+dec]+"0"*(digitos_decimales-dec)
        else:
            return str(int(valor))

    def autoformat(self,valor):
        if  1 > valor > -1:
            return   self.format_valor_truncando(valor,8)
        else:
            return   self.format_valor_truncando(valor,2)    
    
    def cancelar_ultima_orden(self):
        #previo a cancelar hay que ver si no se ha ejecutado 
        #porque podría haberse disparado ante una baja 

        exito=False
        if self.ultima_orden['orderId']>0:       
            orden = self.oe.cancelar_orden(self.ultima_orden['orderId']) # Si fracasa el cancelar hago esfuerzo por cancelar todo
            exito = self.procesar_orden_cancelada(orden)

            if exito:
                self.ultima_orden={'orderId':0}#orden nula
            else:
                pass     
                
                #self.detener()

        return exito # verdadero si hubo exito en cancelar
    
    
    
    #ORDEN_CANCELADA {'symbol': 'BTCUSDT', 'origClientOrderId': 'EtpVAvJ3wxW8cwajR1g2Us', 'orderId': 3146436734, 
    # 'orderListId': -1, 'clientOrderId': 'lA2QuZZbPdSkqtbtRzN7FP', 'price': '11758.58000000', 
    # 'origQty': '0.00190100', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'CANCELED', 
    # 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'SELL'}

    def procesar_orden_cancelada(self,orden):
        exito=False
        if orden['orderId'] !=0: # no es la orden nula
            if orden['status'] =='CANCELED':
                if float(orden['executedQty'])==0:
                    self.log.log(orden['orderId'],'Cancelada OK' )
                    exito = True
                else:
                    self.log.log(orden['orderId'],'Parcialmente Ejecutada' )
                    self.enviar_correo_error('Cancelar Orden')
                    
            else:
                self.log.log(orden['orderId'],'Se mandó a Cancelar pero no se Canceló' )
                self.enviar_correo_error('Cancelar Orden')
        
        return exito 

    


    def crear_orden_compra(self,cantidad,precio):
        
        ret,self.ultima_orden = self.oe.crear_orden_compra_limit(cantidad,precio)    
        
        self.precio_actual_en_orden_compra=0
        if ret=='OK':
            self.precio_actual_en_orden_compra=precio
        elif 'MIN_NOTIONAL' in ret:
            ret = 'MIN_NOTIONAL'
            self.log.log( "Error crear_orden_compra_limit: MIN_NOTIONAL",self.min_notional )
            self.enviar_correo_error('MIN_NOTIONAL')
            self.iniciar_estado( self.estado_anterior )
        
        elif 'code=-2010' in ret:
            ret = 'BALANCE'
            self.log.log( "Error crear_orden_compra_limit: SIN BALANCE SUFICIENTE",self.min_notional )
            self.iniciar_estado( self.estado_anterior )

        return ret    


    def crear_orden_venta_limit(self,cantidad,precio):
        ret,self.ultima_orden = self.oe.crear_orden_venta_limit(cantidad,precio)
        return ret                

    
    
    def mostrar_estado(self):    
        self.log.log(  self.par,'Estado:',self.estado    )

    def detener(self):
        self.reset = True
        self.trabajando = False
        self.tiempo_reposo = 0
        
        if self.log.tiempo_desde_ultima_actualizacion() > 1800:
            self.estoy_vivo=False

    
    #esta es la función le de vida al hilo
    #es invocada por el creado en auto_compra_vende.py
    # la secuencia es:
    # instanciacion del par, eso ejecuta __init__
    # y luego trabajar()....

    def trabajar(self):
        
        #set inicial de valores_que_cambian_poco
        ct_recalculo_valores_que_cambian_poco = Controlador_De_Tiempo(3600)
    
        self.reset=True
        self.trabajando=True

        while self.trabajando and self.g.trabajando: 

            while not self.g.se_puede_operar: #variable de estado general es de lectura y se establece en el bucle principial, True cuando se puede operar, Falce no se puede operar
                print('No se Puede Operar, esperando')
                time.sleep(1)

            self.log.log('*** TRABAJO ***',self.par)    

            if self.reset:
                self.log.log(self.par,"(*) RESET (*)" ) 
                self.cancelar_todas_las_ordenes_activas()
                self.reset=False
                self.cargar_parametros_iniales()
                self.recalculo_valores_que_cambian_poco()
                
                self.iniciar() #ejecuta el inicio del estado o primer estado de la funcion ('comprar','vender' etc)

            else:    #este es el flujo normal del bucle
                
                self.accion()
                #self.actualizar_estadisticas()
                self.reposar()

            # recalculos periódicos
            if ct_recalculo_valores_que_cambian_poco.tiempo_cumplido():
                self.recalculo_valores_que_cambian_poco()

            self.log.log('--fin--ultima-linea-trabajando--')    
                    

        self.log.log(self.par,"--->finalizando...")
        self.cancelar_todas_las_ordenes_activas()
        
        self.log.log(self.par,"--->FIN.")
        ##del self.log  no elimnar el log
        self.estoy_vivo=False
    
    
    def cancelar_todas_las_ordenes_activas(self):
        self.oe.cancelar_todas_las_ordenes_activas()
        self.ultima_orden={'orderId':0}#orden nula


    def recalculo_valores_que_cambian_poco(self):
        self.tomar_info_par() #informacion que el exchage suministra sobre el par y muy necesaria para la creación de ordenes.
    
    

    

    

    

    def reposar(self):
        self.log.log('reposar')
        if self.tiempo_reposo == 0:
            #self.log.log(self.par,'reposo == 0',self.estado)
            return


        try:
            tiempo=int(self.tiempo_reposo)


            #randomizo el tiempo para no dormir a intervalos regulares nunca
            tiempo= 20 + random.randint(0, tiempo)


            self.log.log(self.par,"         Reposando:",tiempo)
            
            self.soniar_que_btc_sube(tiempo)
            
        except Exception as e:
            self.log.err( "Error en reposar():",self.tiempo_reposo,e )  
            self.soniar_que_btc_sube(297) 


    
          


    #hace tiempo que puede ser interrumpido si se produce un reset
    def soniar_que_btc_sube(self,segundos):
        salida_nomal = True
    
        fin = segundos
        t=0
        
        self.seguir_soniando = True
        contador_prueba_de_vida = 0
        while t < fin and not self.reset and self.seguir_soniando and self.g.trabajando:
            time.sleep(1)
            t += 1
            contador_prueba_de_vida += 1
            if contador_prueba_de_vida > 300:
                contador_prueba_de_vida = 0
                self.log.log(self.par," sigo reposando:",t)

        return salida_nomal

    
    def accion(self): 
        
        self.log.log("****** accion() ****** estado",self.estado)

        try:
            self.estado_bucles+=1 #cuanta los bucles o ciclos que hace que está en esta estado

            if self.estado==21:    
                self.estado_21_accion() 
            elif self.estado==31:    
                self.estado_31_accion()#espera fondos para comprar    

        except Exception as e:
            self.log.err( "*!*!___err_en_accion__*!*!*Error en accion:",self.estado,e )
            tb = traceback.format_exc()
            self.log.err( tb)
            

    def retardo_dinamico(self,segundos):
        #retardo para no matar tanto al procesador
        cpu=cpu_utilizada()
        if  cpu > 50:
            tiempo = segundos * cpu/100
            self.log.log( "RRR Retardo dinámico",tiempo )
            time.sleep( tiempo )             

         
    def set_tiempo_reposo(self):
        self.tiempo_reposo = 600
           

    def orden_llena_o_parcilamente_llena_estado_21(self,can_comprada,precio_orden,txt_filled,orden):
        
       
        
        #se compró, hay que pasar al estado de esperar a que suba 
        self.log.log('enviar_correo_filled_compra...')
        self.enviar_correo_filled_compra(txt_filled)
        self.iniciar_estado( self.estado_siguiente() )






    def calcular_fecha_futura(self,minutos_al_futuro):
        ahora = datetime.now()
        fecha_futura = ahora + timedelta(minutes = minutos_al_futuro)
        return  fecha_futura     



#212121212121212121212121


    def estado_21_inicio(self): #comprar
        
        self.estado_21_detenerse = False
       
        self.set_tiempo_reposo()

        self.precio_actual_en_orden_compra=0

        self.log.log( "Estado 21 Compra Arbitraje - Inicio" ,self.par )
        
        self.tiempo_inicio_estado=time.time()
        
        #defino cuanto voy a comprar
        self.calcular_cantidad_a_comprar21()
        if self.cant_moneda_compra * self.precio_compra < self.min_notional: 
            self.log.log('self.cant_moneda_compra * self.precio_compra < self.min_notional',self.cant_moneda_compra,self.precio,self.min_notional)
            #no hay guita, reiniciamos funcion
            self.iniciar_estado( 21 )
            
            return

        ret=self.crear_orden_compra(self.cant_moneda_compra,self.precio_compra)
        
        if ret!='OK':
            self.iniciar_estado( 21 )
            
            return

        self.precio_venta=0
    
    def estado_21_accion(self):  #comprar
        
        #ind=self.ind_pool.indicador(self.par)  
         
        self.retardo_dinamico(1)
        self.set_tiempo_reposo()
        ahora = time.time()
        tiempo_en_estado = int(ahora - self.tiempo_inicio_estado)
        
        self.log.log(  "________E.21 Comprando Arbitraja" ,self.par, "Tiempo",tiempo_en_estado)

        orden=self.oe.consultar_estado_orden(self.ultima_orden)
        precio_orden=orden['precio']
        estado_orden=orden['estado']
        can_comprada=orden['ejecutado']

        if estado_orden in 'NO_SE_PUDO_CONSULTAR UNKNOWN_ORDER NO_EXISTE':
            self.enviar_correo_error('Error al consultar Orden')
            
            self.detener()
            return
        
        elif estado_orden=='FILLED':
            self.log.log(  "Estado FILLED:" )
            self.precio_compra=precio_orden
            self.cant_moneda_compra=can_comprada
            self.orden_llena_o_parcilamente_llena_estado_21(can_comprada,precio_orden,'FI',orden) #FI por Filled 
            return 

        if estado_orden=='NEW': 
            self.log.log(  "NEW seguimos esperando..." )
    
        elif estado_orden=='PARTIALLY_FILLED': 
            self.log.log(  "PARTIALLY_FILLED seguimos esperando..." )
        




#212121212121212121212121         

#3131313131##############
    def estado_31_inicio(self): #vender a precio fijo arbitraje
       
        self.retardo_dinamico(1)
        self.tiempo_inicio_estado =  time.time()

        #ibtc=self.ind["BTCUSDT"]
        self.log.log(  "____E31__ Vender a Pxfijo - INICIO",self.par )
        
        self.cant_moneda_venta = self.establecer_cantidad_a_vender31(self.cantidad_abitraje) #aca se fija idtrade y precio de compra tambien...
        self.precio_venta = 1 * (1 + self.porcentaje_pventa / 100)


        if self.cant_moneda_venta <= 0:
            err='self.cant_moneda_venta <= 0, no podemos vender eso...'
            self.log.log(err)
            self.enviar_correo_error(err)
            self.detener()
            return
                
        if self.precio_venta * self.cant_moneda_venta < self.min_notional:
            err='self.precio_venta * self.cant_moneda_venta < self.min_notional <= 0, no podemos vender eso...'
            self.log.log(err)
            self.enviar_correo_error(err)
            self.detener()
            return

        if not self.estado_31_orden_vender('estado_31_inicio'):
            self.detener()
            return
                

    # ESTADO 31 - Accion #
    
    def estado_31_accion(self):
        
        
        self.retardo_dinamico(10)
        tiempo_en_estado = int (time.time() - self.tiempo_inicio_estado)
        self.set_tiempo_reposo()
  
        self.log.log(  "___E.31 Esp.Ven. Ti:",tiempo_en_estado,self.par )
        
        #consulto el estado de la orden de venta
        # para tomar las desiciones que sean pertinentes 
        orden=self.oe.consultar_estado_orden(self.ultima_orden)
        self.log.log( self.par,"estado_31_accion...decisiones" )
        #self.log.log( self.par,"estado_precio",estado_precio )

        #Si no se pudo consultar, todo mal, estamos perdidos: sincronizamos 
        if orden['estado'] in 'NO_SE_PUDO_CONSULTAR UNKNOWN_ORDER NO_EXISTE':
            self.enviar_correo_error('Error al consultar Orden')
            self.detener()
            return
        
        #Orden Cancelada: en el caso de stoploss si el precio de la orden está por encima del precio actual
        #la orden se cancela. Otro caso podria ser que fue cancelada manualmente.
        if  orden['estado']=='CANCELED':
            self.log.log(  "CANCELED posiblemente el precio bajó y dejó al intento de stop mal parado" )
            self.detener()
            return
        
        #NEW la orden está puesta y no ha sido ejecutada 
        elif orden['estado']=='NEW':
            self.log.log(  "NEW, seguimos esperando..." )
      
        #FILLED:  orden ejecutanda completamente
        #registramos la venta y cambiamos de estado
        elif orden['estado']=='FILLED':
            self.log.log(  "FILLED, se vendió o tocó el stoploss" )
            
            self.precio_venta=orden['precio']

            #agrega al trade la cantidad vendida (ejecutada) que en este caso es el total.
            self.cant_moneda_compra=orden['ejecutado']
            #self.log.log()

            self.enviar_correo_filled_estado()
            
            self.iniciar_estado( self.estado_siguiente() )
            return #FILLED

        #PARTIALLY_FILLED: esperamos una cierta cantidad de bucles (hay que modificarlo a una cierta cantidad de tiempo) para que se llene
        # si no se llena en ese tiempo, cancelo orden y persisto lo ejecutado
        # necesito mejor programacion para las ordenes parcialmente cumplidas pero  
        # como son casos minimos lo dejo para el futuro
        elif orden['estado']=='PARTIALLY_FILLED': 
            self.log.log(  "PARTIALLY_FILLED seguimos esperando..." )
            return  #PARTIALLY_FILLED

        self.log.log("FIN E3. Acciones")

#31313131##############
            
    
        

    # previene que el exchangue de el error de min_notional
    def monto_moneda_contra_es_suficiente_para_min_motional(self,cantidad,precio_vta):   
        valor=cantidad * precio_vta
        if valor < self.min_notional:
            self.log.err( "Min Notional ",self.min_notional," y ",valor, self.moneda_contra)
            return False
        else:
            return True    
   

    def estado_31_orden_vender(self,motivo_venta):         
        ret=False
        self.log.log(  "E31.Vender:", self.cant_moneda_venta, "precio_objetivo :",self.precio_venta )
        
        resultado=self.crear_orden_venta_limit(self.cant_moneda_venta,self.precio_venta) ## aca hay que ver bien cual es la cantidad de moneda que se vende, por ahora self.cant_moneda_compra que sería la misma cantidad que compré
        if resultado =='OK': # hay algo que no podemos manejar
            self.log.log("estado_31_orden_vender OK:")
            ret=True
        else:
            self.enviar_correo_error(motivo_venta + ' no se pudo crear orden de venta, dormimos 10 dias')
            self.detener()
            self.log.err("estado_31_orden_vender error:",motivo_venta,resultado)
        
        return ret  


    def precio_ejecutado(self,orden):
        ejecutado = float(orden['executedQty'])
        if orden['type'] == 'MARKET': # la ordek market no lleva precio, lo calculo a precio promedio asi:
            tot=float(orden['cummulativeQuoteQty'])
            precio= tot / ejecutado
        else: #sino saco el dato de la orden
            precio=float(orden['price'])  

        return precio,ejecutado  


    
    def calcular_cantidad_a_comprar21(self):
         
        self.precio_compra=1 /1.03

        
        #self.log.log('parametro_cantidad=',self.format_valor_truncando(self.parametro_cantidad,self.cant_moneda_precision) )   

        if self.parametro_cantidad>0:
            cant_en_moneda_contra=Par.lector_precios.convertir(self.parametro_cantidad,'USDT',self.moneda_contra)   
            cantidad_a_comprar=Par.lector_precios.unidades_posibles(cant_en_moneda_contra,self.par)
        else:
            cantidad_a_comprar=0   

        #el resultado de unidades_posibles puede ser cero tambien por eso tengo que preguntar nuevamente por valor cero.
        # y si es cero, establezco a lo mínimo indispensable.
        if cantidad_a_comprar==0:
            #minimo=self.redondear_unidades(self.min_notional*1.01/self.precio)
            if self.x_min_notional>1:
                coeficiente=1
            else:
                coeficiente=1.09    
            cantidad_a_comprar=self.redondear_unidades(self.min_notional_compra*coeficiente/self.precio_compra) # establezco una cantidad a comprar en el minimo positble + un poco mas (coeficiente) para el caso que x_min_notional =
            self.log.log('cantidad_a_comprar==0, establezco=',cantidad_a_comprar,'min_notional_compra,coeficiente',self.min_notional_compra,coeficiente)   
        
        if cantidad_a_comprar<1 and self.cant_moneda_precision==0: #es una moneda que no se puede fraccionar 
            cantidad_a_comprar=1 #establezco a 1 que es lo mínimo que se puee comprar

        self.log.log('calcular_cantidad_a_comprar',cantidad_a_comprar)

        


        return cantidad_a_comprar
    
    
    def fmt(self,valor):
        return self.format_valor_truncando( valor , 8)
    

    def establecer_cantidad_a_vender31(self,cantidad):
        cantidad_en_exchange=self.oe.tomar_cantidad(self.moneda)  ## probablemente hay que cambiar esta funcion por tomar_cantidad_disponible() pero no estoy seguro ... razonar cuendo esté siguiendo este tema.
        
        if cantidad_en_exchange >= cantidad:
            return cantidad
        else:
            return cantidad_en_exchange

    
    
    def redondear_unidades(self,unidades):
        cant=unidades
        if  0 < cant <1:
            cant=round(cant,4)
        elif 1 <= cant <9:
            cant=round(cant,2)
        else:
           cant=int(cant)
        return cant 

    #por ahora cambié los enviar_correo por un encolar mensaje puesto que no está funcionado y con 
    #el tema de lso hilos necesito un statcktrace que no dispongo de momento.

    # def enviar_correo_filled_estado_3(self):
    #     gan=str(self.ganancias_contra_stoploss())
    #     texto='Se sale de estado 3: \n'
    #     texto+="Precio Compra: " + self.format_valor_truncando( self.precio_compra,8) + '\n'
    #     texto+="Precio  Venta: " + self.format_valor_truncando( self.stoploss_actual,8) + gan+ '\n'
    #     self.log.log(texto) 
    #     db=self.get_conexion_db()
    #     db.persistir_ganancias(gan,self.moneda,self.moneda_contra)
    #     # self.correo.enviar_correo(self.par+' '+gan,texto)
    #     return

    def enviar_correo_error(self,txt_error):
        
        titulo=self.par + ' ERROR estado ' +str(self.estado)  
        texto=titulo+'\n'+txt_error
        
        
        self.log.log(texto)
        
        texto+= self.log.tail()
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)
        return



    def enviar_correo_filled_estado(self):
        gan=self.calculo_ganancias(self.precio_compra,self.precio_venta)
        sgan=str(gan)
        ganusdt=self.format_valor_truncando(self.calculo_ganancias_usdt(self.precio_compra,self.precio_venta,self.cant_moneda_compra),8)
        gan_moneda_contra=self.format_valor_truncando(self.calculo_ganancias_moneda_contra(self.precio_compra,self.precio_venta,self.cant_moneda_compra),8)

        titulo=self.par+' [Estado '+ str(self.estado)+'] '+sgan+ ' %'
        texto=titulo+'\n'
        texto+=" Precio Compra: " + self.format_valor_truncando( self.precio_compra,8) + '\n'
        texto+=" Precio  Venta: " + self.format_valor_truncando( self.precio_venta,8) +" "+ sgan+ ' %  '+gan_moneda_contra +' m$c ' +ganusdt +' usdt\n'

        self.log.log(texto)
        self.log_resultados.log(texto)

        #2/9/2019 no persisto mas esto se deduce de los trades
        #persistir en la base.       
        #cant=self.tomar_cantidad(self.moneda) 
        

        #cálculo y retroalimientacion de shitcoin
        self.retroalimentacion_shitcoin(gan)

        texto+= self.log.tail()
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)
        return


    def enviar_correo_filled_compra(self,txt_filled):
       

        
        titulo=self.par+ ' Ent.' + txt_filled + ' ' +self.analisis_provocador_entrada+'_'+self.calculo_precio_compra
        texto=titulo+'\n'
          

        #texto+=self.texto_analisis_moneda() #esto etaba matando el envío del mail que rápidamente se tiene que poner a vender
        
        self.log.log(texto)
        texto+=self.log.tail()        
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)

        
        return


    def enviar_correo_generico(self,ptitulo):
       
        titulo=ptitulo +'-'+ self.par 
        texto=titulo+'\n'

        
        self.log.log(texto)
        texto+=self.log.tail()        
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)

        
        return    


    def enviar_correo_senial(self):

        if time.time()-self.hora_ultima_senial<3600: #evita mandar correos de señales demasiado seguido
            return


        titulo=self.par+' Señal ' + self.analisis_provocador_entrada
        texto=titulo+'\n'

        texto+=self.linea("analisis_e7=",self.analisis_e7)
          
        #texto+=self.texto_analisis_moneda() 

        self.log.log(texto)
        texto+=self.log.tail()
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)
        
        self.hora_ultima_senial=time.time()
        return


    
    def calc_tiempo_trade(self):   
        try:
            tiempo_trade=datetime.now().replace(microsecond=0) - self.fecha_trade
            tiempo_trade=str(tiempo_trade.days)+'d/'+str(divmod(tiempo_trade.seconds,3600)[0])+'h'
        except:
            tiempo_trade='tt' 
        return  tiempo_trade   

    def mostrar_microestado(self):
        try:
            if self.estado==2:
                return self.linea( "Px:", self.format_valor_truncando( self.precio,8), 'Cx:', self.format_valor_truncando( self.precio_compra,8),self.analisis_provocador_entrada+'_'+self.calculo_precio_compra,self.escala_de_analisis,str(self.calc_tiempo_trade()))
            elif self.estado==3:    
                return self.txt_precio_y_stoploss()
            elif self.estado==9:
                return self.linea ( self.format_valor_truncando( self.precio,8) , self.rango   )        
            elif self.estado==8:
                return self.linea ( self.format_valor_truncando( self.precio,8),self.format_valor_truncando( self.e8_precio_inferior,8) ,self.format_valor_truncando( self.e8_precio_superior,8))
            elif self.estado==7:
                return self.linea ( self.format_valor_truncando( self.precio,8),  " FS=",  self.e7_filtros_superados    )
        except Exception as e:
            return self.linea('---error en microestado---',str(e))

    def linea(self,*args):
        lin = ' '.join([str(a) for a in args])       
        lin += '\n'
        return lin
    
    def lin(self,*args):
        lin = ' '.join([str(a) for a in args])       
        lin += ' | '
        return lin

    def li(self,*args):
        lin = ' '.join([str(a) for a in args])       
        return lin


    def imprimir_estado_par_en_compra(self):
        ind=self.ind_pool.indicador(self.par)
        texto="\n"
        
         
        #self.log.log( "Libro compran venden:", self.libro.tot_compran_venden(),self.libro.relacion_compra_venta()  )
        #self.log.log( "L g1  compran venden:", self.libro.g1_compran_venden()  )
        #texto+=self.linea( "atr 5m  (10 velas)  :", ind.vatr('5m',10) )
        #texto+=self.linea( "atr 15m (10 velas)  :", ind.vatr('15m',10) )
        #texto+=self.linea( 'Sub4   ,1m,5m,15m,1h:', ind.esta_subiendo3(), ind.esta_subiendo4('1m') , ind.esta_subiendo4('5m') , ind.esta_subiendo4('15m'),ind.esta_subiendo4('1h')     )
        #texto+=self.linea( 'Volumenbu,1m,15m,15m:', ind.volumen_bueno('1m') , ind.volumen_bueno('5m') , ind.volumen_bueno('15m')  ,ind.volumen_bueno('1h'), 'inc_vb=',ind.incremento_volumen_bueno     )
        #texto+=self.linea( 'volumen_porcentaj 1m:', ind.volumen_porcentajes('1m'))
        #texto+=self.linea( 'volumen_porcentaj 5m:', ind.volumen_porcentajes('5m'))
        #texto+=self.linea( 'volumen_porcenta 15m:', ind.volumen_porcentajes('15m'))
        #texto+=self.linea( "                 RSI:", '5m',round(ind.rsi('5m'),2),'15m', round(ind.rsi('15m'),2) ,'4h',round(ind.rsi('4h') ,2),'1d', round(ind.rsi('1d') ,2))
        self.cant_moneda
        if self.estado==2:
            texto+=self.linea( "Precio :", self.format_valor_truncando( self.precio,8), 'Cx:', self.format_valor_truncando( self.precio_compra,8))
        elif self.estado==7:
            texto+=self.linea( "Precio :", self.format_valor_truncando( self.precio,8), self.simbolo_hay_moneda() ) # esparado Señal
               
        self.log.log(texto)

    def imprimir_mini_estado_par_en_compra(self):
        texto="\n"

        if self.estado==2:
            texto+=self.linea( "Precio :", self.format_valor_truncando( self.precio,8), 'Cx:', self.format_valor_truncando( self.precio_compra,8))
            texto+=self.linea( "Act.Px :", Par.mo_pre.comparar_actualizaciones(self.par,'BTCUSDT') )
        elif self.estado==7:
            
                
            texto+=self.linea( "Precio :", self.format_valor_truncando( self.precio,8), self.simbolo_hay_moneda()) # esparado Señal
        self.log.log(texto)

