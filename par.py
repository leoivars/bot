# # -*- coding: UTF-8 -*-
#from binance.enums import * #para  create_order
from mercado_actualizador_socket import Mercado_Actualizador_Socket
from vela import Vela
from binance.client import Client # Cliente python para acceso al exchangue
from indicadores2 import Indicadores #Clase que toma datos de las velas del exchange y produce información (la version1 deprecated)
from logger import Logger #clase para loggear
from correo import Correo
from LectorPrecios import LectorPrecios #clase para tomar precios de todos los pares 
from LibroOrdenes import LibroOrdenes
from datetime import datetime, timedelta
from comandos_interprete import ComandosPar

from ordenes_binance import OrdenesExchange
from actualizador_info_par import ActualizadorInfoPar
from funciones_utiles import memoria_consumida,cpu_utilizada,calc_tiempo_segundos,strtime_a_fecha,strtime_a_time,variacion,variacion_absoluta
from controlador_de_tiempo import *
from variables_globales import  VariablesEstado
from pool_indicadores import Pool_Indicadores
from calc_px_compra import Calculador_Precio_Compra
from intentar_recuperar_venta_perdida import intentar_recuperar_venta_perdida
from fpar.ganancias import calc_ganancia_minima
from mercado import Mercado


from numpy import isnan
import random

#from termcolor import colored #para el libro de ordenes
from acceso_db import Acceso_DB #acceso a la base de datos 
import sys
import time
#from rsi0 import *
import traceback

class Par:
    #variables de clase
    client=''
    operando= False
    lector_precios=None
    correo=None 
    log_resultados=Logger('resultados.log')
    log_errores=Logger('errores.log')
    log_seniales=Logger('seniales.log')
    mo_pre = None
    vol_min_escala={'1M':1,'1w':1/4,'1d':1/30,'4h':(1/30)/24*4,'2h':(1/30)/24*2,'1h':(1/30)/24,'30m':((1/30)/24)/2,'15m':((1/30)/24)/4,'5m':((1/30)/24)/12,'1m':((1/30)/24)/60}
    fibo=(0.236,0.382,0.50,0.618,1,1.382,1.618,2.00,2.618) 
    escalas=('1h','2h','4h','1d','1w','1M')
    adx_minimo={'1m':24 ,'5m':24 ,'15m':24,'30m':24,'1h':23,'2h':23,'4h':22,'1d':21,'1w':20,'1M':19}
    adx_maximo={'1m':30 ,'5m':30 ,'15m':30,'30m':30,'1h':30,'2h':30,'4h':30,'1d':30,'1w':30,'1M':30}
    txt_llamada_de_accion='accion---->'
    

    def __init__(self, client,moneda,moneda_contra,conn,obj_global,mercado): 
        #variables de instancia
        self.par=moneda+moneda_contra
        
        self.g: VariablesEstado = obj_global
        self.estoy_vivo=True # Se usa para detectar cuando la instancia no tiene nada mas que hacer, se elimina de la memoria.
        self.shitcoin=0 # 0 no es shitcoin > 1 si lo es, una shitcoin es una moneda que muy probablemente suba poco y baje rápido por lo que hay que tener las maximas precauciones del caso
        self.libro=''
        self.empCount = 0
        self.ultima_orden={'orderId':0}
        self.moneda_contra='' #moneda contra la que se tradea
        self.moneda='' #moneda que se tiene
        self.moneda_precision=8 #cantidad de digitos para calcular precios dela moneda

        self.idpar=-1
        
        self.precio=0
        self.precio_compra=0
        self.precio_salir_derecho=0
        self.precio_objetivo=0

        self.rango     = (0,0,0)  #rango que se calucla periódicamente en self.recalculo_valores_que_cambian_poco()
        self.rango_sem = (0,0,0) 

        self.precio_salir_derecho_compra_anterior=0 #representa el precio a partir del cual estamos en cero de una compra anterior
        
        self.rango_minimo_promedio=0 # es el rango promedio, de las tres velas mas pequeñas, encontradas de las 100 ultimas velas en escala de 1 dia, se recalcula cada una hora  en el bloque principal  

        self.cant_moneda=0 #cantidad de moneda existente
        self.cant_moneda_stoploss=0 #cantidad de moneda que se proteje con el stoploss
        self.cant_moneda_compra=0 #cantidad de moneda que se pretende comprar
        self.parametro_cantidad=0 #este es el parametro fijado en la base de datos, que se carga en el inicio y no varía se usa en establecer_cantidad_a_comprar(self):   
        self.ganancia_segura=1 #porcentaje que se usa en estado_3_accion para asegurar una ganancia mínima en el caso que el precio esté bajando
        self.ganancia_infima=0.01 # es el porcentaje de ganancia que  nos asegura salir derecho para evitar perdidas mayores
        self.precio_ganancia_infima=0
        self.precio_ganancia_segura=0
        self.tomar_perdidas=0 # si el numero es >=0 no hace nada, caso contrario si nuestras perdidas son inferiores a este numero vendemos asumiendo perdidas
        self.riesgo_tomar_perdidas =-10 # utilizado para el filtro de riesgo beneficio 19/04/2020
        self.tendencia_minima_entrada=4 #tendencia que se usa en estado 7 para determinar que la moneda está subiendo y por lo tanto se puede entrar.

        self.solo_vender=0 #cuando este valor está en no se permite comprar, solo se vende.
        self.solo_seniales=0 #cuando está en 1 solo emite la señial sin comprar
        self.cant_moneda_precision=8 #es la presiscion que acepta el exchange en las ordenes
        self.tickSize=0.00000001 #el minimo incremento/decremento que acepta el exchange
        self.tickSize_proteccion=0 # un minimo incremento calculado en funcion de self.tickSize y de precio actual. La idea es que cuando se produce una variacion muy grande tieda a cero
        self.min_notional=0 # es el valor minimo que debe tener una orden (total de compra o venta) en moneda_contra (varia de para par y se fija en tomar_info_par())
                            # 3/10/2018 encontré un caso en que tomar_info_par() brinda datos erroneos: min_notional que al cumplirlo da error
                            # entonces agrego un campo en min_notional la tabla pares. Si pares.min_notional==0 uso lo obtenido en tomar_info_par()
                            # redondeando pares.min_notional>0 manda sobre tomar_info_par()
        self.min_notional_compra=0 # min notional para comprar
        
        self.x_min_notional = 1 # multiplicador de min_notional, se usa para compra
        
        self._sumaprecios=0 # para calcular precio promedio
        self._cantprecios=0 # para calcular precio promedio
        self.stoploss_actual=0
        self._stoplossActivo=False
        # self.stoploss_actual_string=''
        self.pstoploss_calculado=0 #porcentaje de stoploss que se calcula dinámicamente 
        
        self.estado=-1
        self.estado_anterior=0
        self.estado_bucles=0 #cuenta la cantidad de bucles que ha durado el estado

        self.metodo_compra_venta="auto" #variable que influye en como se calcula el precio de compra y el precio de venta o salida o stoploss
        
        self.cantidad_de_reserva=0

        #usadas en estado4
        self.cant_moneda_venta=0# se calcula a media que se vaya vendiendo.
        self.precio_venta=0# para realizar venta
        self.funcion='' # sirve para saber que actividad está realizando 
        self.log='' #objeto de log que se crean en init

        #comienzo de __init__
        self.client=client
        self._fee= self.g.fee  #comision que cobra el exchangue en cada operacion
        self.pstoploss=5 #parametro de stop loss
        self.generar_liquidez=False # si está en True y el par está en ganancias, el stoploss se calcula al límite de la venta para vender y que haya liquidez
        self.xobjetivo=3 #parametro multiplicador para precio objetivo.
        self.moneda=moneda #moneda que se quiere comprar o vender
        self.moneda_contra=moneda_contra #moneda contra la que se quiere operar 
        
        self.senial_entrada=''
        
        self.stoploss_actual=999 

        self.senial_compra=False # se pone True cuando necesita Comprar


        self.log=Logger(self.par.lower()+'.log') #objeto para loguear la salida de esta clase a un archivo específico como es multihilo por separado
        self.log.loguear=True #False-->solo loguea log.err 
        
        self.ind:Indicadores =Indicadores(self.par,self.log,obj_global,mercado)
        self.mercado:Mercado =mercado
        
        self.libro=LibroOrdenes(client,moneda,moneda_contra,25) #cleación del libro
        self.cola_mensajes=[]
        
        self.bucle=0 #contador general de bucles realziados por el par
        
        self.hora_ultima_senial=0
        
        self.db:Acceso_DB = Acceso_DB(self.log,conn.pool)
        
        if Par.lector_precios == None:
            Par.lector_precios=LectorPrecios(self.client)

        

        self.reserva_btc_en_usd=50 # cantidad expresada en dolares que se deja como reserva de inversion. Se carga con cargar_parametros_json() y se usa en fondos_para_comprar
        self.reserva_usdt=50
        
        self.tiempo_reposo=30 

         

        self.trabajando=True

        self.tendencias=[]
        self.veces_tendencia_minima=3
        self.xvela_corpulenta=10  # si ha velas corpulentas de mayor a x (xvela_corpulenta) veces, no se ingresa por pump 
        self.rsi15m_maximo_para_entrar=65
        self.rsi4h_maximo_para_entrar =65
        self.rsi1d_maximo_para_entrar =65
        
        self.vender_solo_en_positivo=True

        self.bucles_partial_filled=0

        self.forzar_sicronizar=False
        
        self.stoploss_habilitado=0 # indica si debe tener habilitado el stoploss
        self.stoploss_negativo=0# si está en 1, se permite poner stoploss negativos

        self.stoploss_cazaliq=0 # porcentaje (0 100) de gananci que al menos debe tener un par para iniciar el stoploss cuando se encuentra en la funcion cazaliq, si está en cero es automático
        
        self.rango_escala={}# rangos para cada una de las escalas

        #en este momento tengo tres formas posibles de entrar,
        #cada una tiene un analisis o enfoque que predice que la moneda subirá
        #pero tambien tnego salidas, que dependen en cierta medida del análisis que aprobó la entrada
        #particularmente en este momento necesito detectar si se ha entrado por analisis 1 porque tiene encuenta 
        #el cruce de emas para entrar y deberá tene el cruce de emas para salir
        #pero los análisis 2 y 3 son basados en rebotes y por lo tanto no aplican los cruces de ema
        #entonces una entrada por 2 y 3 probacaría una salida instantanea si el algoritmo 

        self.analisis_provocador_entrada='0'
         
        # reset es una mandera que obliga al par
        # a recargar todos sus parametros y comenzar otra vez
        self.reset=False
        
        #porcentaje de ganancia negativa (en realidad es una perdida)
        #a partir de la cual el bot decide comprar mas moneda porque está muy barata
        #y con eso se promedian las pérdidas
        self.e3_ganancia_recompra=-15

        

        #estado 8 esperara que el precio sea menor o = a precio_inferior para comprar
        #pero si el precio se >precio_superior vuelve a la funcion anterior
        self.e8_precio_superior=0
        self.e8_precio_inferior=0


        self.e7_filtros_superados=0

        # id del trade del que se toma la cantidad y el precio y al cual se debe acceder en el momento de venta
        # la funcion que accede al trade debe fijar este valor obtenido con 
        #get_trade_menor_precio... para luego ser utilizado con trade_sumar_ejecutado
        self.idtrade=-1 

        #fecha en la que se ha producido el trade de self.idtrade
        #sirve para establecer la antiguedad del trade y tomar desiciones al respecto
        self.fecha_trade=datetime.now().replace(microsecond=0)

        #instancia de un analizador para btcusdt
        self.analizador_btc=None #
        
        #a partir de que incremento el volumen se considera bueno 
        self.incremento_volumen_bueno=1

        self.uso_de_reserva=0 # algunas monedas pueden usar una parte de las resevas este es un nro entre 0...1

        #con esto me aseguro que to estblezcan los valores iniciales del par
        #self.cargar_parametros_iniales()
        
        # soporte_fibo 
        # luego de realizar una venta es probable que los indicadores de precio den OK para comprar
        # para evitar un comprar inmediatamente luego de vender uso esta variable
        # si es mayor que uno calculo de precio de compra usara retroceso fibo en vez de poc
        self.soporte_fibo=0 

        #minimo volumen expresado en moneda_contra que debe tener el para que entremos al mercado
        # se configura en par.json a razon de un mes
        self.volumen_minimo=0

        self.volumen=0 # el volumen del par, calculado en calcular valores que cambian poco y guardado en los datos del par

        #escala o temporalidad en la que se realiza el análisis de momento para dejarla cuardada en la entrada del trade como
        #para en qué temporalidad somos mas efectivos
        #tambien estoy pensando en poner mas lejanos en escalas grandes y mas ajustadon en escalas chicas
        self.escala_de_analisis='15m' 

        self.oe = OrdenesExchange(self.client,self.par,self.log,obj_global)
        
        #self.actualizador = ActualizadorInfoPar(conn, self.oe ,self.log) #13/9/2021 no actualizamo  mas por ahora 


        self.comandos=ComandosPar(self.log,conn,self) #self: le paso la instancia mima del para para que lo pueda manipular

        
        #par,g: VariablesEstado,log:Logger,ind_par
        self.calculador_precio = Calculador_Precio_Compra(self.par,self.g,self.log,self.ind)

        self.fecha_utimo_px_ws = time.time() - 5000 # alguna fecha vieja para que tenga un valor pero esté desactualizado
        self.fecha_cargar_parametros_durante_accion =  time.time() - 5000 # alguna fecha vieja para que tenga un valor pero esté desactualizado

        self.indentacion=0

        #establece que tipo de cálculo se realizó para determinar el precio de compra
        #en el caso que sea market, el cálculo solo importa para determinar la cantidad a comprar y la orden se creará a market
        self.calculo_precio_compra='?'

   
    def set_log_level(self,log_level):
        self.log.set_log_level(log_level)
        self.log_errores.set_log_level(log_level)
        self.log_resultados.set_log_level(log_level)
        self.log_seniales.set_log_level(log_level)


    # def set_prioridad_idicador(self):
    #     ind:Indicadores=self.ind
    #     prio=0
    #     if   self.estado == 3: #and self.precio > self.precio_salir_derecho and self.stoploss_habilitado == 0:
    #         prio=1
    #     elif self.estado == 2:    
    #         prio=1

    #     ind.prioridad = prio  
    #     self.oe.prioridad = prio  


    def persistir_estado_en_base_datos(self,moneda,moneda_contra,precio,estado):

        self.db.persistir_estado(moneda,moneda_contra,float(precio),estado,self.funcion)


    #esta funciona se usa para cargar parámetros generales de todos los pares
    #que no estarán en la base de datos
    # ahora almacenandos en el obj global
    def cargar_parametros_json(self):

        self.reserva_btc_en_usd= self.g.reserva_btc_en_usd
        self.x_min_notional=self.g.x_min_notional
        self.riesgo_tomar_perdidas=self.g.riesgo_tomar_perdidas

        if self.moneda_contra=='BTC':
            self.volumen_minimo= self.g.volumen_minimo_btc
        elif self.moneda_contra=='USDT':
            self.volumen_minimo=self.g.volumen_minimo_usd
            self.reserva_usdt=self.g.reserva_usdt



    def cargar_parametros_iniales(self):
        #self.log.log('cargar_parametros_iniales')
        self.cargar_parametros_json() #primero que todo porque influye en tomar_info_par
        p=self.db.get_valores(self.moneda,self.moneda_contra)  #necesito que esté primero 
        #antes usaba cant_monesa_compra directamete ahora dejo el parametro cargado y establezco el valor despues, en el futuro hay que mejorarlo pero por ahora lo dejo así por compatibilidad
        Par.lector_precios.leerprecios()

        
        self.pmin_notional = p['min_notional']
        
        self.idpar=p['idpar'] 

        self.parametro_cantidad=p['cantidad']

        self.set_cantidad_moneda_compra(self.parametro_cantidad)

        self.set_cant_moneda_stoploss( float(p['cantidad']) )
        #self.set_precio_compra(p['precio_compra']) el precio de compra se carga del trade ahora
        #self.set_estado_inicial(p['estado_inicial'])
        self.funcion=p['funcion']
        
        
         
        self.solo_vender = p['solo_vender']
        self.solo_seniales= p['solo_seniales']
        self.set_tendencia_minima_entrada(p['tendencia_minima_entrada'])
        self.cantidad_de_reserva=p['cantidad_de_reserva'] #cantidad expresada en moneda del par. 
        self.veces_tendencia_minima=p['veces_tendencia_minima']
        self.xvela_corpulenta=p['xvela_corpulenta']
        self.rsi15m_maximo_para_entrar=p['rsi15m']
        self.rsi4h_maximo_para_entrar =p['rsi4h']
        self.rsi1d_maximo_para_entrar =p['rsi1d']
        self.analisis_e7=p['analisis_e7']
        self.xobjetivo=p['xobjetivo']
        self.shitcoin=p['shitcoin']
        self.stoploss_habilitado=p['stoploss_habilitado']
        self.stoploss_cazaliq=p['stoploss_cazaliq']
        
        self.uso_de_reserva=p['uso_de_reserva']
        self.temporalidades=p['temporalidades'].split()
        
        cant=float(p['cantidad'])
        
        if cant>0:
            Par.lector_precios.usdt_cantidad(cant,self.par) #cantidad a comprar expresado en dolares
        
        
          
        #self.agregar_analizador('BTCUSDT') #lo mismo para este.

        
        #self.agregar_indicador(self.par,self.log)
        ind=self.ind
        #self.agregar_analizador(self.par)
        
        ind.incremento_volumen_bueno=p['incremento_volumen_bueno']
        ind.incremento_volumen_bueno=p['incremento_volumen_bueno']
        

        #self.ganancia_segura=p['ganancia_segura']
        #self.ganancia_infima=p['ganancia_infima']

        #self.ind
        
        self.rsi_analisis_entrada    = p['rsi_analisis_entrada']
        self.escala_analisis_entrada = p['escala_analisis_entrada']

        #como tomar cantidad pone en cero los trades en caso
        #de no tener nada, lo ejecuto aca para empezar 
        #sin trades en diccho caso.
        self.oe.tomar_cantidad(self.moneda)

        self.pstoploss =p['pstoploss']

        self.estado=-1 #-1 obliga a cargar el estado inicial de la funcion #p['estado']
        if p['estado']==4: #nunca empezamos vendiendo
            self.set_estado(-1)
        else:
            self.set_estado(p['estado'])

        

    # def set_pstoploss(self,valor):
        
    #     if valor==0:#calculo automático de stoploss
    #         #self.set_precio()
    #         atr=self.ind.atr('1d',0)#   0 es la vela anteriar a la última, estaba en 1h y parece que era muy, lo pongo en 2h
    #         self.actualizar_precio_ws()
    #         sl=(atr+self.tickSize)/self.precio*100
    #     else:
    #         sl=valor

    #     self.pstoploss=sl 

               
        
                
        
    #def agregar_indicador(self,par,log):
    #    if not par in self.ind:
    #        
    #        self.ind[par]=Indicadores(par,log)          

    #def agregar_analizador(self,par):
    #    if not par in self.ana:
    #        self.ana[par]=Analizador(self.ind_pool.indicador(par))  

    #def eliminar_indicador(self,par):
    #""    if par!='BTCUSDT' and par in self.ind  :
    #        del self.ind[par]

    #def eliminar_analizador(self,par):
    #    if par in self.ana:
    #        del self.ana[par]
        


    def cargar_parametros_durante_accion(self):
        self.log.log(self.txt_llamada_de_accion+'cargar_parametros_durante_accion')
        #self.log.log('cargar_parametros_durante_accion')
        
        p=self.db.get_valores(self.moneda,self.moneda_contra)

        self.parametro_cantidad=p['cantidad']
        
        #self.set_metodo_compra_venta(p['metodo_compra_venta']) #comentado para permitir autoseteo según el caso de cada anális
        self.set_cant_moneda_stoploss( float(p['cantidad']) )
        #self.set_precio_compra(p['precio_compra'])
        #self.set_estado_inicial(p['estado_inicial'])
        
        
        self.set_tendencia_minima_entrada(p['tendencia_minima_entrada'])
        
        self.solo_vender = p['solo_vender']
        self.solo_seniales= p['solo_seniales']
        self.veces_tendencia_minima=p['veces_tendencia_minima']
        self.xvela_corpulenta=p['xvela_corpulenta']
        self.rsi15m_maximo_para_entrar=p['rsi15m']
        self.rsi4h_maximo_para_entrar =p['rsi4h']
        self.rsi1d_maximo_para_entrar =p['rsi1d']
        #self.ind.incremento_volumen_bueno=p['incremento_volumen_bueno']
        self.incremento_volumen_bueno=p['incremento_volumen_bueno']
        if self.moneda_contra!='BTC': #para btc este dato se autoactualiza 
            self.cantidad_de_reserva=p['cantidad_de_reserva']
        self.analisis_e7=p['analisis_e7']
        self.xobjetivo=p['xobjetivo']
        self.shitcoin=p['shitcoin'] 
        self.stoploss_cazaliq=p['stoploss_cazaliq']
        #self.stoploss_habilitado=p['stoploss_habilitado']  comentado 6/5/2019 porque, ahora no es un parámetro de acción ya que se habilita automáticamente cuanto el precio alcanza ciertos niveles de ganancia (hoy ganancia_segura)
        self.e8_precio_inferior=p['e8_precio_inferior']  
        self.e8_precio_superior=p['e8_precio_superior']  
        self.e3_ganancia_recompra=p['e3_ganancia_recompra']  
        
        self.temporalidades=p['temporalidades'].split()
        self.uso_de_reserva=p['uso_de_reserva']

        self.rsi_analisis_entrada    = p['rsi_analisis_entrada']
        self.escala_analisis_entrada = p['escala_analisis_entrada']


        if self.estado==3 or self.estado==1: 
           self.pstoploss = p['pstoploss']
        
        #detectar cambio de función: Si se detecta cambio de función
        #se debe resetear todo
        f=p['funcion'] # detectar cambio de funcion
        if f != self.funcion:
            self.set_funcion(f)

    
    def set_estado(self,pestado_nuevo):
        
        if pestado_nuevo == -1:
            estado_nuevo = self.primer_estado_de_funcion()
        else:
            estado_nuevo = pestado_nuevo    

        self.estado_anterior=self.estado
        
        if self.solo_vender==1:
            self.estado = self.transformar_estado_en_venta(estado_nuevo)
        else:    
            self.estado=estado_nuevo
        
        self.estado_bucles=0

        
    def set_funcion(self,funcion_nueva):
        self.log.log('----------FFFFFFFF funcion nueva',funcion_nueva)
        self.funcion_anterior=self.funcion
        self.funcion=funcion_nueva
        self.reset=True
        self.reposo=1

    def cambiar_funcion(self,funcion_nueva):
        self.log.log('cambiar_funcion',funcion_nueva)
        self.set_funcion(funcion_nueva)
        self.db.persistir_cambio_funcion(self.moneda,self.moneda_contra,-1,funcion_nueva)
        self.tiempo_reposo = 0
        
            

    


    def iniciar(self):
        self.operacion_empezar()
        self.set_precio()

        if self.es_un_estado_valido(self.estado):
            self.iniciar_estado(self.estado)
        else:    
            self.iniciar_estado(self.primer_estado_de_funcion())

        self.operacion_terminar()


    def es_un_estado_valido(self,estado):
        ret = False
        try:
            #validaciones del estado
            if estado >=0:
                ret = True 
        except: 
            pass
        
        return ret     


    def primer_estado_de_funcion(self):
        if self.solo_vender==1:
            return 3

        if self.funcion in "comprar vender": 
            if self.hay_algo_para_vender_en_positivo():
                return 3
            else:    
                return 7        
        elif self.funcion=="arbitraje":
            return 21

        elif self.funcion=="comprar+al+subir": 
            return 9
        elif self.funcion=="comprar+al+subir+stoploss": 
            return 9    
        elif self.funcion=="comprar+precio+stoploss": 
            return 8
        elif self.funcion=="comprar+precio": 
            return 8  
        elif self.funcion=="vender+ya":
            return 4
        elif self.funcion=="comprar+ya":
            return 2        
        elif self.funcion=="cazaliq":
            return 9
        elif self.funcion=="stoploss":
            return 1


        else: #no entiendo nada
            return 0 #solo miro  

    def iniciar_estado(self,pestado):
       
        if pestado>=0:
            self.set_estado(pestado)
        #se quiere cambiar al mismo estado en el que estaba, haría un bucle infinito entonce reiniciamos la funcion.
        elif pestado==self.estado and pestado==self.estado_anterior:
            pestado==self.primer_estado_de_funcion()  
        else: #un parámetro negativo hace que el estado se quede en el mismo lugar si ejecutar set_estado que memoriza el estado anterior, esto es para quedarse en el mismo estado recordando cual era el estado anteror
            pestado=self.estado

        self.log.log('iniciando estado',pestado)
        #para asegurarnos que no quede nada abierto
        self.cancelar_todas_las_ordenes_activas()

        # variables que deben ser reiniciadas en todo estado
        self.tiempo_reposo=0 # anulamos todo reposo porque estamos cambiando de estado
        self.ultima_orden={'orderId':0}
        self.stoploss_habilitado=0
        self.senial_compra=False
        self.fecha_trade=datetime.now().replace(microsecond=0) #una fecha de incio de estado para todos pero luego otros otros estados como el 3 la pueden corregir con los datos previamente guardados
        
        #  

        estado_reconocido=True
        self.log.log('---> Iniciando Estado =',pestado)
        if pestado==0:
            self.estado_0_inicio()
        elif pestado==1:
            self.estado_1_inicio()
        elif pestado==2:
            self.estado_2_inicio()
        elif pestado==3:
            self.estado_3_inicio()
        elif pestado==4:
            self.estado_4_inicio()    
        elif pestado==8:
            self.estado_8_inicio()
        elif pestado==9:
            self.estado_9_inicio()    
        elif pestado==7:
            self.estado_7_inicio()
        else:
            estado_reconocido=False

        if estado_reconocido:
            self.estado_anterior = pestado    

        return estado_reconocido    


    def estado_siguiente(self):
        ret = 0
        if self.funcion=="comprar" or self.funcion=="vender": 
            if self.estado==7: #esperar señar para comprar
                ret =  2 
            elif self.estado==2: #comprar
                ret =  3 
            elif self.estado==3: #esperar a que suba para vender                
                if self.hay_algo_para_vender_en_positivo():
                    ret =  3
                else:    
                    ret =  7     # esto no devería ser 4(vender) INVESTIGAR 
            elif self.estado==4: #vender
                if self.hay_algo_para_vender_en_positivo():
                    ret =  3
                else:    
                    ret =  7  
            else:
                if self.funcion=="comprar":
                    ret =  3
                else:
                    ret =  2    
        elif self.funcion=="arbitraje":
            if self.estado == 21:
                return 31
            else:    
                return 21
        elif self.funcion=="vender+ya":
            self.cambiar_funcion('comprar')
            ret =  -1 

        elif self.funcion=="comprar+ya": 
            ret =  2
    
        elif self.funcion=="comprar+precio": 
            if self.estado==8:
                ret =  2 
            elif self.estado==2: #comprar
                ret =  3 #esperar a que suba y vender
            elif self.estado==3: # Por filled
                ret =  8
            elif self.estado==4: #vendió volvemos al 8 
                ret =  8
        
        elif self.funcion=="cazaliq": 
            if self.estado==9: #esperar fondos para comprar
                ret =  self.pasar_a_estado_a_menos_que_haya_algo_para_vender(nuevo_estado=2)
            if self.estado==2: #comprar
                ret =  3 
            elif self.estado==3: #esperar a que suba para vender                
                ret =  self.pasar_a_estado_9___quedarse_en_3___o_fin_del_trade()
            elif self.estado==4: #vender enviado desde estado 3 cuando se pasó de largo el stoploss. Pero nunca por estado siguiente.
                ret =  self.pasar_a_estado_9___quedarse_en_3___o_fin_del_trade()
            else:
                ret =  9 #no se dió otra condicion, empezamos desde 9

        elif self.funcion=="stoploss": 
            if self.estado==0: #esperar fondos para comprar
                ret =  0
            if self.estado==1: #stoploss
                ret =  4
            elif self.estado==4: #vender enviado desde estado 1
                self.cambiar_funcion('vender')
                ret =  -1 
        
        #si solo_vender está activado, no permito cualquier otro estado
        if self.solo_vender==1:
            ret = self.transformar_estado_en_venta(ret)

        return ret    

    def transformar_estado_en_venta(self,estado):
        if estado !=3 or estado!=4:
            return 3
        else:
            return estado    

    def pasar_a_estado_a_menos_que_haya_algo_para_vender(self,nuevo_estado):
        if self.hay_algo_para_vender_en_positivo(1):
            return 3
        else:    
            return nuevo_estado

    def pasar_a_estado_9___quedarse_en_3___o_fin_del_trade(self):
        gta=self.ganancias_compra_anterior()
        if gta['idtrade'] != -1:
            if gta['gan']>0:
                return 3
            else:
                return 9    
        else:
            #fin del trade    
            self.cambiar_funcion('comprar')
            self.enviar_correo_generico('FIN.TRADE')
            return 0

    def hay_algo_para_vender_en_positivo(self,ganancia=0):
        ret = False
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        idtrade=trade['idtrade'] #este dato es de *suma importancia* para actualizar el trade en caso de vender
        
        cant=self.oe.tomar_cantidad_disponible(self.moneda)
        cant=cant-self.cantidad_de_reserva      
        
        #control de consistencia
        if self.moneda not in "BTC BNB":
            
            # avisa del problema pero permite seguir funcionando
            if cant>0 and idtrade==-1:
                msgerr=self.linea("Error!! hay",cant,self.moneda,"sin trade previo. Revisar")
                self.log.err( msgerr)
        #        self.enviar_correo_error(msgerr)
                
                return False
        
        if idtrade==-1:
            ret = False
        else:
            #camino normal
            if self.monto_moneda_contra_es_suficiente_para_min_motional(cant,self.precio):
                gan=self.calculo_ganancias(trade['precio'],self.precio)
                if gan > ganancia:
                    ret = True
                
        return ret            
    
        
    def ganancias(self):
        ''' ganancia representada en porcentaje '''
        comision=self.precio_compra*self._fee
        comision+=self.precio*self._fee
        
        gan= self.precio - self.precio_compra - comision 
        if self.precio!=0:
            return round(gan/self.precio*100,2)
        else:
            return -0.000000001    
    
    def calculo_ganancias(self,pxcompra,pxventa):  #esta es la funcion definitiva a la que se tienen que remitir el resto.
        comision=pxcompra*self._fee
        comision+=pxventa*self._fee
        gan=pxventa - pxcompra - comision #- self.tickSize
        return round(gan/pxcompra*100,3)          

    def ganancia_total(self,cant=1):
        ''' ganancia representana en moneda contra '''
        comision=self.precio_compra*cant*self._fee
        comision+=self.precio*cant*self._fee
        
        gan= self.precio * cant - self.precio_compra * cant - comision 
        
        return gan

    def calculo_precio_de_venta(self,ganancias):
        comision=self.precio_compra*self._fee
        vta= self.precio_compra * (1+ganancias/100)
        comision+=self.precio*self._fee
        return vta + comision




    def gt(self,tiempo_en_segundos):
        '''
        Retorna una ganancia en porcentaje en funcion del tiempo transcurrido en segundos
        '''    
        # 50 es el 50% anual que sería una locura
        #return 1 + ( 150/(365*86400) ) * tiempo_en_segundos
        return 1 + (tiempo_en_segundos * 0.001)**(1/3) # curva plana entre 1 y 32% a los 360 


    #retorna el precio al que hay que vender para obtener pganancia       
    def calc_precio(self,pganancia):
        return ( -self.precio_compra - self.precio_compra*self._fee) / ( pganancia/100 -1 + self._fee)




    
    def ganancias_contra_stoploss(self):
        comision=self.precio_compra*self._fee
        comision+=self.stoploss_actual*self._fee
        #gan=self.stoploss_actual- self.precio_compra - comision - self.tickSize
        gan=self.stoploss_actual- self.precio_compra - comision
        return round(gan/self.stoploss_actual*100,2) 

    

    def calculo_ganancias_usdt(self,pxcompra,pxventa,cantidad):
        comision = pxcompra * cantidad * self._fee
        comision += pxventa * cantidad * self._fee
        cant_final = cantidad * (pxventa - pxcompra) - comision 
        return Par.lector_precios.valor_usdt(cant_final,self.moneda_contra+'USDT')

    def calculo_ganancias_moneda_contra(self,pxcompra,pxventa,cantidad):
        comision=pxcompra*cantidad*self._fee
        comision+=pxventa*cantidad*self._fee
        gan=cantidad *(pxventa - pxcompra) - comision 
        return gan
    
      

    def tomar_info_par(self,pmin_notional=0): 
        #obtengo info de la moneda y fijo los paramentro necesarios por ahora solo la presicion de la cantidad
        #esto sirve para que se pueda realizar cualquier tipo de orden usado lo que pide el exchange
                
        info = self.oe.info_par()
        
        self.cant_moneda_precision = info['cant_moneda_precision']
        self.moneda_precision      = info['moneda_precision']
        self.tickSize              = info['tickSize']
        self.min_notional          = info['min_notional']
        self.multiplierUp          = info['multiplierUp']

        #pmin_notional viene de pares.min_notional  
        # self.x_min_notional viene de par.json es el multiplicador general
        
        if pmin_notional>0:
            self.min_notional_compra = pmin_notional     * self.x_min_notional
        else:
            self.min_notional_compra = self.min_notional * self.x_min_notional

        return ( info !=None )    

        
        

    #en algunas ocasiones se busca protejer menos cantidad del total
    # como en el caso de BNB que se deja algo para que las comisiones 
    # salgan mas baratas    
    def set_cant_moneda_stoploss(self,cantidad): 
            self.cant_moneda_stoploss=cantidad




    def set_tendencia_minima_entrada(self,valor_int): 
            self.tendencia_minima_entrada=valor_int        



            

    #deprecated ???
    def get_cant_moneda_stoploss(self):
        if self.funcion=="comprar": 
            self.cant_moneda=self.cant_moneda_compra
        if self.funcion=="comprar+stoploss": 
            self.cant_moneda=self.cant_moneda_compra    
        elif self.funcion=="vender" or self.funcion=="vender+fin":
            self.cant_moneda=self.cant_moneda_compra #por ahora uso el mismo parametro para compra que para venta
        elif self.funcion=="stoploss":
            self.cant_moneda=self.cant_moneda_stoploss #y tengo otro parametro para stoploss pero no esta muy claro hay que mejorar esto
        return self.cant_moneda
        

    #fija la cantidad de moneda a comprar  
    
    def set_cantidad_moneda_compra(self,cantidad):
        self.log.log('cantidad_moneda_compra=',cantidad)
        self.cant_moneda_compra=cantidad

    

    def set_precio_venta(self,px):
        self.precio_venta=px


    def tomar_precio(self,precios):
            
        for px in (precios):
            if px['symbol']==self.par:
                self.precio=float(px['price'])
                break
        #datos para el precio promedio        
        self._sumaprecios+=self.precio
        self._cantprecios+=1

    
    def set_precio(self):
        ind=self.ind
        self.precio = ind.precio('1m')


    def precio_promedio(self):
        return  self._sumaprecios/self._cantprecios 
    
    def operacion_empezar(self):
        #while self.operando:
        #    time.sleep(1)
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
            
            #exito = self.procesar_orden_cancelada(orden)

            #if exito:
            #    self.ultima_orden={'orderId':0}#orden nula
            #else:
            #    pass     
                #self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(1440),self.moneda,self.moneda_contra)
                #self.detener()

        return True #exito # verdadero si hubo exito en cancelar
    
    
    
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
                    self.registrar_orden_parcialmente_jecutada(orden)
            else:
                self.log.log(orden['orderId'],'Se mandó a Cancelar pero no se Canceló' )
                self.enviar_correo_error('Cancelar Orden')
        
        return exito 

    def registrar_orden_parcialmente_jecutada(self,orden):
        if orden['side']  == 'BUY':
            self.db.trade_persistir(self.moneda,self.moneda_contra,self.escala_de_analisis,  self.analisis_provocador_entrada+'_'+self.calculo_precio_compra,float(orden['executedQty']),float(orden['price']),2,4,-4,self.texto_analisis_par(),strtime_a_fecha(orden['time']),orden['orderId'])
        else: 
            if self.idtrade>0:
               self.db.trade_sumar_ejecutado( self.idtrade, orden['ejecutado'], orden['precio'],strtime_a_fecha(orden['time']),orden['orderId'])
            else:
                self.log.log(orden['orderId'],'Parcialmente Ejecutada - sin idtrade!' )
                self.enviar_correo_error('Cancelar Orden')    



    def crear_orden_compra(self,cantidad,precio):
        
        if self.calculo_precio_compra=='market':
            ret,self.ultima_orden = self.oe.crear_orden_compra_market(cantidad)
            self.tiempo_reposo=0 #market no esperar
        else:    
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

    #ejemplo de una orden creada con exito
    #self.ultima_orden: {'symbol': 'MANABTC', 'orderId': 38575918, 'clientOrderId': 'P1TuZxGkUFRLXu9fXAaOaB', 'transactTime': 1557695972727, 'price': '0.00000810', 'origQty': '184.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'SELL', 'fills': []}

    def crear_orden_venta_limit(self,cantidad,precio):
        ret,self.ultima_orden = self.oe.crear_orden_venta_limit(cantidad,precio)
        return ret 

    def crear_orden_venta_market(self,cantidad):
        ret,self.ultima_orden = self.oe.crear_orden_venta_market(cantidad)
        return ret                    


    # ORDER_STATUS_NEW = 'NEW'
    # ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    # ORDER_STATUS_FILLED = 'FILLED'
    # ORDER_STATUS_CANCELED = 'CANCELED'
    # ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
    # ORDER_STATUS_REJECTED = 'REJECTED'
    # ORDER_STATUS_EXPIRED = 'EXPIRED'                  
        
    #se supone que un precio está bajando
    #y calcula a cuanto tendría que bajar
    # asegurando una ganancia
    #basánsose en el precio actual

    def zoom(self,escala,x):
        esc=escala
        for i in range(x):
            e=self.g.escala_anterior[esc]
            esc=e
            if e == 'xx':
                #esc=escala
                break
            
        return esc    
    
    def esc_ant(self,escala,x):
        esc=escala
        for i in range(x):
            e=self.g.escala_anterior[esc]
            esc=e
            if e == 'xx':
                esc='1m'
                break
        return esc




    
    def precio_de_recompra_minimo(self,precio_venta,pganancia):
        coef=(1+self._fee)/(1-self._fee)
        ret=precio_venta/coef/(1+pganancia/100)
        return ret


    def calcular_precio_de_compra(self):
        
        metodo=self.determinar_metodo_para_compra_venta()

        px,self.calculo_precio_compra = self.calculador_precio.calcular_precio_de_compra(metodo,self.sub_escala_de_analisis)

        return px



    
    # def restar_cuando_son_malas_condiciones(self,escala,precio):
    #     px=precio
    #     resta=0
    #     ind: Indicadores =self.ind
    
        
    #     if self.moneda_contra=="BTC" and self.esta_feo():
    #         r = ind.promedio_de_maxmin_velas_negativas(escala,top=5,cvelas=10,restar_velas=1)
    #         resta += r
    #         self.log.log('restar_cuando_son_malas_condiciones esta_feo '+ escala ,r) 

    #     #if self.moneda_contra == 'BTC' and self.ind_pool.btc_con_velas_verdes and not self.ind_pool.btc_con_pendiente_negativa: 
    #     #    r = ind.promedio_de_maxmin_velas_negativas(self.escala_de_analisis,top=10,cvelas=30,restar_velas=1)
    #     #    resta += r
    #     #    self.log.log('restar_cuando_moneda_contra_BTC y fomo '+ self.escala_de_analisis ,r) 


    #     # if not self.filtro_rsi(escala,50):
    #     #     prsi=ind.precio_de_rsi(escala,29)
    #     #     r =  abs(px - prsi)
    #     #     resta += r 
    #     #     self.log.log('restar_cuando_son_malas_condiciones filtro_rsi ->' ,r)      
        
    #     return px - resta


    # def esta_feo(self):
        
    #     return not self.ind_pool.btc_con_velas_verdes and self.ind_pool.btc_con_pendiente_negativa  
        
    #     #ind: Indicadores =self.ind_pool.indicador('BTCUSDT')
    #     #ret = False
        
    #     #hmacd = ind.macd_describir(escala)
    #     #if hmacd[1] ==-1 and hmacd[0] ==-1: #macd negativo con pendiente negativa 
    #     #    ret=True   
        

    def determinar_metodo_para_compra_venta(self):
        ''' 
        voy a determinar y comprar por self.sub_escala_de_analisis
        y voy a vender por self.escala_de_analisis

        '''

        ind: Indicadores = self.ind
        
        metodo='menor_de_emas_y_cazaliq' # metodo por defecto
        listo=False   #self.filtro_BTC_pendiente_negativa('1h',20) # si btc comienza a bajar en una hora, nos quedamos con mp_slice_cazaliq
        

        if not listo:
            if self.analisis_provocador_entrada in "buscar_ema_positiva buscar_rebote_rsi":
                metodo="mercado"
                listo=True 

        if not listo:
            if self.analisis_provocador_entrada in "buscar_rsi_bajo":
                metodo="mercado"
                listo=True        
        
        if not listo:
            if self.analisis_provocador_entrada in "buscar_dos_emas_rsi":
                metodo="ema_7"
                #metodo="caza_rsi_bajo2"
                listo=True

        
        if not listo:
            if self.analisis_provocador_entrada in "buscar_cruce_macd_abajo":
                #para escalas mas grandes trato de conseguir un buen precio
                if self.g.escala_tiempo[self.escala_de_analisis] > self.g.escala_tiempo['1h']:
                    if ind.hay_pump3(self.escala_de_analisis,self.g.hay_pump['velas'],self.g.hay_pump['xatr'],self.g.hay_pump['xvol']):
                        metodo="ema_9"
                    else:        
                        metodo="mercado" # en escalas chicas, compramos al toque
                else:
                    metodo="ema_9"
                listo=True

        if not listo:
            if self.analisis_provocador_entrada in "buscar_ema55_para_arriba":
                #para escalas mas grandes trato de conseguir un buen precio
                if self.g.escala_tiempo[self.escala_de_analisis] > self.g.escala_tiempo['1h']:
                    metodo="ema_9"
                else:
                    metodo="ema_20"
                listo=True   
        
        if not listo:
            if self.analisis_provocador_entrada in "buscar_cruce_macd_arriba buscar_ema55_para_arriba":
                #para escalas mas grandes trato de conseguir un buen precio
                if self.g.escala_tiempo[self.escala_de_analisis] > self.g.escala_tiempo['1h']:
                    metodo="ema_9"
                else:
                    metodo="ema_20"
                listo=True        

        if not listo:
            if self.analisis_provocador_entrada in "rebote_pendiente_negativa":
                metodo="ema_9"
                listo=True

        if not listo:
            if self.analisis_provocador_entrada in "rsi_menor_30":
                try:
                    ema = ind.pendiente_positiva_ema('1m',9)
                    if ema:
                        mfi = ind.mfi_vector('1m',2)
                        if  mfi[0] < mfi[1]: # mfi creciendo
                            metodo="mercado"  
                        else:
                            metodo='libro_grupo_mayor'
                except: #algo salió mal, si no compramos barato, no compramos
                    metodo="cazaliq"

                listo=True

        

        if not listo:
            if self.analisis_provocador_entrada in "tres_emas_favorables":
                rsi = ind.rsi(self.sub_escala_de_analisis)
                if rsi < 70:
                    mfi = ind.mfi(self.sub_escala_de_analisis)
                    if mfi >= 40:
                        metodo="ema_9"
                    else:
                        metodo = "ema_20"
                else:
                    metodo="libro_grupo_mayor"

                listo=True
        

        
        if not listo:
            if self.analisis_provocador_entrada=='ema_20_h+':
                metodo="ema_20"
                listo=True
        
        if not listo:
            if self.analisis_provocador_entrada=='ema_55_h+':
                metodo="ema_55"
                listo=True
        
        if not listo:
            if self.analisis_provocador_entrada=='decidir_comprar_deep_macd_rsi':
                metodo="caza_rsi_bajo"
                listo=True

        # if not listo:
        #     p=self.buscar_patron_seguidilla_negativa_rebote_macd(self.sub_escala_de_analisis)
        #     if p[0]:#encontró un patron 180
        #         metodo ='market' #no es lo mismo que mercado, market compra a market que es el preico que sea
        #         listo=True
        #         self.sub_escala_de_analisis = p[1] #redifino la escala al patrón encontrado
        #         self.log.log('patron_seguidilla_negativa_rebote_macd' ,p)      

        # if not listo:
        #     p=self.buscar_patron_180(self.sub_escala_de_analisis)
        #     if p[0]:#encontró un patron 180
        #         metodo ='mercado'
        #         listo=True
        #         self.escala_de_analisis = p[1] #redifino la escala al patrón encontrado
        #         self.log.log('buscar_patron_180' ,p)
        
        if not listo:
            if self.doble_macd_minimo_positivo('15m','5m'):
                metodo ='market'
                listo=True
                

        if not listo:
            if self.doble_macd_minimo_positivo('1h','5m'):
                metodo ='market'
                listo=True
            

        return metodo
    
    def doble_macd_minimo_positivo(self,escala,subescala):
        '''
        busca un armónico entre un macd minimo positivo en una escala y lo mismo en una escala inferior
        la idea es confirmar que esta subiendo en la escala y lo mismo en la subescala
        '''
        ind=self.ind
        ret = False
        if self.filtro_rsi(escala,70):
            macd = ind.busca_macd_hist_min(escala)
            self.log.log('doble_macd_minimo_positivo escala:',escala,macd)
            if macd[0] > 0 and macd[3] > 0 and macd[6] < 60: # macd  con pendiente positiva que en su mínimo el 
                macds = ind.busca_macd_hist_min(subescala)
                if macd[0] > 0 and macds[3]  > 0  : # esta subiendo y el macd en su minimo estaba en menod de 40
                    ret = True
                
                self.log.log('doble_macd_minimo_positivo',ret ,escala,macd,subescala,macds)

        return ret    

    




       
            
     


    

    

    def hay_pump(self):
        ind = self.ind
        ret = False
        for escala in ["5m","15m","1h"]:
            if ind.hay_pump3( escala ,5,10,10):
                ret = True
                break
        return ret   

    
    def mostrar_estado(self):    
        self.log.log(  self.par,'Estado:',self.estado, '{0:.8f}'.format(self.precio), \
        '{0:.8f}'.format(self.precio_promedio()),'{0:.9f}'.format(self.stoploss_actual)      )

    def detener(self):
        self.reset = True
        self.trabajando = False
        self.tiempo_reposo = 0
        
        if self.log.tiempo_desde_ultima_actualizacion() > 1800:
            self.estoy_vivo=False

    def detener_estado_2(self,horas=5):
        self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(horas * 60),self.moneda,self.moneda_contra)            
        self.estado_2_detenerse = True
        self.log.log("detener_estado_2",horas,'hrs')

    
    #esta es la función le de vida al hilo
    #es invocada por el creado en auto_compra_vende.py
    # la secuencia es:
    # instanciacion del par, eso ejecuta __init__
    # y luego trabajar()....

    def trabajar(self):
        
        #set inicial de valores_que_cambian_poco
        ct_recalculo_valores_que_cambian_poco = Controlador_De_Tiempo(3600)
        ct_recalculo_valores = Controlador_De_Tiempo(1800)
        

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
                self.recalculo_valores()
                
                self.iniciar() #ejecuta el inicio del estado o primer estado de la funcion ('comprar','vender' etc)

            if self.forzar_sicronizar: 
                self.forzar_sicronizar=False
                self.sincronizar_compra_venta()
            else:    #este es el flujo normal del bucle
                self.cargar_parametros_durante_accion()
                self.set_precio()
                self.bucle+=1
                self.accion()
                self.imprimir()
                #self.actualizar_estadisticas()
                self.reposar()

            # recalculos periódicos
            if ct_recalculo_valores_que_cambian_poco.tiempo_cumplido():
                self.recalculo_valores_que_cambian_poco()

            if ct_recalculo_valores.tiempo_cumplido():
                self.recalculo_valores()    

            self.log.log(self.txt_llamada_de_accion+'--fin--ultima-linea-trabajando--')    
                    

        self.log.log(self.par,"--->finalizando...")
        self.cancelar_todas_las_ordenes_activas()
        self.mercado.desuscribir_todas_las_escalas(self.par)
        self.imprimir()
        
        #limpio memoria
        #self.eliminar_indicador(self.par)
        #self.eliminar_analizador(self.par)
        #del self.actualizador
        del self.comandos
        del self.ultima_orden
        del self.libro
        
        
        self.log.log(self.par,"--->FIN.")
        
        ##del self.log  no elimnar el log
        self.estoy_vivo=False
    
    
    def cancelar_todas_las_ordenes_activas(self):
        self.oe.cancelar_todas_las_ordenes_activas()
        self.ultima_orden={'orderId':0}#orden nula


    def recalculo_valores_que_cambian_poco(self):
        #self.log.log(self.txt_llamada_de_accion+'__ini__recalculo_valores_que_cambian_poco')
        #ind: Indicadores =self.ind
        #self.rango_minimo_promedio = ind.rango_minimo_promedio('1d',100)
        #self.rango_minimo_promedio = ind.rango_porcentaje_acumulado('1d',-1,30,1)
        #self.log.log('recalculo_valores_que_cambian_poco,rango_minimo_promedio',self.rango_minimo_promedio)  

        #self.actualizar_estadisticas()
        #self.calcular_volumen()
        self.tomar_info_par(self.pmin_notional) #informacion que el exchage suministra sobre el par y muy necesaria para la creación de ordenes.
        #self.log.log(self.txt_llamada_de_accion+'__fin__recalculo_valores_que_cambian_poco')

    def recalculo_valores(self):
        pass
        #self.log.log(self.txt_llamada_de_accion+'__ini__recalculo_valores')
        #self.actualizar_valores_de_rango()
        #self.calcular_gi_gs_tp()  
        #self.log.log(self.txt_llamada_de_accion+'__fin____ini__recalculo_valores')    


    def calcular_volumen(self):
        ind=self.ind
        self.volumen = ind.volumen_sumado_moneda_contra('1d',8)

    # def actualizar_valores_de_rango(self):
    #     for escala in self.g.escalas_comunes_rangos: #en las escalas mas representativas
    #         self.retardo_dinamico(20)
    #         self.rango_escala[escala]=self.calcular_rango(escala)
    #         #self.log.log(self.par,escala,self.rango_escala[escala])

        self.rango = self.rango_escala['1d']    

    # def calcular_rango(self,escala):
    #     ind=self.ind
    #     #velasd = ind.busca_principio_macd_hist_min(escala) # 
    #     #if velasd<7: # si esto da menos
    #     #    velasd=7
    #     # 23/1/2001
    #     # el rango calculado con pocas velas no estaría entregando información correcta por eso pongo un 
    #     # nro harcodeado como para ir viendo
    #     velasd = self.g.escalas_comunes_rangos[escala]
        
    #     rango= ind.mp_slice_ev(escala,velasd,self.tickSize)
    #     return rango

    def reposar(self):
        self.log.log(self.txt_llamada_de_accion+'reposar')
        if self.tiempo_reposo == 0:
            #self.log.log(self.par,'reposo == 0',self.estado)
            return
        else:
            tiempo = self.tiempo_reposo

        self.actualizar_precio_ws_puro()
        px_inico_reposar=self.precio
        
        try:
            

            if tiempo > 1800:
                tiempo=1800   

            #randomizo el tiempo para no dormir a intervalos regulares nunca
            tiempo= tiempo + random.randint(0, 5)


            self.log.log(self.par,"         Reposando:",tiempo)
            
            self.soniar_que_btc_sube(tiempo) # se ejecutó en forma normal
                #espero por una variacion de 0.1% en el precio antes de hace nada
                #self.esperar_actualizacion_precio_ws(px_inico_reposar)

        except Exception as e:
            self.log.err( "Error en reposar():",self.tiempo_reposo,e )  
            self.soniar_que_btc_sube(297) 

    


    #hace tiempo que puede ser interrumpido si se produce un reset
    def soniar_que_btc_sube(self,segundos):
        salida_nomal = True
        fin=segundos
        
        t=0

        self.seguir_soniando = True
        contador_prueba_de_vida = 0
        while t < fin and not self.reset and self.seguir_soniando and self.g.trabajando:
            if self.comandos.interpretar():
                salida_nomal = False
                break

            time.sleep(1)
            t += 1

            contador_prueba_de_vida += 1
            if contador_prueba_de_vida > 300:
                contador_prueba_de_vida = 0
                self.log.log(self.par," sigo reposando:",t)

        return salida_nomal


    def esperar_actualizacion_precio_ws(self,ultimo_precio):
        self.log.log(self.par,"         Esperando cambio en precio...")
        bucles=200 # en caso qeu se cuelgue el actualizador actualizar_precio_ws, sale a los 10 minutos
        while bucles > 0 and ultimo_precio == self.precio and not self.reset and self.g.trabajando:
            #if self.comandos.interpretar(): comentado por que aparentemente se pisaba con la otra llamada. dejo solo una para probar
            #    break
            time.sleep(1)
            self.actualizar_precio_ws_puro()
            bucles -= 1
            
            

    def __no_se_esta_usando____actualizar_estadisticas(self):
        #self.log.log(self.txt_llamada_de_accion+'actualizar_estadisticas')
        ind=self.ind
        escala='1d'
        self.actualizador.actualizar_info(ind,escala,self.moneda,self.moneda_contra)

    


    def liquidez_iniciar(self):
        '''
        Activa la bandera de iniciar_liquidez 
        '''
        self.generar_liquidez = True
        self.seguir_soniando = False #con esto interrumpimos el bucle de sueño
        self.ultimo_calculo_stoploss = 10000 # con esto fuerzo a calcular el stoploss en el próximo loop
        self.log.log('liquidez_iniciar()')
   


    def accion(self): 
        self.log.log(self.txt_llamada_de_accion+'accion')
        
        self.operacion_empezar()

        self.log.log("****** accion() ****** estado",self.estado,'funcion',self.funcion)

        try:
            self.estado_bucles+=1 #cuanta los bucles o ciclos que hace que está en esta estado

            if self.estado==0:    
                self.estado_0_accion() #nada
            elif self.estado==1:    
                self.estado_1_accion() #stoploss
            elif self.estado==2:
                self.estado_2_accion() #comprar  
            elif self.estado==3:
                self.estado_3_accion() #esparar para vender  
            elif self.estado==4:
                self.estado_4_accion() #vender
            elif self.estado==8:
                self.estado_8_accion() #espera precio antes de intentar comprar 
            elif self.estado==7:
                self.estado_7_accion() #espera el momento de comprar
            elif self.estado==9:
                self.estado_9_accion() #espera fondos para comprar    

        except Exception as e:
            self.log.err( "*!*!___err_en_accion__*!*!*Error en accion:",self.par,self.estado,e )
            tb = traceback.format_exc()
            self.log.err( tb)
            self.imprimir()
            self.estado_0_inicio()

        self.operacion_terminar()    


    def estado_0_inicio(self):
        self.log.log( "Estado 0  Inicio" ,self.par )
        self.tiempo_reposo=300 # tiempo entre accion y accion
    def estado_0_accion(self):
        self.log.log(  "Estado 0, no se hace nada" ,self.par )
        if self.funcion=="comprar" or self.funcion=="vender":
            self.sincronizar_compra_venta() 

    def estado_9_inicio(self):
        self.log.log(  "Estado 9, Esperar a tener fondos" ,self.par )
        self.tiempo_reposo=0
        
        
    def estado_9_accion(self):
        pass

        # self.log.log(  "______Estado 9, Acción()_____")
        
        # if self.pasar_a_estado_3_si_hay_algo_en_ganancias():
        #     self.tiempo_reposo=0
        #     return

        # self.tiempo_reposo=450

        # if self.decidir_recomprar_hmacd_rsi('1d'):
        #     ind=self.ind

            
        #     self.log.log( 'px',self.precio,'Rango',self.rango)
            
        #     if self.precio < self.rango[2]: #el precio por debajo del borde superior del rango
        #         if self.fondos_para_comprar():
        #             self.tiempo_reposo=1
        #             self.analisis_provocador_entrada='cazaliq'
        #             self.calculo_precio_compra=''
        #             self.iniciar_estado( self.estado_siguiente() )
        #         else:
        #             self.tiempo_reposo=600    
        #     else:    
        #         self.tiempo_reposo=300

     

    


    
    def pasar_a_estado_3_si_hay_algo_en_ganancias(self):
        gta=self.ganancias_compra_anterior()
        salir = False
        if gta['idtrade'] != -1:
            if gta['gan']>0:
                self.log.log(  "Hay algo para vender en ganancias, nos vamos al estado 3" ,gta['gan'] )
                self.iniciar_estado( 3 )
                salir = True
            else:
                self.log.log(  "ganancias compra anterior" ,gta['gan'] )

        return salir        

             

    def estado_8_inicio(self): #esperar un precio
        self.log.log(  "Estado 8 Descansando" ,self.par )
        
        self.esperar_para_recalcular_rango = Controlador_De_Tiempo(3607) #1 hora 7 segundos, para nuca calcular a la misma hora (teoría conspirativa)
        #self.persistir_estado_en_base_datos(self.moneda,self.moneda_contra,0,self.estado)
        #self.persistir_estado_en_base_datos()

        self.tiempo_reposo=1
        self.metodo_compra_venta="cazabarridas"

        if self.hay_algo_para_vender_en_positivo():
            self.cambiar_funcion('vender')
            self.tiempo_reposo = 0


    def estado_8_accion(self):
        self.log.log( "___E.8 ",self.par )

        self.log.log("\nPrecio: ",self.format_valor_truncando( self.precio,8),  " Esp=",self.format_valor_truncando( self.e8_precio_inferior,8), " Sup=",self.format_valor_truncando( self.e8_precio_superior,8) )
        
        self.tiempo_reposo = 59  
        
        if self.esperar_para_recalcular_rango.tiempo_cumplido():
            
            if self.hay_algo_para_vender_en_positivo():
                self.cambiar_funcion('vender')
                self.tiempo_reposo = 0
                return
            
            # if not self.se_dan_condiciones_para_estado_8():
            #     self.cambiar_funcion('comprar')
            #     self.tiempo_reposo = 0
            #     return    

        if self.precio<=self.e8_precio_inferior:# and self.filtro_btc_apto_para_altcoins():
            self.log.log( "self.precio<=self.e8_precio_inferior: " )
            #abtc=self.ana['BTCUSDT']
            #antes de intentar comprar espero que btc esté tranquilo
            #if not  (  abtc.tomando_fuerza_en_escalas('1m 5m')['resultado'] or abtc.no_es_buen_momento_para_alts()   ): 
            self.precio_compra=0# esto hace que fondos para comprar calcule precio de compra
            if self.fondos_para_comprar():
                self.tiempo_reposo=1
                self.iniciar_estado( self.estado_siguiente() )
                
            else:
                self.log.log( "   Estamos en px pero no hay fondos_para_comprar" )
                #18/01/2020 comentado para evitar el exeso de señales# self.enviar_correo_senial_8()

        elif  self.precio >= self.e8_precio_superior:
            self.log.log( "___E.8 self.precio >= self.e8_precio_superior: " )

            if self.hay_suficiente_para_vender():
                self.cambiar_funcion('vender')
            else:
                self.analisis_provocador_entrada='E.8'
                self.cambiar_funcion('comprar') 

    def retardo_dinamico(self,segundos):
        #retardo para no matar tanto al procesador
        cpu=cpu_utilizada()
        if  cpu > 50:
            tiempo = segundos * cpu/100
            self.log.log( "RRR Retardo dinámico",tiempo )
            time.sleep( tiempo )             


    
    
        
    def estado_7_inicio(self): #comprar por señales
        
        #self.retardo_dinamico(20)

        self.log.log(  "E.7 " ,self.par )

        self.persistir_estado_en_base_datos(self.moneda,self.moneda_contra,0,self.estado)
        self.analisis_provocador_entrada='0'
        self.tiempo_reposo=0
        self.establecer_precio_salir_derecho_compra_anterior()
        #control para no comprar cuando hay que vender
        self.trade_anterior_cerca_entonces_vender()
        if self.estado!=7:
            return



        self.cant_moneda=self.oe.tomar_cantidad(self.moneda)
        


                    # 77777777777777777777
                    # 7::::::::::::::::::7
                    # 7::::::::::::::::::7
                    # 777777777777:::::::7
                    #            7::::::7 
                    #           7::::::7  
                    #          7::::::7   
                    #         7::::::7    
                    #        7::::::7     
                    #       7::::::7      
                    #      7::::::7       
                    #     7::::::7        
                    #    7::::::7         
                    #   7::::::7          
                    #  7::::::7           
                    # 77777777            

    def estado_7_accion(self):
        self.log.log(  "_______E.7",self.par,'B.',self.bucle,"Px:",self.precio)
        self.log.log(  "precio_salir_derecho_compra_anterior",self.precio_salir_derecho_compra_anterior)
        
        self.e7_filtros_superados=0
        self.senial_compra=False 

        #self.retardo_dinamico(20)
        self.set_tiempo_reposo()
        
        #parametro que biene de la tabla pares
        #cuando está en 1 solo emite señales
        solo_senial=self.solo_seniales
        
        if solo_senial==0:
            # si la moneda tiene un tickSize muy grande es muy riesgosa y por lo tanto
            # solo se manda señal
            variacion_tick=round(self.tickSize/self.precio*100,8)
            if  variacion_tick < 3:
                solo_senial=0 # o sea comprar
            else:
                solo_senial=1 # o sea solo dar una señal
                self.log.log('variacion_tick',variacion_tick, 'solo señales')
            
        
        #a precios muy bajos no compramos, esto lo hace filtro 
        comprar = self.filtro_precio()

     

        #decisión nucleo
        if comprar: 
            self.e7_filtros_superados+=1
             
            #comprar=self.super_decision_de_compra()
            comprar=self.super_decision_de_compra()

       
        self.log.log( f'{comprar}<--comprar solo señares {solo_senial}')
        self.imprimir_mini_estado_par_en_compra()    


        # Se pasaron todos los filtros, comprando si tenemos fondos.
        if comprar:
            self.estado_7_comprar(solo_senial)
        else:
            self.estado_7_no_comprar()

        #self.reposar()     
    

    def estado_7_comprar(self,solo_senial):
        self.senial_compra=True
        self.e7_filtros_superados+=1
        
        fondos = self.fondos_para_comprar()

        # si se implemente nuevametne esto, debe ir en una funcion por searado
        #compras_simultaneas = self.g.pares_en_compras[self.moneda_contra] <= self.g.max_compras_simultaneas[self.moneda_contra]

        #if not fondos or not compras_simultaneas:
        #    self.g.falta_de_moneda[self.moneda_contra] = True # al poner esto en true, en auto_compra_vente se baja un par para darle lugar a este que quiere entrar pero no puede

        
        if solo_senial==0 and fondos: # and compras_simultaneas:
            self.tiempo_reposo=0
            self.g.pares_en_compras[self.moneda_contra] += 1
            self.log.log("+++++GOGOGO+++++>  Todo es Positivo, Entramos!",self.par)
            self.log_resultados.log("---",self.par,"Entradando----------------->",self.analisis_provocador_entrada) 
            self.iniciar_estado( self.estado_siguiente() )
            #self.enviar_correo_gogogo()
        else:
            self.log.log(self.par,self.escala_de_analisis,self.analisis_provocador_entrada,"|||||XXXXXX|||||> Todo es Positivo, pero no hay fondos")
            self.estado_7_no_comprar()
                
    
    def estado_7_no_comprar(self):
        # si no compramos, controlamos si en necesario un cambio de estado.
        self.log.log(self.par,"----NO compramos----")
        self.trade_anterior_cerca_entonces_vender()  
        ganterior = self.ganancias_compra_anterior()
        
        
        # si no pasa el filtro filtro_ema_de_tendencia y no se ha cambiado el estado a 3 en la línea anterior, se pone a dormir
        # dormir=False
        # if self.estado!=3:
        #     #si el par está por debajo de la cantidad máxima de pares activos, se duerme
        # #  comentado por ahora # dormir = self.dormir_por_ranking_y_necesidad()
        #     # if not dormir: 
        #     #     #si está muy activo,no lo duermo
        #     #     valor = Par.mo_pre.comparar_actualizaciones(self.par,'BTCUSDT') 
        #     #     if valor < 0.75: #no está muy activo, controlo si hay que dormirlo
        #     #         if not self.filtro_decidir_seguir_comprando_e7():
        #     #             dormir=True
        #     #     else:
        #     #         self.log.log("Activo, mantenemos vivo",valor)         

        #     if dormir:
        #         minutos = self.g.horas_deshabilitar_par * 60 + random.randint(0, 45)
        #         self.db.set_no_habilitar_hasta(self.calcular_fecha_futura( minutos ),self.moneda,self.moneda_contra)            
        #         self.detener()
        #         #self.tiempo_reposo = 900 # en vez de dormirlo, pongo un tiempo de reposo importante

                
    def dormir_por_ranking_y_necesidad(self):
        ret = False
        if self.g.cant_pares_activos > self.g.max_pares_activos:
            miranking = self.g.posicion_ranking(self.moneda,self.moneda_contra)
            self.log.log(self.par,'ranking',miranking)
            if miranking > self.g.max_pares_activos:
                ret = True
        
        return ret        
                





    def deshabiliar_brutalmente(self,minutos_al_futuro=60*24*3):
        self.cancelar_todas_las_ordenes_activas()    
        #self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(minutos_al_futuro),self.moneda,self.moneda_contra)
        self.detener()
        self.log.log("deshabiliar_brutalmente")

    def trade_anterior_cerca_entonces_vender(self):
        #Hay una compra anterior y el precio ahora esta bueno como para esperar para vender (estado 3)
        #ahora esta bueno= el precio ha superado al precio_salir_derecho_compra_anterior
        
        if self.trade_anterior_cerca():
                self.iniciar_estado(3) #Esperar para vender


    def trade_anterior_cerca(self):
        #Hay una compra anterior y el precio ahora esta bueno como para esperar para vender (estado 3)
        #ahora esta bueno= la variacion entre el precio y precio_salir_derecho_compra_anterior es menor al 40% de la ganancia de recompra configurada
        #                  o simplemene el precio ha superado al precio_salir_derecho_compra_anterior
        ret = False
        self.log.log(  "precio_salir_derecho_compra_anterior",self.precio_salir_derecho_compra_anterior)
        if self.precio_salir_derecho_compra_anterior>0:
            variacion_pxant_px= self.var_compra_venta(self.precio_salir_derecho_compra_anterior,self.precio)
            self.log.log(  "precio_salir_derecho_compra_anterior",variacion_pxant_px)
            #si estamos en positivo en el trade anterior, vendemos o si estamos relativamente cerca (pero en negativo) y la funcion no es comprar+precio
            if variacion_pxant_px > 0:
                ret = True
                self.log.log('Hay Trade cerca=',self.precio_salir_derecho_compra_anterior,'precio=',self.precio)

        return ret        
         
    def set_tiempo_reposo(self,ganancias=0):

        if self.estado==3:
            self.tiempo_reposo = 7   
        elif self.estado==7:
            self.tiempo_reposo = 7
        elif self.estado==2:
            self.tiempo_reposo = 17 
        elif self.estado==4:
            self.tiempo_reposo = 15 
        else:
            self.tiempo_reposo = 30


    def super_decision_de_compra(self):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        
        # ya se ha superado la cantidad máxima de  pares con trades, solo esperamos.
        if self.db.trades_cantidad_de_pares_con_trades() >= self.g.maxima_cantidad_de_pares_con_trades and\
           self.db.trades_cantidad(self.moneda,self.moneda_contra) == 0:
            self.log.log(f'maxima_cantidad_de_pares_con_trades superada')   
            return False 

        comprar= False
        entradas = self.db.trades_cantidad(self.moneda,self.moneda_contra)
        cant_temporalidades = len(self.temporalidades)
        self.log.log(f'entradas {entradas}, cant.temporalidades {cant_temporalidades}')
        if entradas < cant_temporalidades:  
            if not comprar: # and self.moneda=='BTC' or self.moneda=='BTCDOWN' or self.moneda=='BTCUP': 
                escalas_a_probar = self.entradas_a_escalas(self.temporalidades,entradas)
                self.log.log(f'escala {escalas_a_probar}')
                
                for esc in escalas_a_probar:
                    if not comprar: 
                        ret = self.buscar_rsi_bajo(esc)
                        if ret[0]:
                            self.escala_de_analisis = ret[1]
                            self.sub_escala_de_analisis = ret[1]
                            self.analisis_provocador_entrada='buscar_rsi_bajo'
                            comprar = True
                            break
                    
                    if not comprar:        
                        ret = self.buscar_rebote_rsi(esc)
                        if ret[0]:
                            self.escala_de_analisis = ret[1]
                            self.sub_escala_de_analisis = ret[1]
                            self.analisis_provocador_entrada='buscar_rebote_rsi'
                            comprar = True
                            break 
            
        return comprar        
        
    def entradas_a_escalas(self,escalas,entradas):
        if entradas <0:
            esc = escalas[0]
        elif entradas > len(escalas) - 1:
            esc = escalas[-1]
        else:
            esc = escalas[ entradas ]   

        if esc=='**': #todas las escalas
            ret=['1m','5m','15m','30m','1h','2h']
        else:
            ret=[esc]    

        return ret     

    def buscar_dos_emas_rsi(self,escala):   
        ret=[False,'xx']
        #self.log.log('0. buscar_rsi_bajo',escala)
        ind: Indicadores =self.ind
        
        if ind.ema_rapida_mayor_lenta(self.g.zoom_out(escala,5),10,55): #analizo solamente en mercado alcista
            rsi = ind.rsi(escala)
            #self.log.log(f'_.rsi {escala} {rsi}')
            if 50 < rsi < 70:
                if ind.variacion_px_actual_px_minimo(self.g.zoom_out( escala,3 ), 48)  < 10:
                    if ind.dos_emas_favorables(escala,7,20):
                        ret = [True,escala,'buscar_dos_emas_rsi']
        
        return ret 


    def buscar_rsi_bajo(self,escala):   
        ret=[False,'xx']
        self.log.log('---buscar_rsi_bajo',escala)
   
        #segun el contexto de la ema 200/50 defino como compraré
        #dmr_vpa,emas_ok = self.calc_dmr_vpa( escala )
        #dmr_rsi = -0.45 if emas_ok else -1 #dmr = diferencia minima recompra, 
        #rsi_inferior = self.calc_rsi_inferior(escala,emas_ok)
        
        #if self.filtro_ema_rapida_lenta(self.g.zoom_out(escala,1), 50,200, 0.01):
        rsi_inf = self.determinar_rsi_minimo_para_comprar(escala)
        if  self.filtro_de_rsi_minimo_cercano(escala, rsi_inf  ,pos_rsi_inferior=(1,2),max_rsi=60):
            if self.filtro_volumen_calmado(escala, 2 , 0.9):
                ret = [True,escala,'buscar_rsi_bajo']

        self.log.log('----------------------')    

        return ret 

    def buscar_rebote_rsi(self,escala):
        ret=[False,'xx']
        self.log.log('---buscar_rebote_rsi',escala)
        if  self.filtro_de_rsi_minimo_cercano(escala, 30 ,pos_rsi_inferior=(1,3),max_rsi=60):
            if self.filtro_ultima_vela_cerrada_alcista(escala):
                if self.filtro_volumen_encima_del_promedio(escala,3,2):
                    ret = [True,escala,'buscar_rebote_rsi']
        self.log.log('----------------------')            
        return ret  



    def filtro_ema_rapida_lenta(self,escala,rapida,lenta,diferancia):
        ind: Indicadores =self.ind
        #esc=self.g.zoom_out(escala,5)
        filtro_ok,dif,pl,pr = ind.ema_rapida_mayor_lenta2( escala, rapida,lenta,diferencia_porcentual_minima=0.09 ) 
        self.log.log(f'    {escala} diferencia% {dif}, pend rapida {pr} pend lenta {pl}')
        self.log.log(f'{filtro_ok} <--ok_filtro_ema_rapida_lenta: {filtro_ok}')
        return filtro_ok

    def buscar_ema_positiva(self,escala):
        ret=[False,'xx']
        self.log.log('--- buscar_ema_positiva',escala)
        if  self.filtro_de_rsi_minimo_cercano(escala, 40 ,pos_rsi_inferior=(1,5),max_rsi=70):
            if self.filtro_ema_rapida_lenta_para_entrar(escala):        
                ret = [True,escala,'buscar_ema_positiva']
        self.log.log('----------------------')
        return ret 

    def filtro_ultima_vela_cerrada_alcista(self,escala):
        ind: Indicadores =self.ind
        v:Vela = ind.ultima_vela_cerrada(escala)
        ret = v.sentido() == 1
        self.log.log( f'{ret}<---UltimaVelaCerrada, open {v.open}, close {v.close}')
        return ret

    def filtro_volumen_encima_del_promedio(self,escala,cvelas,xvol):
        ind: Indicadores = self.ind
        ret = ind.volumen_por_encima_media(escala,cvelas,xvol)    
        self.log.log( f'{ret}<---volumen_encima_del_promedio {escala} {cvelas} {xvol}   ')
        return ret
    
      

    def determinar_rsi_minimo_para_comprar(self,escala):
        ind: Indicadores =self.ind
        #esc_sup = self.g.zoom_out(escala,1)
        rsi_sup = ind.rsi('1d')
        #ema5, difp5,pendr5,pendl5 = ind.ema_rapida_mayor_lenta2( esc_sup , 10,50,0.05) # en temporalidad superior está alcista
        #self.log.log(f'ema {esc_sup}: {ema5}, dif {difp5},pendr {pendr5},pendl {pendl5}')
        ema, difp,pendr,pendl = ind.ema_rapida_mayor_lenta2( '1d', 10,50,0.5,pendientes_positivas=True) 
        self.log.log(f'ema {escala}: {ema}, dif {difp},pendr {pendr},pendl {pendl} rsi_sup {rsi_sup}')
        if 50 < rsi_sup <= 70:
            if ema and pendr > 0 and pendl > 0:
                ret = 40
            else:
                ret = 35
        elif 35 < rsi_sup <= 50:
            if ema:
                ret = 30 
            else: 
                ret = 27
        else: 
            ret = 25       

        if not ema: # la cosa está bajista solo compro con caidas muy pronunciadas
            ret -= 10

        return ret        

    def calc_rsi_inferior(self,escala,emas_ok):
        ind: Indicadores =self.ind
        
        if ind.ema_rapida_mayor_lenta2( self.g.zoom_out(escala,1), 10,20,0.5,pendientes_positivas=True): # en temporalidad superior está alcista
            if emas_ok:
                ret = 45
            else:
                ret = 25    
        else: 
            if emas_ok:
                ret = 40
            else:
                ret = 23

        if self.precio_salir_derecho_compra_anterior >0 :
            ret += 5

        return ret        


    def filtro_ema_rapida_lenta_para_entrar(self,escala):
        ind: Indicadores =self.ind
        filtro_ok,dif,pl,pr = ind.ema_rapida_mayor_lenta2( escala, 10,50, 0.04, pendientes_positivas=True ) 
        self.log.log(f'    {escala} diferencia% {dif}, pend rapida {pr} pend lenta {pl}')
        self.log.log(f'{filtro_ok} <--ok_filtro_ema_rapida_lenta_para_entrar: {filtro_ok}')
        return filtro_ok    

    def filtro_rsi_fuera_zona_indecision(self,escala,rsi_max=56,rsi_min=44):
        ind: Indicadores =self.ind
        rsi = ind.rsi(escala)
        filtro_ok = rsi>rsi_max or rsi <rsi_min
        self.log.log(f'{filtro_ok} <--- {escala} rsi {rsi} ')
        return filtro_ok

    def filtro_ema_rapida_lenta_para_salir(self,escala,gan,duracion_trade):
        self.log.log(f'senial de entrada {self.senial_entrada}')
        ind: Indicadores =self.ind
        gan_min = calc_ganancia_minima(self.g,0.5,self.escala_de_analisis,duracion_trade)
        precio_bajista = self.el_precio_es_bajista('1d')
        precio_no_sube = ind.no_sube(escala)
        tiempo_trade_superado = duracion_trade > self.g.tiempo_maximo_trade[escala]
        duracion_en_velas = int(duracion_trade/self.g.escala_tiempo[escala])
        self.log.log(f'gan_min {gan_min} gan {gan} px_bajista {precio_bajista} px_no_sube {precio_no_sube}' )
        self.log.log(f' duracion {duracion_trade} velas {duracion_en_velas} t_superado {tiempo_trade_superado}')
        
        if gan < 0.3:
            return False
        elif gan < gan_min and not precio_bajista:
            return False

        marca_salida='S>>>'    

        if tiempo_trade_superado and precio_no_sube:
            self.log.log(f'{marca_salida} tiempo_trade_superado y precio_no_sube Velas={duracion_en_velas}')
            return True

        #rapidamente se alcanza el objetivo de self.g.escala_ganancia[escala]
        # solo para escalas pequeñas 
        if self.g.escala_tiempo[escala] <=  self.g.escala_tiempo['15m'] and\
            duracion_trade <= self.g.escala_tiempo[escala] * 2 and\
            gan > self.g.escala_ganancia[escala]:
            self.log.log(f'{marca_salida} ganancia flash {gan} Velas={duracion_en_velas}')
            return True

        rsi_max,rsi_max_pos,rsi = ind.rsi_maximo_y_pos(escala,4)
        self.log.log(f'rsi {rsi} rsi_max {rsi_max} rsi_max_pos {rsi_max_pos}')

        if rsi > 80 and gan>gan_min: ## and self.filtro_volumen_calmado(self.escala_de_analisis):
            self.log.log(f'{marca_salida} rsi escala >80 {rsi}')
            return True

        if rsi > 70 and rsi_max>=rsi and rsi_max_pos <= 3 and precio_no_sube: 
            self.log.log(f'{marca_salida} pico rsi >70 {rsi}')
            return True
        
        if rsi > 65  and self.filtro_volumen_calmado(escala,2) and precio_no_sube:
            self.log.log(f'{marca_salida} rsi escala >65 {rsi}, volumen_calmado 2 and precio_no_sube')
            return True

        if rsi > 53  and precio_bajista and precio_no_sube:
            self.log.log(f'{marca_salida} rsi escala >53 {rsi} ,precio_bajista and precio_no_sube')
            return True

        if rsi_max > 45 and rsi_max_pos <=3 and precio_bajista and precio_no_sube:
            self.log.log(f'{marca_salida} rsi rsi_max > 45 {rsi_max} and rsi_max_pos <3  {rsi_max_pos} and precio_bajista and precio_no_sube')
            return True    

        var = variacion_absoluta(ind.ema(escala,50) ,self.precio  )
        inf = self.g.escala_ganancia[escala] / -10
        if rsi_max > 40 and rsi_max_pos <=5 and precio_no_sube and inf  <= var <= 0:
            self.log.log(f'{marca_salida} rsi_max= {rsi_max} > 40 and rsi_max_pos {rsi_max_pos} <=5 and precio_no_sube and var {inf} <= {var} <= 0')
            return True    
    



        esc_sup = self.g.zoom(escala,1)
        if ind.rsi(esc_sup)>90:
            self.log.log(f'*** rsi escala inf({esc_sup}) >90')
            return True

        if 'buscar_ema_positiva' in self.senial_entrada:            
            salir,dif,pl,pr = ind.ema_rapida_menor_lenta2(escala, 10,50, 0, pendientes_negativas=True ) 
            self.log.log(f'    {escala} 10,50  diferencia% {dif}, pend rapida {pr} pend lenta {pl}')
            return True

        #else:
        #    salir = self.filtro_pico_maximo_ema_maximos(self.escala_de_analisis,4,1) 
        
        return False 




    def el_precio_es_bajista(self,escala):
        ''' trato de definir si el precio es bajista cuando el precio es mayor que la ema de 50. 
        Tratando de evitar la que el resultado sea dudoso ante la compresión de emas (ema 20 muy cerca de ema50) para lo cual uso emas_ok.
        '''
        ind: Indicadores = self.ind
        bajista = True
        if self.precio > ind.ema(escala,50):
            emas_ok, diferencia_porcentual,pend_r,pend_l = ind.ema_rapida_mayor_lenta2(escala,20,50,0.5,True)
            if emas_ok and pend_l >0: 
                bajista = False
        
        return bajista

    def filtro_pico_minimo_ma_minimos(self,escala,cvelas_bajada=7,posicion_minimo=1,control_volumen=True):
        ind: Indicadores =self.ind
        minimo,velas_bajada = ind.minimo_en_ma(escala,6,'Close',cvelas=posicion_minimo+1) 
        min_ok = minimo >= posicion_minimo and velas_bajada >=cvelas_bajada
        self.log.log(f' minimo en {minimo}, velas en bajada {velas_bajada}')
        if min_ok and control_volumen:
            self.log.log(f'{min_ok} <--ok_filtro_pico_minimo_ema_minimos: {cvelas_bajada}')
            vol_ok = ind.volumen_por_encima_media(escala,minimo)
            self.log.log(f'{vol_ok} <--ok_volumen_por_encima_media {minimo}')
            ret = min_ok and vol_ok
        else:
            ret = min_ok    
        return ret 

    def filtro_pico_maximo_ema_maximos(self,escala,cvelas_subida=7,posicion_maximo=1):
        ind: Indicadores =self.ind
        pmaximo, velas_subida = ind.maximo_en_ema(escala,periodos=7,datos='Close',cvelas=posicion_maximo+1) 
        filtro_ok = pmaximo >= posicion_maximo and velas_subida >=cvelas_subida
        self.log.log(f'{filtro_ok} <--ok_filtro_pico_maximo_ema_maximos: {cvelas_subida}')
        self.log.log(f'    maximo en {pmaximo}, velas en subida {velas_subida}')
        return filtro_ok

    def filtro_volumen_calmado(self,escala,cvelas,coef_volumen=1):
        ind: Indicadores =self.ind
        filtro_ok = ind.volumen_calmado(escala,cvelas,coef_volumen)
        self.log.log(f'{filtro_ok} <--ok_filtro_volumen_calmado  cvelas {cvelas}')
        return filtro_ok   

    def filtro_rsi_mayor(self,escala,rsi_mayor_que=50):
        ind: Indicadores =self.ind
        rsi = ind.rsi(escala)
        filtro_ok = rsi >= rsi_mayor_que
        self.log.log(f'{filtro_ok} <--ok_filtro_rsi_mayor:{rsi} >= {rsi_mayor_que}')
        return filtro_ok


    def calc_dmr_vpa(self,escala):
        ''' calcula la diferencia minima de recompra en funcion de la situación del precio actual'''
        ind: Indicadores =self.ind
        emas_ok = ind.ema_rapida_mayor_lenta(escala,50,200)
        if emas_ok: # momento alcista en la escala indicada
            ret=-0.25  # liquidación de 100x
        else:
            ret=-0.45
        return ret,emas_ok  
    

    def filtro_escala_superior_alcista(self,escala):
        #en caso alcista en la escala superior, no utilizo este filtro
        ind:Indicadores=self.ind
        esc_sup = self.g.zoom_out(escala,1)
        self.log.log(f'Escala Superior--> {esc_sup}')
        if ind.ema_rapida_mayor_lenta(esc_sup,50,200,diferencia_porcentual_minima=0.15):
            self.log.log(f'True <-- escala_superior_alcista')
            return True

    def filtro_de_diferencias_de_compra(self,escala,dmr_rsi,dmr_vpa):
        ''' trata de evitar una recompra muy encima de la otra'''
        ind:Indicadores=self.ind
        
        #en caso alcista en la escala superior, no utilizo este filtro
        if self.filtro_escala_superior_alcista(escala):
            self.log.log(f'True <-- diferencias_de_compra por alcista escala sup')
            return True

        _,var_px_rsi = ind.buscar_precio_max_rsi(escala,65,55)
        ok_var_px_rsi = (var_px_rsi < dmr_rsi )
        self.log.log(f'{ok_var_px_rsi} <--ok_para_entrar:  var_px_rsi {var_px_rsi} < {dmr_rsi} dmr  ')   
        if self.cantidad_compra_anterior > 0:
            vpa = variacion_absoluta( self.precio_salir_derecho_compra_anterior, self.precio  )
            ok_vpa =  vpa < dmr_vpa 
            self.log.log(f'{ok_vpa} <--ok_vpa: , var_px_comp_ant {vpa} < {dmr_vpa}') 
        else:
            ok_vpa = True
            self.log.log(f'{ok_vpa} <--ok_vpa: , no hay compra anterior') 

        return ok_var_px_rsi and ok_vpa    

    def filtro_de_rsi_minimo_cercano(self,escala,rsi_inferior,pos_rsi_inferior=(2,15),max_rsi=55):
        ind:Indicadores=self.ind
        rsi_min,rsi_min_pos,rsi= ind.rsi_minimo_y_pos(escala,  pos_rsi_inferior[1]    )
        resultado_filtro=  rsi_min < rsi_inferior and pos_rsi_inferior[0] <= rsi_min_pos <= pos_rsi_inferior[1]  and rsi<max_rsi
        self.log.log(f'{resultado_filtro} <-- filtro_de_rsi_minimo_cercano: ')
        self.log.log(f'    busco {rsi_inferior}, actual {rsi_min}')
        self.log.log(f'    rango de cercanía {pos_rsi_inferior}, actual {rsi_min_pos}')
        self.log.log(f'    rsi maximo {max_rsi}, actual {rsi}')
        
        return resultado_filtro

    def filtro_de_histograma_macd_positivo(self,escala):   
        ind:Indicadores=self.ind
        hmacd = ind.macd_describir(escala)
        hmacd_ok = (hmacd[1] ==1  ) #la pendiente de la penultima ema 8 positiva
        self.log.log(f'{hmacd_ok} <--hmacd_ok  hmacd -->{hmacd}')
        return hmacd_ok

    def filtro_de_pendientes_ema(self,escala,periodos_ema=9):
        ind:Indicadores=self.ind
        pemas = ind.pendientes_ema(escala,periodos_ema,2)
        pemas_ok = (pemas[0] > 0 and pemas[1] > 0  ) #la pendiente de la penultima ema 8 positiva
        self.log.log(f'{pemas_ok} <--pemas_ok  pemas -->{pemas}')    
        return pemas_ok
    



    def adx_mdd_ok(self,adx,mdd):
        return    ( adx[0]>=23 and  mdd[0] == 1 and adx[1] >  0) or ( adx[0] < 23 and mdd[0] == -1 and adx[1] < 0 )                   
    
    
    
    def precondiciones_de_entrada_rsi(self,escala):
        ''' reviso acá si se dan las condiciones para comprar tranquilo
            si es una escal chica reviso  que haya tendencia en 4 horas y 1d 
        '''
        ind: Indicadores =self.ind
        ret = True
        
        #para escalas inferiores escalas a controlar
        #controlo que sea alcista y no esté pasado el rsi 
        if ret:
            escalas_a_controlar = ['1d','4h'] # 
            for esc in escalas_a_controlar: 
                if self.g.escala_tiempo[escala] < self.g.escala_tiempo[esc]:
                    rsi = ind.rsi(esc)
                    self.log.log('_. rsi',esc,rsi) 
                    ret = rsi < 70
                    if not ret:
                        break

        #if ret:
        #    ret = not ind.el_precio_puede_caer(escala) 
        #    self.log.log('el_precio_puede_caer!')
        return ret            
   
    
           

    def filtro_muy_cerca_rebote_ema55(self):
        ind: Indicadores =self.ind
        filtro_ok = True
        for esc in self.temporalidades:
            vta = self.precio_de_venta_especulado(self.precio,porcentaje_ganancia=self.g.ganancia_minima[esc],cantidad_ganancia=self.tickSize * 2)
            ema = ind.ema(esc,55)
            if self.precio < ema and ema < vta: #el precio
                filtro_ok = False
                break
        
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_muy_cerca_rebote_ema55 esc,ema,vta',esc,ema,vta)
        return filtro_ok    


    
    def filtro_compara_adx_ema55(self,escala,cvelas):
        ind: Indicadores =self.ind
        adx=ind.compara_adx(escala,cvelas)
        ema=ind.compara_emas(escala,55,cvelas)
        filtro_ok=True
        fin=min(len(adx),len(ema))
        for i in range(0,fin):
            if adx[i]<=0 or ema[i]<0:
                filtro_ok=False
                break  
        self.log.log('adx_compara',adx)
        self.log.log('ema_compara',ema)    
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_compara_adx_ema55',escala,cvelas)
        
        return filtro_ok     

    def fitro_estado_emas_e7(self):
        filtro_ok = False
        for esc in ['1h','4h','1d']: 
            if self.filtro_ultimas_compara_emas(esc ,55,2):
                filtro_ok = True
                break

        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'fitro_estado_emas_e7') 
        
        return filtro_ok 

    

    
    

    def filtro_de_largo_plazo(self):
        ''' hace un análisis minmax mensual de todas las velas
            y un analisis semanal de ultimas 8 semanas para determinar
            si la moneda ha subido mucho '''
        ind: Indicadores =self.ind    
        mm=ind.minmax('1M',48)
        ms=ind.minmax('1w',8)
        rmm=round(-mm[3]/mm[2],2)
        rms=round(-ms[3]/ms[2],2)
        if rmm < 0.5 or rms < 0.5:
            self.log.log('filtro_de_largo_plazo_NOok',mm,ms,rmm,rms)
            return False
        else:
            self.log.log('filtro_de_largo_plazo_OK',mm,ms,rmm,rms)
            return True
    
    
    #filtro que evita comprar monedas de muy bajo precio
    def filtro_precio(self):
        filtro=0
        if self.moneda_contra == 'BTC':
            filtro=0.00000050
        elif self.moneda_contra == 'USDT':
            filtro=0.0001
                  #0.0001621
        
        ret = True
        if self.precio < filtro:
            ret=False
            self.log.log(self.txt_resultado_filtro(ret,self.indentacion)+'filtro_precio',self.precio,filtro)

        return ret
    
    def filtro_atualizaciones_de_precio_par(self):
    
        # cuantos mas pares activos hay, mas exigente me pongo con que reviso
        #if self.g.cant_pares_activos <= 60:
        #    porcentaje_minimo = 0.20
        #elif 60 < self.g.cant_pares_activos < 90:
        #    porcentaje_minimo = 0.15
        #elif 90 < self.g.cant_pares_activos < 110:
        #    porcentaje_minimo = 0.10
        #else:
        
        porcentaje_minimo = 0.005    

        act_vs_btc = Par.mo_pre.comparar_actualizaciones(self.par,'BTCUSDT')
        filtro_ok = ( act_vs_btc > porcentaje_minimo )
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_atualizaciones_de_precio_par',act_vs_btc,'minimo',porcentaje_minimo)   
        return filtro_ok


    def filtro_ema_instantanea(self):
        filtro_ok = (  Par.mo_pre.ema_precio_no_baja(self.par) )
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_ema_instantanea')    
        return filtro_ok   


    def filtro_ema_rsi_1_minuto(self):
        ind: Indicadores =self.ind
        filtro_ok = ind.ema_rapida_mayor_lenta('1m',9,55)
        if filtro_ok:
            filtro_ok = ind.rsi('1m') < 70
        
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_ema_rsi_1_minuto')   

        return filtro_ok    
   

    def filtro_rompe_rango_superior(self):
        
        ret = ( self.precio > self.rango[2]  and self.rango[2] > 0 )
        
        self.log.log('filtro_rompe_rango_superior',ret, self.rango[2])
        
        return ret 


    def filtro_romperango(self):
        ind: Indicadores =self.ind
        pxsuperior=ind.promedio_de_altos('15m',7,77,1) #no toma la ultima vela
        pxinferior=ind.promedio_de_bajos('15m',7,77,1) #no toma la ultima vela
        variacion = pxsuperior/pxinferior - 1
        if variacion > 0.04 and self.precio > pxsuperior:
            ret = True
        else:
            ret = False

        self.log.log('filtro_romperango',ret,'var',variacion,pxinferior,pxsuperior,self.precio)  

        return ret

    def filtro_ultimas_compara_emas(self,escala,periods,cant_pendientes):
        ind: Indicadores =self.ind
        ptes=ind.compara_emas(escala,periods,cant_pendientes)
        sube=True
        for p in ptes:
            #print (p)
            if p <=0:
                sube  = False
                break # si uno solo es negativo, no está subiendo

        if sube:
            self.log.log('filtro_compara_emas_ok',escala,periods,cant_pendientes,ptes)  
        else:
            self.log.log('filtro_compara_emas_NO_ok',escala,periods,cant_pendientes,ptes)  


        return sube
    


    def filtro_ema_de_tendencia(self,escala='1h',rapida=10,lenta=55): # en estado 7 para decidir comprar # en estado 2 para seguir comprando o abortar compra
        ind: Indicadores =self.ind
    
        #filtro_ok = (ind.precio_mayor_ultimas_emas(escala,10,2)  and ind.ema_rapida_mayor_lenta(escala,9,25)) \
        #            or ind.precio_mayor_ultimas_emas(escala,100,2)

        filtro_ok = ind.ema_rapida_mayor_lenta(escala,rapida,lenta)
        
        self.log.log(self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_ema_de_tendencia',escala,rapida,lenta,filtro_ok)  

        return filtro_ok

    def filtro_pendiente_positiva_ema(self,escala='1h',periodos=55): # en estado 7 para decidir comprar # en estado 2 para seguir comprando o abortar compra
        ind: Indicadores =self.ind
    
        #filtro_ok = (ind.precio_mayor_ultimas_emas(escala,10,2)  and ind.ema_rapida_mayor_lenta(escala,9,25)) \
        #            or ind.precio_mayor_ultimas_emas(escala,100,2)

        filtro_ok = ind.pendiente_positiva_ema(escala,periodos)
        
        self.log.log(self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_pendiente_positiva_ema',escala,periodos)  

        return filtro_ok
    

    def filtro_rsi(self,escala='1h',valor_maximo=60): # en estado 7 para decidir comprar # 
        ind: Indicadores =self.ind

        rsi =  ind.rsi(escala)
       
        filtro_ok = rsi < valor_maximo or rsi > 100 # mas que 100 es un rsi indefinido
        
        self.log.log(self.txt_resultado_filtro(filtro_ok,self.indentacion)+'rsi',escala,'max',valor_maximo,rsi)  

        return filtro_ok

    def filtro_rsi_positivo(self,escala='1h'): # 
        ind: Indicadores =self.ind

        rsic =  ind.compara_rsi(escala,2) #tomos las dos ultimas variaciones del rsi 
       
        filtro_ok = ( rsic[0]+rsic[1]  >= 0 ) # el rsi está subiendo en caso de que la suma de las variaciones de positivo. 
        
        self.log.log(self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_rsi_positivo',escala,rsic)  

        return filtro_ok


    def filtros_sar(self): # en estado 7 para decidir comprar # 
        self.log.log('filtros_sar ini')

        filtro_ok = self.filtro_sar('15m')

        #if filtro_ok:
        #    filtro_ok = self.filtro_sar('1h')

        ##if filtro_ok:
        #    filtro_ok =  self.filtro_sar('1d')

        self.log.log('filtros_sar fin')

        return filtro_ok
    
    def filtro_sar(self,escala): 
        ind: Indicadores =self.ind
        
        sar =  ind.sar(escala)

        filtro_ok =  ( sar < self.precio )
        
        if filtro_ok:
            self.log.log('filtro_sar_OK',escala,sar,self.precio)
        else:
            self.log.log('filtro_sar_NO_ok',escala,sar,self.precio)

        return filtro_ok    


    def filtro_ema_de_tendencia_e7(self): # este filtro de utiliza para mantener al par vivo o dormirlo 

        escala='1d'
        filtro_ok=False
        
        while escala != '2h':# 
            if self.__subfiltro_ema_de_tendencia(escala):
                filtro_ok=True
                break
            else:
                escala = self.zoom(escala,1)
        
        return filtro_ok

    def __subfiltro_ema_de_tendencia(self, escala):
        ind: Indicadores =self.ind
    
        rapida = 12
        lenta  = 55

        filtro_ok = ind.ema_rapida_mayor_lenta(escala,rapida,lenta)

        if filtro_ok:
            self.log.log('ema_de_tendencia_e7_OK',escala,rapida,lenta)
        else:
            self.log.log('ema_de_tendencia_e7_NO_ok',escala,rapida,lenta)

        return filtro_ok


    
    def txt_resultado_filtro(self,resultado,nivel=0):
        indentacion=self.txt_indent(nivel)
        if resultado:
            return indentacion + 'OK----'
        else:
            return indentacion + 'NO_ok_' 

    def txt_indent(self,nivel=0):
        return '' + '-' * nivel * 4 
        



    #luego de vender si este filtro da mal  me salgo
    def filtro_ema_de_tendencia_luego_de_vender(self):
        ind: Indicadores =self.ind

        filtro_ok = (ind.ema_rapida_mayor_lenta('15m',21,55)) \
                    or ind.precio_mayor_ultimas_emas('4h',12,55)
        
        return filtro_ok

    
    def filtro_ema_de_tendencia_duro(self):
        ind: Indicadores =self.ind
        
        filtro_ok = ind.precio_mayor_ultimas_emas('4h',200,2) and ind.pendientes_ema_mayores("1h",50,7,0)
        
        return filtro_ok
        

    def filtro_macd(self,escala):
        ind: Indicadores =self.ind
        macd=ind.macd_analisis(escala,12)
        
        if macd[0]==1 and  macd[1]<=10: #señal del macd
            self.log.log("filtro_macd-------> macd_ok",escala,macd)
            ret = True
        else:
            self.log.log("filtro_macd-------> macd_no_ok",escala,macd)
            ret = False

        return ret    

    
  
    def decidir_comprar(self,escala,escala_salida='1m'):
        ind: Indicadores =self.ind
        comprar = False


        while True:
            if ind.ema_rapida_mayor_lenta(escala,10,55):
                self.log.log('---> OK_emas_10_55',escala)
                macd=ind.busca_macd_hist_min(escala)
                # 30/5/2015 cambien el concepto de macd[1] < 1 (muy cerca del minimo) por macd[1] < 15 (en la zona del minimo)
                # para luego obtener confirmacion con rsi <50 y rango previo
                if macd[0]> -1 and macd[1] < 15 and  macd[2] <= 0 and macd[3] >0 and macd[4]>2 : #pendiente del histograma positiva (macd[3] >0) en histogramas negativos(macd[2]) en la zona del minimo (macd[1] < 15) y macd[4]>2 al menos 3 velas negativas
                    self.log.log('---> OK_macd_hist_neg',macd,escala)
                    comprar = True
                    break
                else:
                    self.log.log('---> NO_ok_macd_hist_neg',macd,escala)

            else: 
                self.log.log('---> NO_emas_10_55',escala)

            if escala == escala_salida:
                break

            escala = self.zoom(escala,1)
         
        ret = [comprar,escala]
        self.log.log('---> decidir_comprar',ret)
        return ret



    
    
    def filtro_macd_minimo(self,escala):
        ind: Indicadores =self.ind
        macd=ind.busca_macd_hist_min(escala)
        
        try:
            filtro_ok = ( macd[0]> -1 and macd[1] < 15 and  macd[2] <= 0  and macd[4]>2 ) # en histogramas negativos(macd[2]) en la zona del minimo (macd[1] < 15) y macd[4]>2 al menos 2 velas negativas
        except:
            filtro_ok = False

        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_macd_minimo',escala,macd)
        return filtro_ok

    def filtro_macd_minimo_con_pendiente_positiva(self,escala,velas_en_minimo=2):
        ind: Indicadores =self.ind
        macd=ind.busca_macd_hist_min(escala)
        
        try:
            filtro_ok = ( macd[0]> -1 and macd[1] < 15 and  macd[2] <= 0 and macd[3] >0 and macd[4]>=velas_en_minimo ) # en histogramas negativos(macd[2]) en la zona del minimo (macd[1] < 15) y macd[4]>2 al menos 3 velas negativas
        except:
            filtro_ok = False

        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_macd_minimo_con_pendiente_positiva',escala,macd)
        return filtro_ok

    
    
    

    
    def log_resultado(self,ok,txt):
        if ok:
            self.log.log('OK-',txt)
        else:
            self.log.log('NO-',txt)    
    
    
    def filtro_macd_histograma_con_pendiente_positiva(self,escala):
        '''
           Solo se fija que el histograma tenga pendiente positiva
           no importa si está de lado positivo o negativo
        '''
        ind: Indicadores =self.ind
        macd=ind.busca_macd_hist_min(escala)
        try:
            filtro_ok = (  macd[3] >0  ) 
        except:
            filtro_ok = False

        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'filtro_macd_histograma_con_pendiente_positiva',escala,macd)
        return filtro_ok

    

    
    

    def decidir_comprar_rsi_macd(self,escala,rsi_max):
        ''' La idea de esta funcion es detectar el momento que empieza a recuperarse un par 
            luego de una caida terrible.  Preferentemente en escala 1d o mayor 
            con niveles de rsi muy bajos de 40, esta situación se transforaría en una muy buena oportunida de compra.
            Es probable que por estar en una caía la moneda no se encuentre alcista por lo que las
            emas quedan descartadas.
        '''
        ind: Indicadores =self.ind
        comprar = False
        rsi = ind.rsi(escala)
        if rsi <= rsi_max:
            self.log.log('---> RSI maximo OK',rsi,escala)
            macd=ind.busca_macd_hist_min(escala)
            if macd[0]> -1 and macd[1] < 15 and  macd[2] <= 0 and macd[3] >0 : #pendiente del histograma positiva (macd[3] >0) en histogramas negativos(macd[2]) en la zona del minimo (macd[1] < 15) 
                self.log.log('-----> OK_macd_hist_neg',macd,escala)
                comprar=True
            else:
                self.log.log('-----> NO_ok_macd_hist_neg',macd,escala)
        else:
            self.log.log('---> RSI maximo NO_ok',rsi,escala)            
        
        if comprar:
            self.log.log(self.par,'---> decidir_comprar_rsi_macd_OK',escala,rsi_max)          
        else:
            self.log.log(self.par,'---> decidir_comprar_rsi_macd_NO_ok',escala,rsi_max)  

        return comprar


    def filtro_macd_positivo_pendiente_negativa(self,escala):
        ind: Indicadores =self.ind
        dmd=ind.macd_describir(escala)
        if dmd[0] == 1 and dmd[1] == -1: # esto es macd positivo con mendiente negativa
            return True
        else:
            return False       
    
    def filtro_pendiente_ema_negativa(self,escala,periodos):
        ind: Indicadores =self.ind
        pen=ind.pendientes_ema(escala,periodos,1)
        positva = ind.pendiente_positiva_ema(escala,periodos)
        return not positva
    
    # 26/6/2020 si la ema de minimos de 25 periodos es mayor que la ema de 55 periodos quiere decir que 
    # se está produciendo un rechazo en el precio 
    def filtro_ema_emaminimos(self,escala,cvelas):
        ind: Indicadores =self.ind
        
        ema = ind.ema(escala,55)
        #busco los periodos para la ema donde todos los valore estan debajo de las sombras
        periodos = ind.periodos_ema_minimos(escala,cvelas)
        ema_minimos = ind.ema_minimos(escala,periodos)

        filtro_ok = ( ema_minimos > ema )
        self.log.log (self.txt_resultado_filtro(filtro_ok,self.indentacion)+'_ema_emaminimos',ema_minimos,ema)
        
        return filtro_ok
    
    

    def compara_emas_para_decidir_vender(self,escala):
        ''' retorna True si pendiente OK'''
        ind: Indicadores =self.ind
        mm=ind.compara_emas(escala,10,1)
        if mm[0] >0: 
            self.log.log('------>compara_emas_OK',escala,mm)
            return True
        else:
            self.log.log('------>compara_emas_NO_ok',escala,mm)
            return False


    ###### análisis MACD ######
    def analizar_por_macd(self,escala):
        ind=self.ind
        comprar=False

        macd=ind.macd_analisis(escala,5)
        if macd[0]==1 and  macd[1]<=2: #señal del macd
            self.log.log("amacd-------> macd_ok",escala,macd)
            comprar = True
        else:
            self.log.log("amacd-------> macd_no_ok",escala,macd)

        #analisis del histograma de la señal
        if comprar:
            if macd[2]>0:  
                self.log.log("amacd-------> histograma_ok"   ,escala,macd[2])
                self.e7_filtros_superados+=1
            else:
                self.log.log("amacd-------> histograma_no_ok",escala,macd[2])
                comprar= False    

        self.log.log('analizar_por_macd--->',comprar)
        return comprar 

    


    def estado_1_inicio(self):
        self.retardo_dinamico(5)
        self.tiempo_reposo = 600
        self.tiempo_inicio_estado =  time.time()
        self.log.log(  "____E.1 - stoploss - INICIO",self.par )
        self.persistir_estado_en_base_datos(self.moneda,self.moneda_contra,self.precio_compra,self.estado)
        
        
        
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        #self.log.log('TRADE',trade) 
        if trade['idtrade'] == -1:
            err='No hay trade previo para mantener un stop loss'
            self.log.log(err)
            self.enviar_correo_error(err)
            self.dormir_30_dias()
            return

        self.establecer_precio_salir_derecho_compra_anterior()
        self.establecer_cantidad_a_vender(trade)
        
        self.vender_solo_en_positivo=False # para que estado 4 pueda vender en negatibo en caso de ser necesario
        self.precio_salir_derecho= self.precio_de_venta_minimo(0)
        
        #self.precio_stoploss = self.precio / (1 + self.pstoploss /100)
        self.escala_rango_sl = self.estado_1_calcular_escala_rango()


    #def estado_1_actualizar_stoploss(self):
    #    nuevo_stoploss = self.precio / (1 + self.pstoploss /100)

    #    if nuevo_stoploss > self.precio_stoploss and\
    #         variacion(nuevo_stoploss,self.precio_stoploss)>1:
    #        self.precio_stoploss = nuevo_stoploss

    def estado_1_calcular_precio_inicial(self):
        '''
        busco el precio promedio a todas las partes bajas de las escalas
        para establecer el precio simulado como precio de compra ficticio
        '''
        suma=0
        c=0
        for esc in self.rango_escala:
            ri=self.rango_escala[esc][0] #limite inferior del rango en la escala
            print('ri',ri)
            if variacion(self.precio,ri) < 2:
                suma += ri
                c += 1

        if suma == 0:
            ret = self.precio
        else:
            ret = suma / c

        return ret 

    def estado_1_calcular_escala_rango(self):
        '''
        busco una escala con el rango que contenga al precio actual
        '''
        escala="1d"
        for esc in ['1h', '4h', '1d', '1M', '1w']:
            if self.rango_escala[esc][0] < self.precio < self.rango_escala[esc][2]:
                escala=esc
        return escala                     


    def estado_1_accion(self):
        self.retardo_dinamico(5)
        self.log.log(  "___E.1 STOP_LOSS ",self.par )
        
        if self.hay_algo_para_vender_en_positivo():
            self.cambiar_funcion('vender')
            return

        #self.precio_inicial_stoploss =  self.estado_1_calcular_precio_inicial()

        #var = self.var_compra_venta(self.precio_inicial_stoploss, self.precio  ) 
        gan = self.var_compra_venta(self.precio_compra, self.precio  ) 

        self.log.log(  "self.precio..............",self.precio )
        self.log.log(  "self.precio_compra.......",self.precio_compra ) 
        #self.log.log(  "precio_inicial_stoploss..",self.precio_inicial_stoploss)
        self.log.log(  "rango....................",self.rango_escala[self.escala_rango_sl], self.escala_rango_sl )
        self.log.log(  "self.pstoploss...........",self.pstoploss )
        #self.log.log(  "variacion px y px_ini_sl.",var )
        self.log.log(  "ganancia.................",gan )

            #se rompió el stoploss y el rango:
        if gan < self.pstoploss * -1 and  self.precio < self.rango_escala[self.escala_rango_sl][0] / 1.01  : 
            self.enviar_correo_generico('MOMENTO DE VENDER')
            self.iniciar_estado( self.estado_siguiente() )
            
            #el trade se volvió positivo, nos ponemos a vender 
        elif gan > 0:
            self.cambiar_funcion('vender')    
 





                                                      
 #                  222222222222222                     
 #                 2:::::::::::::::22                   
 #                 2::::::222222:::::2                  
 #                 2222222     2:::::2                  
 #                             2:::::2                  
 #                             2:::::2                  
 #                          2222::::2                   
 # ---------------     22222::::::22    --------------- 
 # -:::::::::::::-   22::::::::222      -:::::::::::::- 
 # ---------------  2:::::22222         --------------- 
 #                 2:::::2                              
 #                 2:::::2                              
 #                 2:::::2       222222                 
 #                 2::::::2222222:::::2                 
 #                 2::::::::::::::::::2                 
 #                 22222222222222222222                 
                                                      
                                                      
                 
    def estado_2_inicio(self): #comprar
        
        self.estado_2_detenerse = False

        self.tactualiza_2=time.time()
        
        self.set_tiempo_reposo()

        self.precio_actual_en_orden_compra=0

        self.establecer_precio_salir_derecho_compra_anterior()

        self.log.log( "Estado 2 Comprando - Inicio" ,self.par )
        
        self.tiempo_inicio_estado=time.time()

        self.stoploss_negativo=0 # esto regulará impedirá la posibilidad de tener stoploss negativo en estado 3, pero estado 3 no tiene la posibilidad de autoregularse. Solamente se habilita la posibilidad de stoploss negativo vis comando (intervencion humana) por el momento
        
        #self.actualizar_valores_de_rango()
        
        # #no entiendo bien que quise hacer con esto, por ahora lo dejo (24/2/19)
        # if self.estado_anterior==3 and (self.ganancias()<0 or self.precio<self.precio_objetivo):
        #     self.estado_7_inicio()
        #     return
 
        #defino el precio de oferta
        #self.libro.actualizar() #descargo el estado actual del libro de ordenes
        #este promedio permite ofrecer un precio situado debajo del precio de compra
        #y encima del mejor soporque en este momento
        #self.precio_compra=(self.libro.mejor_precio_compra()+self.libro.precio_compra())/2 
     
        
        #defino cuanto voy a comprar
        self.establecer_cantidad_a_comprar()
        if self.cant_moneda_compra * self.precio_compra < self.min_notional: 
            self.log.log('self.cant_moneda_compra * self.precio_compra < self.min_notional',self.cant_moneda_compra,self.precio,self.min_notional)
            #no hay guita, reiniciamos funcion
            self.iniciar_estado( self.primer_estado_de_funcion() )
            
            return

        ret=self.crear_orden_compra(self.cant_moneda_compra,self.precio_compra)
        
        if ret!='OK':
            self.iniciar_estado( self.primer_estado_de_funcion() )
            
            return

        self.tiempo_calcular_px_compra = Crontraldor_Calculo_Px_Compra(self.sub_escala_de_analisis)
        self.bucles_partial_filled=0
        #self.persistir_estado_en_base_datos()

        self.precio_venta=0
    
 
    def esperar(self,tiempo,mensaje):
        self.log.log(  mensaje )
        time.sleep(tiempo)

    
    
    def estado_2_accion(self):  #comprar
        
        
        
        #ind=self.ind  
         
        self.retardo_dinamico(1)
        self.set_tiempo_reposo()
        ahora = time.time()
        tiempo_en_estado = int(ahora - self.tiempo_inicio_estado)
        
        self.log.log(  "________E.2 Comprando" ,self.par, "Tiempo",tiempo_en_estado)

        sub_escala_antes=self.sub_escala_de_analisis
        hay_que_salir =self.es_momento_de_salir_estado_2()  #2020-04-01 esto lo calculo antes porque si demora se me puede llenar la orden durente el cálculo 

        
        orden=self.oe.consultar_estado_orden(self.ultima_orden)
        precio_orden=orden['precio']
        estado_orden=orden['estado']
        can_comprada=orden['ejecutado']

        

        if estado_orden in 'NO_SE_PUDO_CONSULTAR UNKNOWN_ORDER NO_EXISTE':
            self.enviar_correo_error('Error al consultar Orden')
            self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(1440),self.moneda,self.moneda_contra)
            self.detener()
            return
        # ORDER_STATUS_NEW = 'NEW'
        # ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
        # ORDER_STATUS_FILLED = 'FILLED'
        # ORDER_STATUS_CANCELED = 'CANCELED'
        # ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
        # ORDER_STATUS_REJECTED = 'REJECTED'
        # ORDER_STATUS_EXPIRED = 'EXPIRED' 
        #self.libro.actualizar() #descargo el estado actual del libro de ordenes
        
        self.imprimir_estado_par_en_compra()

        #calculo nuevo precio de compra, como este proceso es lento al final vuelvo a consultar el estado de la orden
        hay_nuevo_precio=False
        if estado_orden=='NEW': 
            #si cumplió el tiempo para recalcular el precio o ha cambiado la subescala de análisis recalculamos precio
            if self.tiempo_calcular_px_compra.tiempo_cumplido()  or sub_escala_antes !=self.sub_escala_de_analisis:
                self.log.log(  "self.calcular_precio_de_compra()...in" )
                self.establecer_cantidad_a_comprar() # calcula cant y precio
                varpc = variacion(self.precio_actual_en_orden_compra,self.precio_compra)
                self.log.log('----Variación_Precio:',varpc)
                hay_nuevo_precio = varpc > 0.02
                self.log.log(  "self.calcular_precio_de_compra()...fi" , self.format_valor_truncando(self.precio_compra,8) )

                orden=self.oe.consultar_estado_orden(self.ultima_orden)
                precio_orden=orden['precio']
                estado_orden=orden['estado']
                can_comprada=orden['ejecutado']
                if estado_orden in 'NO_SE_PUDO_CONSULTAR UNKNOWN_ORDER NO_EXISTE':
                    self.enviar_correo_error('Error al consultar Orden')
                    self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(1440),self.moneda,self.moneda_contra)
                    self.detener()
                    return


        #ahora proceso el resultado de la orden
        if estado_orden=='NEW': #no ha pasado nada todavía
            self.log.log(  "Estado NEW:" )
            if not hay_que_salir:
                if hay_nuevo_precio: # tenemos un nuevo precio de compra ponemos denuevo la orden
                    self.log.log(  "----->>Reajustamos precio de compra =",self.precio_compra )
                    if self.cancelar_ultima_orden():
                        if self.cant_moneda_compra * self.precio_compra < self.min_notional: 
                            self.log.log('self.cant_moneda_compra * self.precio_compra < self.min_notional',self.cant_moneda_compra,self.precio,self.min_notional)
                            self.iniciar_estado( self.estado_anterior )
                            return
                        else:
                            ret = self.crear_orden_compra(self.cant_moneda_compra,self.precio_compra)
                            if ret!='OK':
                                self.iniciar_estado( self.primer_estado_de_funcion() )
                                return
                    else:
                        self.intentar_recuperar_compra()
                        return
                                
        
        elif estado_orden=='FILLED':
            self.log.log(  "Estado FILLED:" )
            self.precio_compra=precio_orden
            self.cant_moneda_compra=can_comprada
            txt_filled = f'{self.precio_compra}'
            self.orden_llena_o_parcilamente_llena_estado_2(can_comprada,precio_orden,txt_filled,orden) #FI por Filled 
            return 

        elif estado_orden=='PARTIALLY_FILLED': 
            if self.bucles_partial_filled>80: # 20 bucles de 90 segundos, 30 minutos aprox
                orden_cancelada=self.ultima_orden
                if self.cancelar_ultima_orden():
                    #consulto la orden para ver como quedó
                    orden=self.oe.consultar_estado_orden(orden_cancelada)
                    precio_orden=orden['precio']
                    can_comprada=orden['ejecutado']
                    self.precio_compra=precio_orden
                    self.cant_moneda_compra=can_comprada
                    txt_filled = f'PARCIALMENTE-LLENTA.{self.precio_compra}'
                    self.orden_llena_o_parcilamente_llena_estado_2(can_comprada,precio_orden,txt_filled,orden) #PF por Partial Filled

                    self.sincronizar_compra_venta()
                else:
                    self.intentar_recuperar_compra()
                    return
            self.bucles_partial_filled+=1 
            return
        
        if self.estado_2_detenerse:
            self.detener()
        
        if hay_que_salir or self.hay_que_salir_luego_de_no_haber_comprado():             
            self.log.log(  "hay_que_salir, pasamos a estado anterior" )
            self.iniciar_estado( self.primer_estado_de_funcion() )
            self.tiempo_reposo = 0
            #self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(10),self.moneda,self.moneda_contra)
            #self.detener()

    def orden_llena_o_parcilamente_llena_estado_2(self,can_comprada,precio_orden,txt_filled,orden):
        
        gi=self.ganancia_infima
        gs=self.ganancia_segura
        tp=self.tomar_perdidas
                   
        if self.funcion=='comprar+ya': # la decisión de compra fue tomada manualmente, le meto escala de 1d para vender a intradia...
            self.escala_de_analisis='1d' 

        self.log.log('persistiendo trade...')

        self.db.trade_persistir(self.moneda,self.moneda_contra,self.escala_de_analisis,self.analisis_provocador_entrada,can_comprada,precio_orden,gi,gs,tp,self.texto_analisis_par(),strtime_a_fecha(orden['time']),orden['orderId'])
        
        #se compró, hay que pasar al estado de esperar a que suba 
        self.log.log('enviar_correo_filled_compra...')
        self.enviar_correo_filled_compra(txt_filled)
        if self.funcion=='comprar+ya':
            self.cambiar_funcion('vender')
        else:    
            self.iniciar_estado( self.estado_siguiente() )


    def es_momento_de_salir_estado_2(self):
        ''' hace control sobre si se dan las condiciones para seguir comprando
            con indicadores. Como se demora, se hace previo a revisar si se llenó la orden.
            Porque si lo hacemos despues y hay demoras en los indicadores, se podría llenar la orden 
            mientras durante el control.
        
        '''
        # if self.sobrecomprado():
        #     self.log.log('Estoy sobrecomprado! No hay fondos, no podemos seguir comprado')    
        #     return True

        self.log.log(  "Control de malas condiciones de compra estado_2 con indicadores" )
        salir = not self.super_decision_de_compra() 

        if salir:

            self.log.log(  "Salir! no se dan las condiciones de compra, revisaremos orden y saldremos en caso de no haber comprado" )

        return salir

    def hay_que_salir_luego_de_no_haber_comprado(self):
        ''' todo código de salida que no lleve acceso a indicadores
            (porque debe ser muy rápido)
        '''
        #if self.funcion=='cazaliq': # cazaliq solo sale cuando ha comprado, cazaliq es macho, es un nija, es un jedi que sabe el precio donde se va a producir un rebote y por eso no sale nunga
        #    return False
    
        self.actualizar_precio_ws()

        salir = False
        ################### CONTROLO SI TENGO QUE SEGUIR O TENGO QUE  ABANDONAR ##########################

        #Estoy esperando para comprar pero no compra y la situacion del par ya no es buena.
        #He aquí la lista de situaciones e la que abandono la compra.
        
        tiempo_en_estado = int(time.time() - self.tiempo_inicio_estado)

        
        self.log.log(  "Control de malas condiciones de compra estado_2 luego de revisar Orden" )
        
        if not salir:
            self.trade_anterior_cerca_entonces_vender() 
            if self.estado == 3: #Se cambió el estado, nos vamos
                salir = True

        #vuelve a esperar el precio que se haya configurado
        if not salir and self.funcion=='comprar+precio' and self.precio > self.e8_precio_inferior:
            self.log.log(  "funcion=='comprar+precio' and self.precio > self.e8_precio_inferior",self.e8_precio_inferior)
            self.iniciar_estado( self.estado_anterior )
            salir = True
       
        if salir:
            self.log.log(  "Salir! no se dan las condiciones de compra post revidar orden" )

        return salir



    def calcular_fecha_futura(self,minutos_al_futuro):
        ahora = datetime.now()
        fecha_futura = ahora + timedelta(minutes = minutos_al_futuro)
        return  fecha_futura     


     
                   
            #      333333333333333   
            #     3:::::::::::::::33 
            #     3::::::33333::::::3
            #     3333333     3:::::3
            #                 3:::::3
            #                 3:::::3
            #         33333333:::::3 
            #         3:::::::::::3  
            #         33333333:::::3 
            #                 3:::::3
            #                 3:::::3
            #                 3:::::3
            #     3333333     3:::::3
            #     3::::::33333::::::3
            #     3:::::::::::::::33 
            #      333333333333333   
    

    def estado_3_inicio(self): #esperar hasta que suba para vender, o salir por stoploss bajo
       
        self.retardo_dinamico(1)
        self.tiempo_orden_px_objetivo = time.time() - 10000 # una fecha vieja
        self.tiempo_inicio_estado =  time.time()

        self.tiempo_inicio_ganancia = 0
        self.tiempo_inicio_ganancia_infima = 0
        self.tiempo_inicio_ganancia_segura = 0
        self.tiempo_inicio_precio_bajo_stoploss = 0
        self.stoploss_habilitado=0
        self.ultima_orden['orderId']=0
        #duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())

        self.establecer_precio_salir_derecho_compra_anterior()
        

        #ibtc=self.ind["BTCUSDT"]
        self.log.log(  "____E3 Esperar para vender - INICIO",self.par )
        

        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        #self.log.log('TRADE',trade) 
        if trade['idtrade'] == -1:
            self.log.log("No hay trade previo, self.primer_estado_de_funcion()")
            primer_estado = self.primer_estado_de_funcion()
            if primer_estado != 3:
                self.log.log(" self.primer_estado_de_funcion() ---> ", primer_estado)
                self.iniciar_estado( primer_estado )
            else:
                self.dormir_30_dias()
            return

        self.establecer_cantidad_a_vender(trade) #aca se fija idtrade y precio de compra tambien...
        self.generar_liquidez=False

        if self.cant_moneda_compra <= 0:
            err='self.cant_moneda_compra <= 0, no podemos vender eso...'
            if not intentar_recuperar_venta_perdida(self.moneda,self.moneda_contra,self.oe,self.db,self.log):
                self.log.log(err)
                self.enviar_correo_error(err)
                self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(16),self.moneda,self.moneda_contra)
                self.detener()
            else:
                self.reset = True    
            return
        
        #ind=self.ind_pool.indicador(self.par)    

        #self.establecer_precio_compra()
        self.persistir_estado_en_base_datos(self.moneda,self.moneda_contra,self.precio_compra,self.estado)
        
        self.vender_solo_en_positivo=True #esto afecta a estado 4
        
        self.precio_salir_derecho= self.precio_de_venta_minimo(0) 
        
        self.log.log ('Estado anterior',self.estado_anterior,'analisis_provocador_entrada', self.analisis_provocador_entrada)
                
                


    # ESTADO 3 - Accion #
    def estado_3_accion(self):
        self.retardo_dinamico(1)
        ind: Indicadores =self.ind
        tiempo_en_estado = int (time.time() - self.tiempo_inicio_estado)
        duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        #esc_lp = self.escala_a_largo_plazo(self.escala_de_analisis,duracion_trade)
        #zoom_esc_lp = self.zoom(esc_lp,1)
        self.actualizar_precio_ws()
        gan=self.ganancias() #creo esta variable para no llamar reiteradamente a la funcion
        self.set_tiempo_reposo(gan)
        
        self.log.log(  "___E.3 Esp.Ven. Ti:",tiempo_en_estado,self.par,self.escala_de_analisis,self.senial_entrada)
        
        # partir de acá controlo condiciones de venta o salida
        self.log.log(  "---> Control de condiciones de salida --->" )
       
        self.actualizar_precio_ws() 

        ####TOMAR GANANCIAS #####
        #if self.hay_que_tratar_de_tomar_ganancias(gan,atr):
        if self.filtro_ema_rapida_lenta_para_salir(self.escala_de_analisis,gan,duracion_trade):
            self.log.log(  self.par,"cerrar_trade!" )
            self.vender_solo_en_positivo = False
            self.iniciar_estado( 4 )# vendemos
            self.tiempo_reposo = 0
            return

        # #### TOMAR PERDIDAS ####
        # self.log.log( "hay_que_tomar_perdidas?" )
        # if self.filtro_ema_rapida_lenta_para_salir(self.escala_de_analisis ): 
        #     self.log.log( "************tomar_PERDIDAS!******************" )
        #     self.vender_solo_en_positivo = False
        #     self.iniciar_estado( 4 )# vendemos
        #     self.tiempo_reposo = 0
        #     return   

        # PORNER A RECOMPRAR en caso de pérdidas
        # acá  si pasamos cierto umbral de pérdidas, ponemos a recomprar

        if self.momento_de_recomprar(self.escala_de_analisis,gan,duracion_trade):
            #self.enviar_correo_generico(f'RECOMPRA.')
            self.tiempo_reposo = 0
            self.iniciar_estado(7)
            return
        
        self.log.log("FIN E3. Acciones")

 
    def momento_de_recomprar(self,escala,gan,duracion_trade):
        #gan_atr = round ( atr/self.precio * 100 * self.g.x_neg_patr,2 ) #multiplicador de atr negativo para recomprar cuando se pasa cierta perdida
        self.log.log( f'momento_de_recomprar?  gan {gan}' )
        recomprar =  gan < -0.31 and duracion_trade > 60
        ret = False            
        if recomprar:
            self.log.log( 'Intento recomprar---> Sí')
            ret =  self.super_decision_de_compra()
        
        return ret     

    def estado_3_condicones_que_inician_el_stoploss(self,ind,gan,esc_lp,zoom_esc_lp,duracion_trade):
        self.log.log(  "---> condiciones que inician el stoploss --->" )
        self.log.log(  "senial_entrada",self.senial_entrada)

        #condición minima indispensable para poder iniciar un stoploss        
        if  self.precio >= self.precio_salir_derecho + self.tickSize * 2:
            self.log.log(  self.par,"check ganancia_segura")
            if gan >= self.ganancia_segura:
                self.iniciar_stoploss()
                self.log.log("ganancia_segura ini.stoploss")
                return 

            self.log.log(  self.par,"check hay_pump?",esc_lp)
            if self.hay_pump():
                self.log.log(  self.par,"hay_pump! confirmado")
                volatilidad = ind.atr_bajos('15m') + self.tickSize * 2
                if self.precio - volatilidad > self.precio_salir_derecho:
                    self.iniciar_stoploss()
                    return  
                else:
                    self.log.log(  self.par,"hay_pump no se puede. Volatilidad",volatilidad)
            
            _,_,pmin = ind.bollinger(esc_lp,20,2)
            if pmin >= self.precio_salir_derecho:
                tadx =  ind.tendencia_adx (esc_lp,per_rapida=9,per_lenta=55)
                self.log.log(  self.par,"check tendencia_adx",tadx,esc_lp)
                if tadx <=2:
                    self.iniciar_stoploss()
            
            if self.escala_de_analisis in '2h 1h 30m 15m 5m 1m' and duracion_trade < self.tiempo_trade_rapido(self.escala_de_analisis):
                atr = ind.atr_bajos(esc_lp,top=10,cvelas=150,restar_velas=1)
                buffer = self.precio_salir_derecho + atr
                self.log.log(  self.par,"check scalping  atr",esc_lp,atr,'buffer',buffer)
                if self.precio > buffer  :
                    self.log.log(  self.par,"stoploss_iniciado: scalping")
                    self.iniciar_stoploss()
                    return

                self.log.log(  self.par,"check salvar el 1%-- gan:",gan)
                if gan > 4:
                    pxgan = self.calc_precio(1)
                    if self.precio > pxgan + self.tickSize * 2:
                        self.tomar_ganancias(1) #1%
                        return    
                
            if gan >= self.ganancia_infima:
                self.log.log(  self.par,"check pendiente_ema_planas",esc_lp)
                if self.filtro_macd_positivo_pendiente_negativa(esc_lp):
                    if "ema_20_h+" in self.senial_entrada and self.filtro_pendiente_ema_negativa(esc_lp,20):
                        self.log.log("ema_plana ema_20_h+",esc_lp," ini.stoploss")
                        self.iniciar_stoploss()
                    if "ema_55_h+" in self.senial_entrada and self.filtro_pendiente_ema_negativa(esc_lp,55):
                        self.log.log("ema_plana ema_55_h+",esc_lp," ini.stoploss")
                    return  
                
                self.log.log(  self.par,"check el precio puede caer",zoom_esc_lp)
                if ind.el_precio_puede_caer(zoom_esc_lp):
                    self.log.log(  self.par,"el precio puede caer!")
                    self.iniciar_stoploss()
                    return   

                
               

            #28/08/2020 rebote a la media movil de 55
            #Cuando el precio está por debajo de la media movil de 55 en la escala de compra
            #se presume rebote hacia abajo
            self.log.log(  self.par,"check stoploss precio_rebote_a_la_ema55")
            if gan >= self.ganancia_infima and self.rebote_a_la_ema(esc_lp,55):
                self.log.log("precio_rebote_a_la_ema55, ini.stoploss")
                self.iniciar_stoploss()
                return  

            #8/11/2020 rebote al rango superior
            # cuado el precio se acerca al rango superior, ponemos stoploss finito
            # porque es muy probable que el precio no pase de ahí por estadísticas..
            self.log.log(  self.par,"check stoploss rebote_al_rango_superior")
            if gan >= self.ganancia_infima and self.rebote_al_rango_superior():
                self.log.log("rebote_al_rango_superior, ini.stoploss")
                self.iniciar_stoploss()
                return  

            #9/11/2020 rebote al rango inferior
            # cuado el precio se acerca al rango inferior, ponemos stoploss finito
            # porque es muy probable que el precio no pase de ahí por estadísticas..
            self.log.log(  self.par,"check stoploss rebote_al_rango_inferior")
            if gan >= self.ganancia_infima and self.rebote_al_rango_inferior():
                self.log.log("rebote_al_rango_inferior, ini.stoploss")
                self.iniciar_stoploss()
                return  

            # 12/10/2020
            # 27/7/2020  en escalas que se considan muy volátiles se pone el stoploss apenas se pueda
            # si pasa mas de media hora sin poder poner stoploss así, se sale por los caminos normales
            # durante los primeros 7 días.
            #self.log.log(  self.par,"check stoploss seguro_escalas_pequeñas")
            #if  duracion_trade < 604800 and self.escala_de_analisis in '1h 30m 15m' and \
            #    self.precio >= self.precio_salir_derecho + ind.atr_bajos(self.escala_de_analisis,top=100,cvelas=None,restar_velas=1):
            #    self.log.log(  self.par,"stoploss_iniciado: seguro_escalas_pequeñas")
            #    self.iniciar_stoploss()
            #    return
            
            #7/11/2020 activo el stoploss
            #self.log.log(  self.par,"check filtro_btc_apto_para_altcoins")
            #if gan > self.ganancia_infima and not self.filtro_btc_apto_para_altcoins():
            #    self.log.log(  self.par,"stoploss_iniciado: BTC no apto para altcoins")
            #    self.iniciar_stoploss()
            #    return         

            #19/9/2020 como cazaliq es un rebote, apenas estamos en salir derecho clavamos stoploss. 
            # si pasa mas de media hora sin poder poner stoploss así, se sale por los caminos normales
            if  self.funcion=='cazaliq' and self.stoploss_cazaliq>0 and duracion_trade < 600:
                if gan > self.stoploss_cazaliq:
                    self.log.log(  self.par,"stoploss_iniciado: seguro_de_cazaliq")
                    self.iniciar_stoploss()
                    return

            # 06/7/2020 habilitación de stoploss en funciona de gt (ganancias en funcion del tiempo)
            #self.log.log(  self.par,"check stoploss gt")
            #if gan > self.gt(duracion_trade):
            #    self.log.log(  self.par,"stoploss_iniciado: ganancia > gt")
            #    self.iniciar_stoploss()
            #    return        

            #22/5/2020 no hay stoploss, estoy ganando algo y ha pasado mas de una dia desde que compramos
            #self.log.log("duracion_trade",duracion_trade,self.fecha_trade)
            #if  duracion_trade > self.g.escala_tiempo[self.escala_de_analisis] and \
            #    self.calcular_tiempo_ganancia() > 600 and \
            #    self.el_precio_esta_en_un_rango('15m',6):
            #    self.log.log("ccc el_precio_esta_en_un_rango")
            #    self.iniciar_stoploss()
            #    return        

            #23/01/2020 si hay pump y estamos en positvo, ponemos stoploss
            if gan > self.ganancia_infima and Par.mo_pre.ema_precio_no_baja(self.par):
                self.log.log("gan > self.ganancia_infima and Par.mo_pre.ema_precio_no_baja")

                self.log.log(  self.par,"check stoploss tiempo_maximo_trade")
                if duracion_trade > self.g.tiempo_maximo_trade[esc_lp]:
                    self.log.log(  self.par,"stoploss_iniciado: tiempo_maximo_trade")
                    self.iniciar_stoploss()
                    return

                # 18/7/2020 habilitación de stoploss por ema minimos 
                self.log.log(  self.par,"check stoploss stoploss_ema_minimos")
                if self.funcion !="cazaliq" and self.escala_de_analisis in '1d 4h 1h': #saco a cazaliq porque, al comprar sobre mínimos el stoploss se activa al toque
                    emam = ind.stoploss_ema_minimos(esc_lp,cvelas=8,restar_velas=1)
                    if  self.precio > emam > self.precio_salir_derecho :
                        self.log.log(  self.par,"stoploss_iniciado: stoploss_ema_minimos(",esc_lp,",6,1)")
                        self.iniciar_stoploss()
                        return   
                
                #self.log.log(  self.par,"check patron")
                #if  duracion_trade <  self.tiempo_trade_rapido(self.escala_de_analisis) and    'patron' in self.senial_entrada:
                #    self.log.log('patron en ' , self.senial_entrada)
                #    self.iniciar_stoploss()
                #    return

                self.log.log(  self.par,"check stoploss rsi 70")
                if ind.rsi(esc_lp) > 70: #mucha probabilidad de caer
                    self.log.log("ccc rsi("+esc_lp+")> 70 , ini.stoploss")
                    self.iniciar_stoploss()
                    return

                    

            

            if self.analisis_provocador_entrada in "rebote_bajo_ema_patron ema_55_h+":
                atr = ind.atr(esc_lp)
                buffer = self.precio_salir_derecho + atr
                self.log.log(  self.par,"rebote_bajo_ema_patron ema_55_h+ check precio >= psd+atr",buffer,'atr', atr,'escala',esc_lp )
                if self.precio >= buffer:
                    self.iniciar_stoploss()

            if "DOWN" in self.moneda:
                atrbajos = ind.atr_bajos(esc_lp,top=10,cvelas=None,restar_velas=1)
                buffer = self.precio_salir_derecho + atrbajos
                self.log.log(  self.par,"DOWN check psd+atr_bajos",buffer,'atr_bajos', atrbajos,'escala',esc_lp )
                if self.precio >= buffer:
                    self.iniciar_stoploss()
                    
                
                #self.log.log(  self.par,"check stoploss rsi 15")
                #if ind.rsi('15m') > 80: #mucha probabilidad de caer
                #    self.log.log("ccc rsi('15m')> 80 , ini.stoploss")
                #    self.iniciar_stoploss()
                #    return


    def tiempo_trade_rapido(self,escala):
        if escala in "1m 5m 15m 30":
            return 14400 # 4 horas
        elif escala in "1h 2h 4h":
            return 43200 # 12 horas 
        else:
            return 86400 # 1 dia   

    def escala_a_largo_plazo(self,escala,duracion_trade):
        '''si estamos dentro de el tiempo de la escala, lo conservamos pero si se 
        nos pasó el tiempo, usamos la escal de un día.
        Esto es para salir mejor de un trade que salío mal, duró mucho y cuando da salida salga como un trade de largo plazo
        y no como un escalping

        '''
        esc =  escala
        if self.g.escala_tiempo['1d'] > duracion_trade:
            esc = '1d'
        
        self.log.log(esc)    
        return esc


    # def debemos_subir_el_stoploss(self):
    #     ''' estudian situaciones en la que debemos subir el stoploss un poco '''

    #     return not self.filtro_btc_apto_para_altcoins() or self.escala_de_analisis in "5m 1m"

    def px_rango_roto(self):
        return round( self.rango[0] / 1.01, self.moneda_precision  )   


    def actualizar_precio_ws(self):
        ''' actualiza self.precio primero tratando de obtener informacion del web socket
            pero como el puto ws se está cayendo, si el precio es muy viejo o no existe
            voy por el precio mas actualizado de indicadores '''
        
        self.precio = self.precio=self.ind.precio_mas_actualizado()
        self.tickSize_proteccion = self.calcular_tickSize_proteccion()


    def actualizar_precio_ws_puro(self):
        ''' actualiza self.precio solamente web socket
            esto se usa para detectar cambio en el precio impulsado
            desde el exchage '''
        self.precio=self.ind.precio('1m')
    def calcular_tickSize_proteccion(self):
        if self.tickSize/self.precio < 0.01:
            return self.tickSize * 6
        else:    
            return self.tickSize  * 3   
    
    def variacion_tick(self):
        return  round(self.tickSize/self.precio*100,8)


    def ticks_proteccion(self,porcentaje_proteccion=0.5):
        '''' retorna un valor en tickSize * cant_ticks
        donde cant_ticks es 1 si la variacion del tick es mayor a porcentaje_proteccion
        o tantos ticks como sea necesario para aproximarse a porcentaje_proteccion en caso contrario'''
        vt=self.variacion_tick()
        if vt > porcentaje_proteccion:
            cant_ticks = 1
        else:
            cant_ticks = int(porcentaje_proteccion/vt)  

        return self.tickSize * cant_ticks    


    def calcular_tiempo_ganancia_segura(self):
        ahora=time.time()
        gan = self.ganancias()
        ret = 0 
        if gan >= self.ganancia_segura and self.tiempo_inicio_ganancia_segura == 0: # se fija la hora de inicio ganando
            self.tiempo_inicio_ganancia_segura = ahora
        else:
            if gan < self.ganancia_segura: #no estoy ganando
                self.tiempo_inicio_ganancia_segura = 0   
            else: # ganando, calculo el tiempo ganando
                ret = ahora - self.tiempo_inicio_ganancia_segura
        
        return ret

    def calcular_tiempo_ganancia_infima(self):
        ahora=time.time()
        gan = self.ganancias()
        ret = 0 
        if gan >= self.ganancia_infima and self.tiempo_inicio_ganancia_infima == 0: # se fija la hora de inicio ganando
            self.tiempo_inicio_ganancia_infima = ahora
        else:
            if gan < self.ganancia_infima: #no estoy ganando
                self.tiempo_inicio_ganancia_infima = 0   
            else: # ganando, calculo el tiempo ganando
                ret = ahora - self.tiempo_inicio_ganancia_infima
        
        return ret

    def calcular_tiempo_ganancia(self):
        ahora=time.time()
        ret = 0 
        pxgan=self.precio_salir_derecho + self.ticks_proteccion(1) + self.tickSize
        self.log.log('calcular_tiempo_ganancia pxgan',pxgan)
        if self.precio >= pxgan and self.tiempo_inicio_ganancia == 0: # se fija la hora de inicio ganando
            self.tiempo_inicio_ganancia = ahora
        else:
            if self.precio < pxgan: #no estoy ganando
                self.tiempo_inicio_ganancia = 0   
            else: # ganando, calculo el tiempo ganando
                ret = int( ahora - self.tiempo_inicio_ganancia )
                self.log.log('---tiempo_ganancia--->',ret)

        return ret


    def calcular_tiempo_stoploss(self):
        ahora=time.time()
        
        if self.stoploss_habilitado == 1:
            ret = ret = ahora - self.tiempo_inicio_stoploss
        else:
            ret =0

        return ret        

    
    def detener_stoploss(self):
        self.log.log('detener_stoploss_stoploss....')
        self.stoploss_habilitado=0
        self.tiempo_inicio_precio_bajo_stoploss = 0
        if self.cancelar_ultima_orden():
            self.stoploss_actual=0
            self.estado_3_orden_vender('detener_stoploss')
        else:
            self.intentar_recuperar_venta()    
           

    def iniciar_stoploss(self):
        self.log.log(self.par,'iniciar_stoploss....')

        stoploss=self.calcular_stoploss() 

        if self.stoploss_negativo == 0 and  stoploss < self.precio_salir_derecho: # abortamos, hemos calculado no es válido
            #este stoploss calculado es inválido, pero si hay un stoploss puesto de antes válido, lo deja
            self.log.log('No se pude poner stoploss ',stoploss,' < ',self.precio_salir_derecho,'precio_salir_derecho'  )
            return
                
        if self.cancelar_ultima_orden():

            resultado = self.ajustar_stoploss(stoploss)

            if resultado =='OK':
                self.enviar_correo_generico('SL.INI.')
            else:
                self.calcular_precio_objetivo()
                self.estado_3_orden_vender('iniciar_stoploss fracasado')
        else:
            self.intentar_recuperar_venta()        


    def subir_stoploss(self,tikcs,forzado=False):
        if not forzado and not self.ct_subir_stoploss.tiempo_cumplido(): #para evitar subir el stoploss por este método, muy seguido
            return
        nuevo_stoploss = self.stoploss_actual + self.tickSize * tikcs
        if nuevo_stoploss + self.tickSize * 2 < self.precio:
            if self.stoploss_habilitado==1:
                if self.cancelar_ultima_orden():
                    resultado = self.ajustar_stoploss(nuevo_stoploss)
                    if resultado == "OK":
                        ret='sl subido ' + str(nuevo_stoploss) 
                        self.ct_subir_stoploss.reiniciar()
                    else:    
                        self.calcular_precio_objetivo()
                        self.estado_3_orden_vender('iniciar_stoploss fracasado')
                        ret='falló subir el stoploss'
                else:
                    self.intentar_recuperar_venta()    
            else:
                ret='no se puede subir sl, (no habilitado)'    

        else:
            ret='no se puede subir sl'    

        return ret

    def subir_stoploss_uno(self):
        if not self.ct_subir_stoploss_uno.tiempo_cumplido(): #para evitar subir el stoploss por este método, muy seguido
            return
        gan = self.ganancias()
        subido= False

        nuevo_stoploss = self.calculo_precio_de_venta( int(gan) - 1.5 )   

        if nuevo_stoploss > 0 and self.stoploss_actual < nuevo_stoploss < self.precio:
            if self.stoploss_habilitado==1:
                if self.cancelar_ultima_orden():
                    resultado = self.ajustar_stoploss(nuevo_stoploss)
                    if resultado == "OK":
                        self.log.log('sl subido ' + str(nuevo_stoploss) )
                        subido= True
                        self.ct_subir_stoploss_uno.reiniciar()
                    else:    
                        self.calcular_precio_objetivo()
                        self.estado_3_orden_vender('subir_stoploss_uno fracasado')
                        self.log.log('falló subir el stoploss',nuevo_stoploss )

                else:
                    self.intentar_recuperar_venta()    
            else:
                self.log.log('no se puede subir sl, (no habilitado)' )   

        else:
            self.log.log('no se puede subir sl', nuevo_stoploss)   

        if not subido: #como no pude subir 1% trate de subir un tick
            self.subir_stoploss(1)


        return        


    def ajustar_stoploss(self,nuevo_stoploss):
        resultado,self.ultima_orden = self.oe.crear_stoploss(self.cant_moneda_compra,nuevo_stoploss)
        
        if 'STOP_SOBRE_PRECIO' in resultado: #error, la orden se dispararía automáticamente: Vedemos como market
            resultado,self.ultima_orden = self.oe.crear_orden_venta_market(self.cant_moneda_compra)
            self.tiempo_reposo=0 # porque market es al toque

        if resultado =='OK':
            #no se pudo crear el stoploss, vuelvo al sistema que crea orden de venta limit
            self.stoploss_habilitado=1
            self.stoploss_actual = nuevo_stoploss
            self.log.log('stop_loss OK',nuevo_stoploss,resultado)
            self.tiempo_inicio_stoploss = time.time()
            self.tiempo_inicio_precio_bajo_stoploss = 0
            self.ultimo_calculo_stoploss = time.time()
            self.ct_subir_stoploss = Controlador_De_Tiempo(600)
            self.ct_subir_stoploss_uno = Controlador_De_Tiempo(600)
        else:
            self.stoploss_habilitado=0
            self.stoploss_actual=0
            self.log.log('No de puedo poner stoploss',nuevo_stoploss,resultado)    

        return resultado    


    # previene que el exchangue de el error de min_notional
    def monto_moneda_contra_es_suficiente_para_min_motional(self,cantidad,precio_vta):   
        valor=cantidad * precio_vta
        if valor < self.min_notional:
            self.log.err( "Min Notional ",self.min_notional," y ",valor, self.moneda_contra)
            return False
        else:
            return True    


    #retorna la variacion entre compra y ventan %
    def var_compra_venta(self,px_compra,px_venta):
        return ( px_venta/px_compra -1   ) * 100                    
        
    
    def calcular_precio_objetivo_rapido(self):
        self.actualizar_precio_ws()
        self.precio_ganancia_infima=round(self.precio_salir_derecho * ( 1 + self.ganancia_infima / 100) ,8 )   

        self.precio_objetivo = Par.mo_pre.promedio_de_altos(self.par,10)

        if self.precio_objetivo < self.precio_salir_derecho:
            self.precio_objetivo = round(self.precio_salir_derecho * ( 1 + self.ganancia_segura / 100) ,8 ) 
        
        return
    
    def calcular_precio_objetivo(self):
    
        self.actualizar_precio_ws()
        self.precio_ganancia_infima=round(self.precio_salir_derecho * ( 1 + self.ganancia_infima / 100) ,8 )  
        self.precio_ganancia_segura=round(self.precio_salir_derecho * ( 1 + self.ganancia_segura / 100) ,8 )   
        
        self.precio_objetivo=0

        ind=self.ind 
        _, px ,_ = ind.bollinger('1d',periodos=20,desviacion_standard=2,velas_desde_fin=40)

        #for escala in self.g.escalas_comunes_rangos: #en todas las escalas disponibles
        #    px=self.rango_escala[escala][1]
        #    if px > self.precio_objetivo  and self.precio_ganancia_segura * 1.01 < px <  self.precio * self.multiplierUp *.7: #self.precio * self.multiplierUp maximo valor que se puede poner a un precio
        #        self.precio_objetivo = px
                
        
        if self.precio_objetivo == 0:
            self.precio_objetivo = self.precio_salir_derecho * 1.5

        if self.cant_moneda_compra * self.precio_objetivo    < self.min_notional:
            self.precio_objetivo= ( self.min_notional / self.cant_moneda_compra ) + self.tickSize
    
   
    def calcular_gi_gs_tp(self):
        self.actualizar_precio_ws()
        
        self.ganancia_infima = self.buscar_ganancia_en_rangos(0.5)
        
        self.ganancia_segura = self.buscar_ganancia_en_rangos( self.ganancia_infima * 2)
        
        self.tomar_perdidas  = self.buscar_perdida_en_rangos( (self.ganancia_infima /2 * -1) )

        self.log.log('ganancia_infima',self.ganancia_infima,'ganancia_segura',self.ganancia_segura,'tomar_perdidas',self.tomar_perdidas)
 
 
    def buscar_ganancia_en_rangos(self,ganar_como_minimo):
        px=self.precio
        ret=ganar_como_minimo
        
        #ordenos los precios de los rangos
        precios=[]
        for escala in self.g.escalas_comunes_rangos:
            precios.append(self.rango_escala[escala][1])
        precios.sort()  

        print(precios)

        # busco el primer precio que cumple con la condicion
        for precio  in precios:
            gan = self.calculo_ganancias(px,precio)
            if gan > ganar_como_minimo:
                ret = gan
                break

        return float(ret)    

    def buscar_perdida_en_rangos(self,perder_como_minimo):
        px=self.precio
        ret=perder_como_minimo

        #ordeno los precios de los rangos
        precios=[]
        for escala in self.g.escalas_comunes_rangos:
            precios.append(self.rango_escala[escala][0])
        precios.sort(reverse=True)

        #busco el primer precio que comple con la condicon
        for precio in precios:
            gan = self.calculo_ganancias(px,precio)
            if gan < perder_como_minimo:
                ret = gan
                break

        return float(ret)            
    
    
    def estado_3_orden_vender(self,motivo_venta):         
        ret=False
        
        self.log.log(  "E3.Vender:", self.cant_moneda_compra, "precio_objetivo :",self.precio_objetivo )
        if self.monto_moneda_contra_es_suficiente_para_min_motional(self.cant_moneda_compra,self.precio_objetivo):
            resultado=self.crear_orden_venta_limit(self.cant_moneda_compra,self.precio_objetivo) ## aca hay que ver bien cual es la cantidad de moneda que se vende, por ahora self.cant_moneda_compra que sería la misma cantidad que compré
            if resultado =='OK': # hay algo que no podemos manejar
                self.log.log("estado_3_orden_vender OK:")
                ret=True
            else:
                if self.funcion in "comprar vender" and self.solo_vender == 0:
                    self.enviar_correo_error(motivo_venta + ' no se pudo crear orden de venta, pasamos a estado 7')
                    self.iniciar_estado( 7 )
                else:
                    self.enviar_correo_error(motivo_venta + ' no se pudo crear orden de venta, dormimos 10 dias')
                    self.db.set_no_habilitar_hasta( self.calcular_fecha_futura(  60 * 240)  ,self.moneda,self.moneda_contra)
                    self.detener()
                self.log.err("estado_3_orden_vender error:",motivo_venta,resultado)
        
        return ret  

    def dormir_hasta_la_proxima_vela(self):
        duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        esc_lp = self.escala_a_largo_plazo(self.escala_de_analisis,duracion_trade)        
        minutos = self.g.escala_tiempo[self.esc_ant(esc_lp,1)]/60
        self.db.set_no_habilitar_hasta( self.calcular_fecha_futura(  minutos  )  ,self.moneda,self.moneda_contra)
        self.detener()

    def dormir_un_tiempo_prudencial(self):
        gan=self.ganancias()
        if 0 < gan <= 1:
            ad1 = 300
            ad2 = 600
        elif 1 < gan <= 3:    
            ad1 = 900
            ad2 = 1800
        elif 3 < gan <= 10:        
            ad1 = 1800
            ad2 = 3600
        else:
            ad1 = 3600
            ad2 = 7200

        tiempo = self.g.escala_tiempo[self.escala_de_analisis] + random.randint(ad1, ad2)
        
        if tiempo  > self.g.escala_tiempo["1d"]:
            tiempo  = self.g.escala_tiempo["1d"] + random.randint(100, 600)
        
        minutos = int(tiempo /60)

        self.db.set_no_habilitar_hasta( self.calcular_fecha_futura(  minutos  )  ,self.moneda,self.moneda_contra)
        self.detener()    


    def dormir_30_dias(self):
        self.iniciar_estado( 0 )
        minutos = 60 * 24 * 30
        self.db.set_no_habilitar_hasta( self.calcular_fecha_futura(  minutos  )  ,self.moneda,self.moneda_contra)
        self.detener()


   
   
                                                                                                                                        
                                                                                                                                        
#                           tttt                                               lllllll                                                    
#                        ttt:::t                                               l:::::l                                                    
#                        t:::::t                                               l:::::l                                                    
#                        t:::::t                                               l:::::l                                                    
#     ssssssssss   ttttttt:::::ttttttt       ooooooooooo   ppppp   ppppppppp    l::::l    ooooooooooo       ssssssssss       ssssssssss   
#   ss::::::::::s  t:::::::::::::::::t     oo:::::::::::oo p::::ppp:::::::::p   l::::l  oo:::::::::::oo   ss::::::::::s    ss::::::::::s  
# ss:::::::::::::s t:::::::::::::::::t    o:::::::::::::::op:::::::::::::::::p  l::::l o:::::::::::::::oss:::::::::::::s ss:::::::::::::s 
# s::::::ssss:::::stttttt:::::::tttttt    o:::::ooooo:::::opp::::::ppppp::::::p l::::l o:::::ooooo:::::os::::::ssss:::::ss::::::ssss:::::s
#  s:::::s  ssssss       t:::::t          o::::o     o::::o p:::::p     p:::::p l::::l o::::o     o::::o s:::::s  ssssss  s:::::s  ssssss 
#    s::::::s            t:::::t          o::::o     o::::o p:::::p     p:::::p l::::l o::::o     o::::o   s::::::s         s::::::s      
#       s::::::s         t:::::t          o::::o     o::::o p:::::p     p:::::p l::::l o::::o     o::::o      s::::::s         s::::::s   
# ssssss   s:::::s       t:::::t    tttttto::::o     o::::o p:::::p    p::::::p l::::l o::::o     o::::ossssss   s:::::s ssssss   s:::::s 
# s:::::ssss::::::s      t::::::tttt:::::to:::::ooooo:::::o p:::::ppppp:::::::pl::::::lo:::::ooooo:::::os:::::ssss::::::ss:::::ssss::::::s
# s::::::::::::::s       tt::::::::::::::to:::::::::::::::o p::::::::::::::::p l::::::lo:::::::::::::::os::::::::::::::s s::::::::::::::s 
#  s:::::::::::ss          tt:::::::::::tt oo:::::::::::oo  p::::::::::::::pp  l::::::l oo:::::::::::oo  s:::::::::::ss   s:::::::::::ss  
#   sssssssssss              ttttttttttt     ooooooooooo    p::::::pppppppp    llllllll   ooooooooooo     sssssssssss      sssssssssss    
#                                                           p:::::p                                                                       
#                                                           p:::::p                                                                       
#                                                          p:::::::p                                                                      
#                                                          p:::::::p                                                                      
#                                                          p:::::::p                                                                      
#                                                          ppppppppp                                                                      
    def rebote_a_la_ema(self,escala,periodos,precio=None):
        if precio == None:
            precio = self.precio
        ind=self.ind
        ema = ind.ema(escala, periodos)
        if -2 < variacion_absoluta(precio,ema) < 1:
            self.log.log("zona de rebote_a_la_ema_"+str(periodos),escala)
            return True
        else:
            return False    
    
    def rebote_al_rango_superior(self,precio=None):
        if precio == None:
            precio = self.precio
        ret = False
        try:
            var = variacion_absoluta(precio,self.rango[2])
            if -2 < var < 1:
                ret = True
        except:
            self.log.log('ERROR.rebote_al_rango_superior') 
            
        self.log.log (self.txt_resultado_filtro(ret,self.indentacion)+'rebote_al_rango_superior var=',var)
        return ret

    def rebote_al_rango_inferior(self):
        ret = False
        try:
            var = variacion_absoluta(self.precio,self.rango[0])
            if  var < -1: # el precio es mayor que el rango inferior y se acerga a éste entonces -10..-9.. -8..
                ret = True
        except:
            self.log.log('ERROR.rebote_al_rango_inferior') 
            
        self.log.log (self.txt_resultado_filtro(ret,self.indentacion)+'rebote_al_rango_inferior var=',var)
        return ret


    def calculo_stoploss_negativo(self):
        ind=self.ind
        #tomo la banda inferior de bollinger con una desviancion standar de 2.5, la desviacion por defecto es 2 lo que me asegura que 
        #la volatilidad en el precio no me afecte
        _,_,banda_inferior = ind.bollinger(self.escala_de_analisis,periodos=20,desviacion_standard=2.5,velas_desde_fin=40)

        return banda_inferior


    def calcular_stoploss(self):
        ind=self.ind
        tiempo_en_stoploss = self.calcular_tiempo_stoploss()
        self.actualizar_precio_ws()
        self.ultimo_calculo_stoploss = time.time()
        duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        escala_a_largo_plazo = self.escala_a_largo_plazo(self.escala_de_analisis,duracion_trade)

        st = self.calculo_basico_stoploss() 

        if self.stoploss_negativo == 1 and self.precio < self.precio_salir_derecho:
            return self.calculo_stoploss_negativo()

        if self.funcion=='cazaliq':
            
            if tiempo_en_stoploss > 600:
                st=self.intentar_subir_stoploss()
                self.log.log('calc.intentar_subir_stoploss',st,'tiempo',tiempo_en_stoploss) 
                return self.st_correccion_final(st)
            else:
                self.log.log('no se aplica intentar_subir_stoploss,tiempo',tiempo_en_stoploss) 
        
        
        if self.g.escala_tiempo[ escala_a_largo_plazo ]  <= self.g.escala_tiempo['2h'] : # si la escala es menor o igual 2h
            gan = self.ganancias()
            self.log.log(  self.par,"stoploss  salvar el 1%-- gan:",gan)
            if gan > 1:
                pxgan = self.calc_precio(1)
                if self.precio > pxgan + self.tickSize * 2:
                    self.log.log(  self.par,"stoploss  salvar el 1% OK")
                    st = max(pxgan,st)
        
        #    st = ind.stoploss_ema_minimos( "5m",5,1 )
        #    self.log.log('hay_que_tratar_de_tomar_ganancias-->',st) 
        #    return self.st_correccion_final(st)
        
        
        
        if self.hay_pump():
            #punto medio entre la ema minimos y el precio actual
            stx = (ind.stoploss_ema_minimos(  self.escala_de_analisis,4,1) + self.precio ) / 2
            self.log.log('calc.sl hay_pump',stx)
            st = max(stx,st)
        else:
            # se calcula un stoploss por debajo de los minimos registrados las ultimas 6 velas en una hora y sin tener en cuenta la ultima vela
            stx= round( ind.stoploss_ema_minimos(  self.escala_de_analisis,4,1) , self.moneda_precision )
            self.log.log('calc.sl ind.stoploss_ema_minimos',self.escala_de_analisis,stx)
            st = max(stx,st)

        if  st == -1 or st > self.precio:
            stx = round( ind.retroceso_macd_hist_max(self.escala_de_analisis) , self.moneda_precision)
            self.log.log('calc.sl retroceso_macd_hist_max',stx) 
            st = max(stx,st)   

        if  st > self.precio:
            px = self.libro.precio_compra_grupo_mayor() - self.tickSize 
            if px < self.precio and px > self.precio_salir_derecho + self.tickSize * 2:
                self.log.log('calc.sl precio_compra_grupo_mayor',px) 
                st = max(px,st)
            
        if self.generar_liquidez:
            #punto mendio entre el stoploss calculado y el precio actual
            #mas tick
            stx = ind.stoploss_ema_minimos( "5m",4,1 )
            self.log.log('calc.sl recalculo por general liquedez',stx) 
            if stx > self.precio:
                stx = self.precio - self.tickSize
                st = max(stx,st)    

        st =  self.st_correccion_final(st)
        
        return   st    

    def calculo_basico_stoploss(self):
        #   salir_derecho     Px1     ganancia_infima   Px2       ganancia_segura  Px3
        #........|.............|............|:..........|...........|..............|...........> precio_objetivo    
        #        |             |            |           |           |              |
        #        |...........SL.            |.........SL.           |............SL.              
        
        sl = 0
        px3 = self.ganancia_segura * 1.07
        if self.precio > px3:
            sl = self.ganancia_segura
        else:
            px2 =  self.precio_ganancia_infima + (self.ganancia_segura - self.precio_ganancia_infima ) / 2  
            if self.precio >  + px2:
                sl = px2
            else: 
                px1 =  self.precio_salir_derecho + (self.precio_ganancia_infima - self.precio_salir_derecho ) / 2   
                if self.precio > px1:
                    sl = px1

        return sl
    
    def tomar_ganancias(self,ganancias):
        px_stoploss=self.calc_precio(ganancias)
        self.log.log('px_stoploss',px_stoploss)
        self.cancelar_ultima_orden()
        respuesta=self.ajustar_stoploss( px_stoploss )
        if respuesta =='OK':
            self.log.log('tomar_ganancias ok')
        else:
            self.log.log('tomar_ganancias NO ok')

    def st_correccion_final(self,st): 
        st =  round( st , self.moneda_precision)

        if st >= self.precio:
            st=self.precio - self.tickSize

        if st < self.precio_salir_derecho:
            st = self.precio_salir_derecho
            self.log.log('corrección final st < self.precio_salir_derecho',st)
        
        return st  

    def tomar_ganancias_rsi(self,gan):
        self.log.log(f'tomar_ganancias_rsi...')
        ind: Indicadores=self.ind
        
        picos = ind.rsi_contar_picos_maximos(self.escala_de_analisis,3,67)
        self.log.log(f'picos rsi {picos}')
        return picos >0          

    def hay_que_tratar_de_tomar_ganancias(self,gan,atr):
        '''
           se analizan las condiones en la que hay que tratar de tomar ganancias 
           en funcion de la acción del precio en la escala de análisis

        '''
        #duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        #escala = self.escala_a_largo_plazo(self.escala_de_analisis,duracion_trade)
        escala = self.escala_de_analisis
        # escala = '1d' #self.escala_de_control(self.escala_de_analisis)
        
        self.log.log(f'hay_que_tratar_de_tomar_ganancias( {gan},{atr} )')

        if gan < self.calc_ganancia_minima(self.escala_de_analisis):
            return False

        rsi_min = 45

        tomar_ganancias = False 
        #tomar_ganancias = ind.rsi_baja_sin_divergencia(self.escala_de_analisis)    
        
        #tomar_ganancias =  self.tomar_ganancias_rsi(gan)   
        
        #tomar_ganancias = self.filtro_rechazo_alcista(self.escala_de_analisis) and\
        #                    self.filtro_rsi_mayor(self.escala_de_analisis,rsi_min)

        if not tomar_ganancias: 
            tomar_ganancias = self.filtro_pico_maximo_ema_maximos(escala,cvelas_subida=7,posicion_maximo=2) and\
                            self.filtro_rsi_mayor(self.escala_de_analisis,rsi_min)

        if not tomar_ganancias:  
            tomar_ganancias= gan > 1 and self.filtro_pendiente_ema_negativa(self.escala_de_analisis,20)

        if not tomar_ganancias:
            tomar_ganancias = self.filtro_rsi_mayor(self.escala_de_analisis,70) or\
                              self.filtro_rsi_mayor(self.g.zoom_out(self.escala_de_analisis,1),70)     

        return tomar_ganancias

    def calc_ganancia_minima(self,escala):
        ind:Indicadores=self.ind
        if ind.ema_rapida_mayor_lenta(escala,10,50):
            gan=.4
        else:
            gan=.2

        return gan        

    
    def escala_de_control(self,escala_actual):
        '''
        Cuando la escala es muy grande quiero quiero establecer escalas mas pequeñas para controlar
        '''
        if self.escala_de_analisis in "1w 1M":
            escala = "1d"
        else:
            escala = escala_actual

        return escala    


    def intentar_subir_stoploss(self):
        diff = self.precio -  self.stoploss_actual
        ticks = int( diff / self.tickSize * 0.20)
        if ticks >0 :
            return self.stoploss_actual + self.tickSize * ticks
        else:
            return self.stoploss_actual 

    def intentar_subir_stoploss_atr(self):
        '''
           la idea de esta funcion es mantenerse con un stoploss a una distancia prudencial del precio
           que permita seguir en el mercado sin que te saque por volatilidad
        '''
        
        ind:Indicadores=self.ind
        duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        escala = self.escala_a_largo_plazo(self.escala_de_analisis,duracion_trade)
        esc = escala
        i = 3
        nuevo_stoploss = 0

        while  nuevo_stoploss < self.stoploss_actual and esc != '1m' and  i > 1:
            atr=ind.atr(esc)
            nuevo_stoploss = self.precio - atr

            i -= 1
            esc = self.zoom(esc,1) 

        self.log.log('intentar_subir_stoploss_atr', escala,'-->',esc, nuevo_stoploss)    

        return nuevo_stoploss
    
    # def calcular_stoploss_fibo(self):
    #     for f in self.fibo:
    #         st=self.precio - Par.mo_pre.variacion_precio(self.par) * ( 1 + f ) 
    #         if self.precio_salir_derecho + self.tickSize_proteccion * 2 < st:
    #             self.log.log('calc.sl fibo',f,st) 
    #             break

    #     return st    


        
   
    def porcentaje_en_ticksize(self,valor,porcentaje):
        vporcentaje = valor * porcentaje / 100
        cant_ticks = int(vporcentaje / self.tickSize)
        if cant_ticks == 0: #corrección para que de al menos 1 tick  
            cant_ticks = 1
        return (cant_ticks * self.tickSize)    

    
    def coeficiente_temporal(self,tiempo_ganando,valor_maximo=0.8):
        ''' retorna un nro entra 0 y valor_maximo 
             t=0, ret=0 t=tiempo_maximo, ret=valor_maximo
             cuanto mas tiempo pasa mas cerca de valor_maximo es el valor que retorna
             sería algo así como un paciencia que se va perdiendo...    
        '''

        if self.shitcoin > 3:
            can=2
        else:
            can=8    

        tiempo_maximo=3600 * can
        if tiempo_ganando>tiempo_maximo:
            t=tiempo_maximo
        else:
            t=tiempo_ganando    
        
        return round( t / tiempo_maximo * valor_maximo, 4 )     
    
    def stop_positivo(self,stoploss): #clava stoploss positivo sobre todo se debe usar para shitcoins
        #ind=self.ind
        #self.tiempo_inicio_estado=time.time()
        
        coef_gm=3 * 900 / (900+time.time()-self.tiempo_inicio_estado) # coeficiente que se aproxima a cero a medida que pasa el tiempo
        
        st=stoploss
        pxseguro=self.precio/(1+self.ganancia_infima*coef_gm/100)-self.tickSize #- 0.00000001# el precio actual menos el minimo descuento posible
        gan_calculada=self.calculo_ganancias(self.precio_compra, pxseguro)
        
        self.log.log("stop_positivo: pxseguro",pxseguro,"gan_calculada",gan_calculada,"coef_gm",coef_gm,"gan.inf",self.ganancia_infima*coef_gm)

        if gan_calculada>self.ganancia_infima*coef_gm and gan_calculada<self.ganancia_segura:
            st=pxseguro
                
        return st   


    def coef_stoploss_seguro(self): #a medida que van pasando los bucles (el tiempo) se pone mas nervioso y baja las pretensiones
        if self.estado_bucles<150: 
           coef=1.02
        elif self.estado_bucles>=300 and self.estado_bucles<600:
            coef=1.015
        else:    
            coef=1.01
        return coef        


    #devuelve True cuaando hay un stoploss menor a (alguna formula en desarrolo) , muy probable que se ejecute
    # cuando lo que se busca es solamente tener una proteccion en caso de una bajada muy brusca 
    # pero el objetivo es aguantar hasta que suba evitando que una pequeña bajada nos arruine la espera.
    #todo ello siempre y cuando el stoploss no haya superado al precio_objetivo en cuyo caso
    #estamos en la ganancia esperada y todo lo que suba de aquí en mas es un regalo del cielo.
    def se_debe_actualizar_stoploss(self):
        ret=False
        if self._stoplossActivo and self.ganancias()<0 :
            if self.stoploss_actual < self.precio_objetivo and  self.precio-self.stoploss_actual < self.ind.atr('5m')*self.pstoploss:
                self.log.log(  "stoploss_muy_cercano!",self.stoploss_actual )
                ret =True
        elif self.precio<self.stoploss_actual:        
            ret=True

        return ret    

    #VENDER# Vende a precio de libro!! 

    def estado_4_inicio(self): #Vender
        self.log.log(  "Estado 4 Vender - Inicio" )
        #no persisto estado 4 en base de datos para no arrancar vendiendo por las dudas
        #self.persistir_estado_en_base_datos(self.moneda,self.moneda_contra,self.precio_compra,self.estado)
        
        self.tiempo_reposo=30 # tiempo entre accion y accion
        #por el motivo que sea hay que vender
        
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        #self.log.log('TRADE',trade) 
        if trade['idtrade'] == -1:
            self.log.log("Me mandan a vender y no hay trade previo...")
            self.enviar_correo_error('No se pudo crear orden de venta en estado_4_inicio')
            self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(5),self.moneda,self.moneda_contra)
            self.detener()
            return

        self.establecer_cantidad_a_vender(trade) #aca se fija idtrade tambien...

        self.precio_salir_derecho= self.precio_de_venta_minimo(0)

        Par.lector_precios.leerprecios()
                
        #creo la orden de venta
        self.libro.actualizar() #descargo el estado actual del libro de ordenes
        self.precio_venta=self.libro.primer_precio_venta() #5/4/2019  #-self.tickSize #le resto un tick para quedar primero en venta.
        self.cancelar_ultima_orden()
        if not self.estado_4_orden_vender():
            self.enviar_correo_error('No se pudo crear orden de venta en estado_4_inicio')
            #db.set_no_habilitar_hasta(self.calcular_fecha_futura(1),self.moneda,self.moneda_contra)
            if self.estado_anterior == 4:
                self.estado_anterior = self.primer_estado_de_funcion()
            self.iniciar_estado( self.estado_anterior )
            return

        self.bucles_partial_filled=0
        
        self.set_tiempo_reposo()
        self.reposar()


    def estado_4_accion(self): 
        self.log.log(  "Estado 4 Vendiendo - Accion" ,self.par )
        orden=self.oe.consultar_estado_orden(self.ultima_orden)
        
        if orden['estado']=='FILLED':
            self.log.log(  "FILLED (e.4.accion)" )
            self.precio_venta=orden['precio']

            #agrega al trade la cantidad vendida (ejecutada) que en este caso es el total.
            self.db.trade_sumar_ejecutado(self.idtrade,orden['ejecutado'],orden['precio'],strtime_a_fecha(orden['time']),orden['orderId'])   

            self.enviar_correo_filled_estado()
            #se vendió como se esperaba

            #calculo un precio de compra nuevo para comprar en caso de que se de la oportunidad
            #self.precio_compra=self.precio_de_recompra_minimo(self.stoploss_actual,abs(self.ganancias()))

            if self.hay_algo_para_vender_en_positivo():
                self.iniciar_estado( 3 ) #mismo estado
            else:    
                #self.dormir_un_tiempo_prudencial()
                self.iniciar_estado( self.estado_siguiente() )
            
            return

        elif orden['estado']=='CANCELED': #Se dio un caso que apareció una orden cancelada... en este caso tratamos de vender nuevamente.
            if orden['ejecutado']>0:
                self.db.trade_sumar_ejecutado(self.idtrade,orden['ejecutado'],orden['precio'],strtime_a_fecha(orden['time']),orden['orderId'])
                self.cant_moneda_compra= self.cant_moneda_compra - orden['ejecutado']
            if not self.estado_4_orden_vender():
                self.enviar_correo_error('No se pudo crear orden de venta en estado_4_accion para orden en estado == CANCELED')
                self.estado_0_inicio()
                return

        elif orden['estado']=='NEW':
            self.log.log(  "NEW, revisamos si estamo pudiendo vender..." )
            #no se vendió 
            self.libro.actualizar() #descargo el estado actual del libro de ordenes

            #si el precio de venta ofrecido ha variado, creo una nueva orden
            pxvta=self.libro.primer_precio_venta()  #5/4/2020# -self.tickSize #le resto un tick para quedar primero en venta.

            if self.vender_solo_en_positivo and pxvta < self.precio_salir_derecho*1.002:
                #no queremos vender en perdidas
                self.log.log(  "No se pude vender en positivo, volvemos a esperar..." )
                if self.cancelar_ultima_orden():
                    self.iniciar_estado( self.primer_estado_de_funcion() )
                    return
                else:
                    self.intentar_recuperar_venta()
                    return


            if pxvta != self.precio_venta:
                self.precio_venta=pxvta
                if self.cancelar_ultima_orden():
                    if not self.estado_4_orden_vender():
                        self.enviar_correo_error('No se pudo crear orden de venta en estado_4_accion para orden en estado == NEW luego de una una deteccion en el cambio de precio de venta')
                        self.iniciar_estado( self.primer_estado_de_funcion())
                        return
                else:
                    self.intentar_recuperar_venta()
                    return
        elif orden['estado']=='PARTIALLY_FILLED': #ojo hay que cancelar, y luego leer cuanto fue lo que se alanzó vender.
            self.log.log(  "bucles   =",self.bucles_partial_filled )
            self.log.log(  "ejecutado=",orden['ejecutado'] )
            if self.bucles_partial_filled>200: #15 seg cada iter, aprox 1.1 minutos
                ultima = self.ultima_orden
                if self.cancelar_ultima_orden():
                    order_cancelada=self.oe.consultar_estado_orden(ultima)
                    if order_cancelada['estado']=='CANCELED':
                        #agrega al trade la cantidad vendida (ejecutada) que en este caso es el total.
                        self.db.trade_sumar_ejecutado(self.idtrade,order_cancelada['ejecutado'],order_cancelada['precio'],strtime_a_fecha(orden['time']),orden['orderId'])
                        self.cant_moneda_compra= self.cant_moneda_compra - orden['ejecutado']
                        if not self.estado_4_orden_vender():
                            #en este caso puede ser que un resto muy pequeño de error al crear la orden por el tema del minimo requerido, pasamos al estado siguiente dejamos que fluya
                            self.iniciar_estado( self.estado_siguiente() )
                            return
                            #TODO: hay que investigar el tema del min notonial para evitar el error de la orden antes de que pase.
                    else:
                        self.enviar_correo_error('No se pudo cancelar una orden en estado_4_accion para orden en estado == PARTIALLY_FILLED')
                        self.deshabilitacion_de_emergencia()
                        return
                else:
                    self.deshabilitacion_de_emergencia()
                    return
            self.bucles_partial_filled+=1    

        self.set_tiempo_reposo()
            

    
    def deshabilitacion_de_emergencia(self,horas = 24):
        self.enviar_correo_error('deshabilitacion por '+str(horas)+ ' hrs') 
        self.db.set_no_habilitar_hasta( self.calcular_fecha_futura( 60 * horas )  ,self.moneda,self.moneda_contra)
        self.detener()


    def estado_4_orden_vender(self):         

        if self.precio_venta < self.precio_salir_derecho and self.vender_solo_en_positivo: 
            self.log.err('ERROR--> vender positivo activado y self.precio_venta < self.precio_salir_derecho')
            return False

        ret=False
        self.log.log(  "Vender:", self.cant_moneda_compra, "precio:",self.precio_venta )
        if self.monto_moneda_contra_es_suficiente_para_min_motional(self.cant_moneda_compra,self.precio_venta):
            #resultado=self.crear_orden_venta_limit(self.cant_moneda_compra,self.precio_venta) ## aca hay que ver bien cual es la cantidad de moneda que se vende, por ahora self.cant_moneda_compra que sería la misma cantidad que compré
            resultado=self.crear_orden_venta_market(self.cant_moneda_compra)          ## aca hay que ver bien cual es la cantidad de moneda que se vende, por ahora self.cant_moneda_compra que sería la misma cantidad que compré
            if resultado !='OK': # hay algo que no podemos manejar
                self.log.err("estado_4_orden_vender error:",resultado)
                self.enviar_correo_error('ERR VTA EST 4')
                self.db.set_no_habilitar_hasta( self.calcular_fecha_futura( 5 )  ,self.moneda,self.moneda_contra)
                self.detener()
            else:
                self.log.log("estado_4_orden_vender OK:")
                ret=True
        return ret    

    
    def intentar_recuperar_venta(self):
        if self.iniciar_recuperacion_luego_de_posible_venta():
            self.enviar_correo_error('RECUPERACION DE VENTA OK')
            self.iniciar_estado( self.estado_siguiente() )
        else:
            self.enviar_correo_error('REC VENTA FALLIDA, dormimos 24 hrs') 
            self.deshabilitacion_de_emergencia()
        

    def iniciar_recuperacion_luego_de_posible_venta(self):
        exito = False
        self.cancelar_todas_las_ordenes_activas()
        #cant=self.oe.tomar_cantidad(self.moneda)
        #tot=round( self.db.total_moneda_en_trades(m) ,self.cant_moneda_precision)
        
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        if trade['idtrade'] !=-1: #trade hay un trade
            ordenes = self.oe.consultar_ordenes(self.par,3)
            orden = self.encontar_orden_venta(ordenes,trade['cantidad'])
            if orden['orderId'] != -1: #encontró orden NO registrada, reciente, que conicide en cantidad y precio para el ultimo trade
                precio,ejecutado = self.precio_ejecutado(orden)
                self.db.trade_sumar_ejecutado(trade['idtrade'],ejecutado,precio,strtime_a_fecha(orden['time']),orden['orderId'])   
                exito = True
        
        return exito        

    #{'symbol': 'BTCUSDT', 'orderId': 3393217013, 'orderListId': -1, 'clientOrderId': 'y3Q7fX2YDtwQanM16ZetVD', 'price': '11793.82000000', 'origQty': '0.00090000', 'executedQty': '0.00090000', 'cummulativeQuoteQty': '10.61378100', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1603188272871, 'updateTime': 1603188272871, 'isWorking': True, 'origQuoteOrderQty': '0.00000000'}

    def precio_ejecutado(self,orden):
        ejecutado = float(orden['executedQty'])
        if orden['type'] == 'MARKET': # la ordek market no lleva precio, lo calculo a precio promedio asi:
            tot=float(orden['cummulativeQuoteQty'])
            precio= tot / ejecutado
        else: #sino saco el dato de la orden
            precio=float(orden['price'])  

        return precio,ejecutado  

    def encontar_orden_venta(self,ordenes,cant):
        orden={'orderId': -1} # orden vacía
        self.log.log('Buscando orden por cantidad=',cant)
        for o in reversed(ordenes):
            self.log.log('Orden:',o)
            time_orden=strtime_a_time(o['time'])
            if o['status']=='FILLED' and o['side'] =='SELL' and \
                orden['executedQty'] == orden['origQty'] and \
                float(orden['executedQty']==cant) and \
                calc_tiempo_segundos(time_orden,time.time()) < 1800:
                #encontramos una orden, nos aseguramos que no esté previamente registrada:
                trade=self.db.get_trade_venta_orderid(o['orderId'])
                if trade['idtrade'] == -1:
                    orden = o
                    break
        return orden      
    
    
    def intentar_recuperar_compra(self):
        if self.iniciar_recuperacion_luego_de_posible_compra():
            self.enviar_correo_error('RECUPERACION DE COMPRA OK')
            self.iniciar_estado( self.estado_siguiente() )
        else:
            self.enviar_correo_error('ERROR EN RECCOMPRA, dormimos 24 hrs') 
            self.deshabilitacion_de_emergencia()
    
    
    def iniciar_recuperacion_luego_de_posible_compra(self):
        exito = False
        self.cancelar_todas_las_ordenes_activas()
        ordenes = self.oe.consultar_ordenes(self.par,5)
        for orden in reversed(ordenes):
            if orden['status']=='FILLED' and orden['side'] =='BUY': #es una orden de compra ejecutadda
                trade=self.db.get_trade_compra_orderid(orden['orderId'])
                if trade['idtrade'] == -1: 
                    self.registrar_compra_perdida(orden)
                    exito = True
                    break
        
        return exito        
    
    def registrar_compra_perdida(self,orden):
        #ana: Analizador  =self.ana[self.par] 

        try:
            escala = self.escala_de_analisis
        except:
            escala = '1d'

        precio,ejecutado = self.precio_ejecutado(orden)   

        #r = ana.altobajo.calcular_gi_gs_tp(precio, escala)

        #self.calcular_gi_gs_tp()

        gi=self.ganancia_infima
        gs=self.ganancia_segura
        tp=self.tomar_perdidas

        #correcciones en caso de valores malos
        if gs<10:
            gs=10
        if gi<2:
            gi=gs/2
        if tp<-10:
            tp=-10 
        
        try:
            senial_entrada = self.escala_de_analisis +' '+ self.analisis_provocador_entrada+'_'+self.calculo_precio_compra
        except:
            senial_entrada = '??'

        try:
            analisis = self.texto_analisis_par()
        except:
            analisis = '??'
        

        self.log.log('persistiendo trade...')
        

        self.texto_analisis_par()

        self.db.trade_persistir(self.moneda,self.moneda_contra,escala ,senial_entrada, ejecutado ,precio ,gi,gs,tp,
                                analisis, strtime_a_fecha(orden['time']) ,orden['orderId'])

        self.log.log('enviar_correo_filled_compra recuperada...')
        self.enviar_correo_filled_compra('COMPRA RECUPERADA')
       


    #version vieja de sincronizar 
    def sincronizar_compra_venta(self):
        self.log.log("...<><><>sincronizar_compra_venta(",self.par,")<><><>...")   
        #cancelamos todo lo que esté activo por las dudas
        self.cancelar_todas_las_ordenes_activas()
        #consultamos los fondos disponibles de moneda
        if self.funcion=="comprar" or self.funcion=="vender" :
            self.establecer_precio_salir_derecho_compra_anterior() # si esl precio está muy en contra nos vamos a esperar a estado 7
            if self.calculo_ganancias(self.precio_salir_derecho_compra_anterior,self.precio)< self.e3_ganancia_recompra:
                self.iniciar_estado( 7  )
            else:
                cant=self.oe.tomar_cantidad(self.moneda)
                valor= Par.lector_precios.valor_usdt(cant,self.par)
                if valor>11: # tengo suficiente para vender
                    self.iniciar_estado(3)
                else:
                    self.iniciar_estado(7) # me pongo a esperar para comprar cuando sea el momento oportuno
        elif self.funcion=="comprar+precio":
            self.iniciar_estado( 8 ) 
             
        elif self.funcion=='cazaliq':
            self.iniciar_estado( 9 )    
        else:
            self.iniciar_estado( self.estado_siguiente() )       

        

    # regresa True si los fondos que tengo para comprar alcanzan para un self.min_notional
    def fondos_para_comprar(self):
        
        #if self.sobrecomprado():
        #    self.log.log('continuacion_alcistacomprado! No hay fondos')    
        #    return False

        cant_posible=self.calcular_cantidad_posible_para_comprar()
        
        importe_posible = self.precio * cant_posible

        self.log.log('importe posible', importe_posible ,'min_notional_compra', self.min_notional_compra)

        if (importe_posible > self.min_notional_compra):
            ret = True 
        else:
            ret = False

        return ret


    # esta funcion tendría que directamente al gestoer de posición
    # def sobrecomprado(self):
    #     '''
    #     agrega a lo transado la compra actual y calcula cuanto estaríamos invertido
    #     '''
    #     esta_compra =  self.precio_compra * self.cant_moneda_compra
    #     if self.moneda_contra == 'USDT':
    #         transado = self.g.usdt_transado + esta_compra
    #         invertido =  transado / (transado + self.g.usdt_operable) 
    #         if invertido > self.g.max_inversion_usdt:
    #             return True
    #     elif self.moneda_contra == 'BTC':
    #         transado = self.g.btc_transado + esta_compra
    #         invertido =  transado / (transado + self.g.btc_operable) 
    #         if invertido  > self.g.max_inversion_btc:
    #             return True
    #     else:
    #         return False          

    def calcular_cantidad_posible_para_comprar(self):
        #en el caso que precio de compra sea 0, lo calculamos acá, esto es para salvar un división por cero que se produce en una llamada de auto_compra_vende  
        if self.precio_compra==0: 
            self.precio_compra=self.precio #self.calcular_precio_de_compra()


        self.cargar_parametros_json() #actualizo 
        #cant_disponible=self.tomar_cantidad_disponible(self.moneda_contra)
        cant_total=self.oe.tomar_cantidad_disponible(self.moneda_contra)
        #pxbtc=self.ind["BTCUSDT"].precio('1m') # precio del btc en DollarTeter
        #self.log.log('self.reserva_btc_en_usd=',self.reserva_btc_en_usd)

        if self.moneda_contra=='BTC':
            reserva_btc_global=Par.lector_precios.valor_btc(self.reserva_btc_en_usd,'BTCUSDT')
            reserva_btc_trades=0#comentado por que uso cantidad disponible #self.db.trade_btc_tradeando()
            self.log.log(self.moneda_contra,cant_total)     
            self.log.log('reserva_btc_global',reserva_btc_global) 
            #self.log.log('reserva_btc_trades',reserva_btc_trades)   
            
            cant= cant_total - reserva_btc_global * (1 - self.uso_de_reserva)  - reserva_btc_trades
            
        elif self.moneda_contra=='USDT':
            cant= cant_total - self.reserva_usdt * (1 - self.uso_de_reserva)

        else:
            cant= cant_total 
        
        cant_posible=float( self.format_valor_truncando( cant / self.precio_compra,self.cant_moneda_precision) )    
        return cant_posible
 
    
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
    
    
    
    
    def calcular_cantidad_a_comprar(self):
         
        self.precio_compra=self.calcular_precio_de_compra()

        
        #self.log.log('parametro_cantidad=',self.format_valor_truncando(self.parametro_cantidad,self.cant_moneda_precision) )   

        if self.parametro_cantidad>0:
            cant_en_moneda_contra=Par.lector_precios.convertir(self.parametro_cantidad,'USDT',self.moneda_contra)   
            cantidad_a_comprar=Par.lector_precios.unidades_posibles(cant_en_moneda_contra,self.par)
        else:
            cantidad_a_comprar=0   

        #self.log.log('cantidad_a_comprar=',self.format_valor_truncando(cantidad_a_comprar,self.cant_moneda_precision))    

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
    
      


    def establecer_cantidad_a_comprar(self):
        #self.parametro_cantidad está expresado en dolar o establecoin

        cantidad_a_comprar=self.calcular_cantidad_a_comprar()
       
        #si no me alcanza lo que tengo, compro lo que puedo.
        cant_posible=self.calcular_cantidad_posible_para_comprar()
        self.log.log('cant_posible',cant_posible)

        if cant_posible < cantidad_a_comprar: # si la cantidad de Unidades Posibles es menor que la cantidad parametrizada de unidades a comptrar
            #como la plata no alcanza y probablemente está subiendo
            #establezco la cantidad posible menos la cantidad que puedo comprar con 2 tick
            self.cant_moneda_compra=cant_posible     
        else:
            self.cant_moneda_compra=cantidad_a_comprar    #establezco la cantidad a lo calculado

        #redondeo la cantidad a la presicion de la moneda
        self.cant_moneda_compra=float( self.format_valor_truncando(self.cant_moneda_compra,self.cant_moneda_precision) )    

        #correccion en caso que le falta para llegar al min_notional
        if self.cant_moneda_compra * self.precio_compra < self.min_notional_compra:
            
            compensacion =  1/10**self.cant_moneda_precision

            self.cant_moneda_compra += compensacion # le agrego el poquito que trunqueé
            # dif = self.min_notional_compra - self.cant_moneda_compra * self.precio_compra

            # cant=   dif / self.precio_compra

            # if x_dif_truncado == 0 : #and self.cant_moneda_precision == 0: # si los dos son sero no podemos llegar al min_notional, metemos 1 a truncado
            #     x_dif_truncado = 1
            
            # self.cant_moneda_compra +=  x_dif_truncado * self.tickSize
            self.log.log(' < self.min_notional_compra',self.cant_moneda_compra ,' se sumó',compensacion)

        self.log.log('establecer_cantidad_a_comprar=',self.cant_moneda_compra)    

    def fmt(self,valor):
        return self.format_valor_truncando( valor , 8)
    







    def establecer_cantidad_a_vender(self,trade):
        cant=self.oe.tomar_cantidad(self.moneda)  ## probablemente hay que cambiar esta funcion por tomar_cantidad_disponible() pero no estoy seguro ... razonar cuendo esté siguiendo este tema.
        if cant <= 0: # no hay nada que vender
            self.cant_moneda_compra=0
            txt_error="estado_3_orden_vender error: establecer_cantidad_a_vender.oe.tomar_cantidad=0, no hay nada para vender"
            self.log.err(txt_error)
            self.enviar_correo_error(txt_error)
            self.db.set_no_habilitar_hasta( self.calcular_fecha_futura( 1440 ) ,self.moneda,self.moneda_contra)
            self.detener()

        cant=cant - self.cantidad_de_reserva
        #tomo solo la cantidad que corresponde con el ultimo trade realizado, el de precio mas pequeño
        # se tratará te tomar ganancia sobre ese trade en esa cantidad
        # si hemos comprado mas caro en otro trade, se venderá cuando sea el momento
       
        #self.log.log('get_trade_menor_precio',trade)
        self.idtrade=trade['idtrade'] #este dato es de *suma importancia* para actualizar el trade en caso de vender
        self.fecha_trade=trade['fecha'] 
        cant_ultimo_trade=trade['cantidad'] - trade['ejecutado']
        self.precio_compra=trade['precio']
        self.escala_de_analisis=trade['escala']
        self.senial_entrada=trade['senial_entrada']
        self.ganancia_infima=trade['ganancia_infima']
        self.ganancia_segura=trade['ganancia_segura']
        self.tomar_perdidas=trade['tomar_perdidas']

        if 'cazb' in trade['senial_entrada']:
            self.metodo_compra_venta='cazabarridas'

        #self.log.log('ganancia_infima',self.ganancia_infima,type(self.ganancia_infima))
        #self.log.log('ganancia_segura',self.ganancia_segura)
        #self.log.log('precio_compra',self.precio_compra)

        #deprecated#         self.set_ganancia_infima_segura_perdidas(p['ganancia_infima'],p['ganancia_segura'],0)
        
        
        if cant_ultimo_trade>0 and (cant - cant_ultimo_trade) >  self.cantidad_de_reserva:
            self.cant_moneda_compra=cant_ultimo_trade
        else:
            self.cant_moneda_compra=cant-self.cantidad_de_reserva
        
    def precio_de_venta_minimo(self,pganancia,pcosto=None):
        
        if pcosto is None:
            costo=self.precio_compra
        else:
            costo=pcosto    
        
        coef=(1+self._fee)/(1-self._fee)
        ret=costo*coef*(1+pganancia/100)+self.tickSize #acá sí va tickSize
        
        return round( ret , self.moneda_precision)    

    def precio_de_venta_especulado(self,costo,porcentaje_ganancia=0,cantidad_ganancia=0):
        '''
        calculo de un precio de venta a partir de un costo + una ganancia en porcentaje + una ganancia en cantidad fija
        '''
        coef=(1+self._fee)/(1-self._fee)
        ret=costo*coef*(1+porcentaje_ganancia/100)+cantidad_ganancia+self.tickSize #acá sí va tickSize
        return round( ret , self.moneda_precision)      


    def establecer_precio_salir_derecho_compra_anterior(self):
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        self.precio_salir_derecho_compra_anterior=self.precio_de_venta_minimo(0,trade['precio'])
        self.cantidad_compra_anterior =trade['cantidad']
        self.log.log('set--->precio_salir_derecho_compra_anterior',self.precio_salir_derecho_compra_anterior,type(self.precio_salir_derecho_compra_anterior))
   
    def ganancias_compra_anterior(self):
        trade=self.db.get_trade_menor_precio(self.moneda,self.moneda_contra)
        if trade['idtrade']>0:
            gan=self.calculo_ganancias(trade['precio'],self.precio)
            ret= {'idtrade':trade['idtrade'] ,'gan':gan}
        else:    
            ret={'idtrade':-1,'gan':0}
        
        return ret
    



    
    def hay_suficiente_para_vender(self):
        ret=False
        disponible=self.oe.tomar_cantidad_disponible(self.moneda)  ## probablemente hay que cambiar esta funcion por tomar_cantidad_disponible() pero no estoy seguro ... razonar cuendo esté siguiendo este tema.
        cant=disponible-self.cantidad_de_reserva
        if cant * self.precio > self.min_notional: # hay  suficiente generar un min notional
            ret=True
        return ret     
    
    
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

        titulo=self.par+' [Estado '+ str(self.estado)+'] '+sgan+ f' % {self.escala_de_analisis}'
        texto=titulo+'\n'
        texto+=" Precio Compra: " + self.format_valor_truncando( self.precio_compra,8) + '\n'
        texto+=" Precio  Venta: " + self.format_valor_truncando( self.precio_venta,8) +" "+ sgan+ ' %  '+gan_moneda_contra +' m$c ' +ganusdt +' usdt\n'

        self.log.log(texto)
        self.log_resultados.log(texto)

        #2/9/2019 no persisto mas esto se deduce de los trades
        #persistir en la base.       
        #cant=self.tomar_cantidad(self.moneda) 
        #self.db.persistir_ganancias(ganusdt,self.moneda,self.moneda_contra)

        #cálculo y retroalimientacion de shitcoin
        self.retroalimentacion_shitcoin(gan)

        texto+= self.log.tail()
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)
        return


    def retroalimentacion_shitcoin(self,gan): #gan ganancias como resultado compra - ventas - fees en %
        shitcoin=self.shitcoin
        if gan<=-2:
            shitcoin = shitcoin + 1
        elif gan>=20:
            shitcoin = shitcoin -1
            if self.shitcoin==1 and shitcoin<1:
                shitcoin=1 # la moneda que es shitcoin, lo seguirá siendo. no se sali de shitcoin en forma automática
        self.db.persistir_shitcoin(shitcoin,self.moneda,self.moneda_contra)



    def enviar_correo_filled_compra(self,txt_filled):
       

        
        titulo=self.par+ ' Ent.' + txt_filled + ' ' +self.analisis_provocador_entrada+'_'+self.calculo_precio_compra
        texto=titulo+'\n'
          

        #texto+=self.texto_analisis_moneda() #esto etaba matando el envío del mail que rápidamente se tiene que poner a vender
        
        self.log.log(texto)
        texto+=self.log.tail()        
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)

        
        return

    def enviar_correo_gogogo(self):
       

        
        titulo=self.par+ ' gogo.' 
        texto=titulo+'\n'

        #texto+=self.texto_analisis_moneda() 
        
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


    def enviar_correo_senial_8(self):
        
        #lo deshabilito
        return

        if time.time()-self.hora_ultima_senial<900: #evita mandar correos de señales demasiado seguido
            return

        titulo=self.par+' Señal e8' 
        texto=titulo+'\n'
          
        texto+=self.texto_analisis_moneda()  
        
        self.log.log(texto)

        texto+=self.log.tail()         
        correo=Correo(self.log)
        correo.enviar_correo(titulo,texto)

        self.hora_ultima_senial=time.time()
        return

    def texto_analisis_moneda(self):
        
        ind=self.ind
                     
        texto="Analisis "+self.par+"\n"

        #if ind.esta_subiendo2('1m'):
        #    texto+=self.linea('1m Subiendo2')

        #if ind.esta_subiendo2('5m'):
        #    texto+=self.linea('5m Subiendo2')
            
        #if ind.esta_subiendo2('15m'):
        #    texto+=self.linea('15m Subiendo2')

        #if ind.esta_subiendo2('1h'):
        #    texto+=self.linea('1h Subiendo2')    

        #if ind.esta_subiendo2('4h'):
        #    texto+=self.linea('4h Subiendo2')    
        
        #if ind.esta_subiendo4('1m'):
        #    texto+=self.linea('1m Subiendo4')

        #if ind.esta_subiendo4('5m'):
        #    texto+=self.linea('5m Subiendo4')
            
        #if ind.esta_subiendo4('15m'):
        #    texto+=self.linea('15m Subiendo4') 

        #if ind.esta_subiendo4('1h'):
        #    texto+=self.linea('1h Subiendo4')

        #if ind.esta_subiendo4('4h'):
        #    texto+=self.linea('4h Subiendo4')    

        #if ind.volumen_bueno5('1m',self.incremento_volumen_bueno):
        #    texto+=self.linea('1m Volumen Bueno: ', ind.volumen_porcentajes('1m'))

        #if ind.volumen_bueno5('5m',self.incremento_volumen_bueno):
        #    texto+=self.linea('5m Volumen Bueno: ',ind.volumen_porcentajes('5m'))
        
        #if ind.volumen_bueno5('15m',self.incremento_volumen_bueno):
        #    texto+=self.linea('15m Volumen Bueno: ',ind.volumen_porcentajes('15m'))
        
        #if ind.volumen_bueno5('1h',self.incremento_volumen_bueno):
        #    texto+=self.linea('1h Volumen Bueno: ',ind.volumen_porcentajes('1h'))

        #if ind.volumen_bueno5('4h',self.incremento_volumen_bueno):
        #    texto+=self.linea('4h Volumen Bueno: ',ind.volumen_porcentajes('4h'))

        texto+=self.linea( 'RSI 15m :', round(ind.rsi('15m'),2)  )    
        texto+=self.linea( 'RSI 1h  :', round(ind.rsi('1h') ,2)  )    
        texto+=self.linea( 'RSI 4h  :', round(ind.rsi('4h') ,2)  )    
        texto+=self.linea( 'RSI 1D  :', round(ind.rsi('1d') ,2)  )
        texto+=self.linea( 'RSI 1S  :', round(ind.rsi('1w') ,2)  )

        #texto+=self.linea( 'ADX 5m  :', ind.adx('5m')  )    
        #texto+=self.linea( 'ADX 15m :', ind.adx('15m')   )    
        #texto+=self.linea( 'ADX 4h  :', ind.adx('4h')   )    
        #texto+=self.linea( 'ADX 1D  :', ind.adx('1d')   ) 
        #texto+=self.linea( 'ADX 1S  :', ind.adx('1w')   ) 

        
        
        texto+=self.linea( "Act.Px    :", Par.mo_pre.comparar_actualizaciones(self.par,'BTCUSDT') )
        

        texto+="=== Fin Analisis ==="+self.par+"\n"


    def texto_analisis_par(self):
        escalas=['15m','1h','2h','4h','1d','1w']
        ind=self.ind
        texto=''  
        return texto


        #amputada          
        
        # texto+='pendiente_positiva_ema 55: '
        # for esc in escalas:
        #     texto+=self.lin(  esc ,  ind.pendiente_positiva_ema(esc,55)  )  
        
        # texto+='~EMA 10,55: '
        # for esc in escalas:
        #     texto+=self.lin(  esc ,  self.filtro_ema_de_tendencia(esc,10,55)  )    

        # texto+='~busca_macd_hist_min: '
        # for esc in escalas:
        #     texto+=self.lin(  esc , ind.busca_macd_hist_min(esc)  )    
        
        # texto+='~RSI: '
        # for esc in escalas:
        #     texto+=self.lin(  esc ,round(ind.rsi(esc),2)  )    

        # texto+='~ADX: '
        # for esc in escalas:
        #     texto+=self.lin(  esc , ind.adx(esc)   )    

        # return texto 

    def texto_analisis_moneda_e3(self):
        
        ind=self.ind
                     
        texto="Analisis "+self.par+"\n"

        texto+=self.txt_precio_y_stoploss()
        
        #texto+=self.linea( "PX WS     :", Par.mo_pre.precio(self.par) )
        texto+=self.linea( "% Gan.Inf.:", self.ganancia_infima  )
        texto+=self.linea( "% Gan.SEg.:", self.ganancia_segura  )
        texto+=self.linea( "% Tom.Per.:", self.tomar_perdidas )    
        texto+=self.linea( "P Gan.Inf.:", self.format_valor_truncando( self.precio_salir_derecho * ( 1 + self.ganancia_infima/100)  ,8 ) )
        texto+=self.linea( "P Gan.Seg.:", self.format_valor_truncando( self.precio_salir_derecho * ( 1 + self.ganancia_segura/100)  ,8 ) )
        texto+=self.linea( "P Sal.Der.:", self.format_valor_truncando( self.precio_salir_derecho,8)  )
        texto+=self.linea( "SDer+2*Tz.:", self.format_valor_truncando( self.precio_salir_derecho + self.tickSize_proteccion * 2,8)  )
        texto+=self.linea( "Tz.Protec.:", self.format_valor_truncando( self.tickSize_proteccion,8)  )
        texto+=self.linea( "Objetivo  :", self.format_valor_truncando( self.precio_objetivo,8)  )
        texto+=self.linea( "Stop.Loss.:", self.format_valor_truncando( self.stoploss_actual ,8 )  , self.calculo_ganancias( self.precio_compra, self.stoploss_actual)     )
        texto+=self.linea( "Cant.Vend.:", self.format_valor_truncando( self.cant_moneda_compra ,8 ) )
        texto+=self.linea( "idtrade   :", self.idtrade )

        #texto+=self.linea( 'Cache     :')
        #texto+=self.linea( ind.cache_txt())
        #texto+=self.linea( ind.mercado.get_panda_df(self.par,'5m',10).tail() )
        #texto+=self.linea( ind.mercado.get_panda_df(self.par,'15m',10).tail() )


     
        texto+="=== Fin Analisis ==="+self.par+"\n"
        return texto  


    def texto_sar(self,escala):
        sar=  self.ind.sar(escala)  
        txt = 'SAR '+ escala
        txt = txt.ljust(8)+':'
        if sar > self.precio:
            hubicacion=' arriba'
        else:
            hubicacion=' abajo'
        txt+=self.format_valor_truncando( sar  ,8 ) + hubicacion

        return txt




    def txt_precio_y_stoploss(self):
        try:
            if self.stoploss_habilitado==1:
                st='sl'
            else:
                st='--'    
                
            #stop_loss_calculado=self.calcular_stoploss()
            
            tiempo_trade=self.calc_tiempo_trade()

            st+=' ' + tiempo_trade # + ' ' + str(round(self.pstoploss,2))

            return self.linea( f"Px: {self.format_valor_truncando( self.precio,8)}  {self.ganancias()} {st} {self.escala_de_analisis} " )    
        except Exception as e:
            return str(e)   
    
    def calc_tiempo_trade(self):   
        try:
            tiempo_trade=datetime.now().replace(microsecond=0) - self.fecha_trade
            tiempo_trade=str(tiempo_trade.days)+'d '+str(divmod(tiempo_trade.seconds,3600)[0])+'h '+str(divmod(tiempo_trade.seconds,60)[0])+'m'
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




    #esta funcion deberia ser elimindada
    def _deprecated_encolar_mensaje(self,*args):
        linea = ' '.join([str(a) for a in args])
        self.cola_mensajes.append(linea)

    
    def imprimir(self):
        self.log.log(self.txt_llamada_de_accion+'imprimir')

        #print ("~~~~~~~~",self.bucle,datetime.now(),"~~~~~~~~")
        #for m in (self.cola_mensajes):
        #    self.log.log(m)
        
        #self.log.log("imprimir()... inicio")

        if self.estado==3:
            #ind=self.ind
            texto = self.texto_analisis_moneda_e3()
            self.log.log( texto )
        
        #self.indicandor_en_estudio('1m')
        #self.indicandor_en_estudio('5m')
        #self.indicandor_en_estudio('15m')
        

        self.log.log("imprimir()... fi")    

        
        #self.cola_mensajes=[]  

    def indicandor_en_estudio(self,escala):
        ind=self.ind
        atr1=ind.atr(escala,1)
        atr0=ind.atr(escala,0)
        self.log.log( 'ind_estudio_atr'+escala+' 1 0 ',round(atr1/atr0,2),atr1,atr0)





    def imprimir_estado_par_en_compra(self):
        ind=self.ind
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

    def simbolo_hay_moneda(self):
        if self.cant_moneda>0:
            return '(ooo)'
        else:
            return '(---)' 


