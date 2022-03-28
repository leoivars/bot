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
from libro_ordenes2 import Libro_Ordenes_DF
from datetime import datetime, timedelta
from comandos_interprete import ComandosPar

from ordenes_binance import OrdenesExchange
from actualizador_info_par import ActualizadorInfoPar
from funciones_utiles import calcular_fecha_futura, cpu_utilizada,calc_tiempo_segundos,strtime_a_fecha,strtime_a_time,variacion,variacion_absoluta
from controlador_de_tiempo import *
from variables_globales import Global_State
from calc_px_compra import Calculador_Precio_Compra
from intentar_recuperar_venta_perdida import intentar_recuperar_venta_perdida
from fpar.ganancias import calc_ganancia_minima, calculo_ganancias
from mercado import Mercado

from fpar.filtros import filtro_parte_baja_rango, filtro_zona_volumen, filtro_pendientes_emas_positivas,filtro_parte_alta_rango
from fpar.filtros import filtro_pico_minimo_ema_low,filtro_velas_de_impulso,filtro_dos_emas_positivas
from fpar.filtros import filtro_xvolumen_de_impulso,filtro_de_rsi_minimo_cercano,filtro_ema_rapida_lenta,filtro_rsi
import fauto_compra_vende.habilitar_pares
from acceso_db_funciones import Acceso_DB_Funciones
from acceso_db_modelo import Acceso_DB


from numpy import isnan
import random

#from termcolor import colored #para el libro de ordenes
from acceso_db_modelo import Acceso_DB
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
    escalas=('1h','2h','4h','1d','1w','1M')
    txt_llamada_de_accion='accion---->'

    def __init__(self, client,moneda,moneda_contra,pool,obj_global,mercado): 
        #variables de instancia
        self.par=moneda+moneda_contra
        
        self.g: Global_State = obj_global
        self.estoy_vivo=True # Se usa para detectar cuando la instancia no tiene nada mas que hacer, se elimina de la memoria.
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
        
        self.stoploss_actual=0 

        self.senial_compra=False # se pone True cuando necesita Comprar


        self.log=Logger(self.par.lower()+'.log') #objeto para loguear la salida de esta clase a un archivo específico como es multihilo por separado
        self.log.loguear=True #False-->solo loguea log.err 
        
        self.ind:Indicadores =Indicadores(self.par,self.log,obj_global,mercado)
        self.mercado:Mercado =mercado
        
        self.libro=LibroOrdenes(client,moneda,moneda_contra,25) #cleación del libro
        self.cola_mensajes=[]
        
        self.bucle=0 #contador general de bucles realziados por el par
        
        self.hora_ultima_senial=0
        
        fxdb=Acceso_DB_Funciones(self.log,pool)       #paso el pool directamente en vez del conn.pool ojo 
        self.db = Acceso_DB(self.log,fxdb)
        
        self.comandos=ComandosPar(self.log,self.db,self)   #self: le paso la instancia mima del para para que lo pueda manipular
        
        if Par.lector_precios == None:
            Par.lector_precios=LectorPrecios(self.client)

        

        self.reserva_btc_en_usd=50 # cantidad expresada en dolares que se deja como reserva de inversion. Se carga con cargar_parametros_json() y se usa en fondos_para_comprar
        self.reserva_usdt=50
        
        self.tiempo_reposo=30 

         

        self.trabajando=True

        self.tendencias=[]
        self.veces_tendencia_minima=3
        
        
        self.vender_solo_en_positivo=True

        self.bucles_partial_filled=0

        self.forzar_sicronizar=False
        
        self.stoploss_habilitado=0     # indica si está habilitado el stoploss. Hay una orden de stoploss activada.
        
        self.stoploss_negativo=0# si está en 1, se permite poner stoploss negativos

        
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
        
        self.uso_de_reserva=0 # algunas monedas pueden usar una parte de las resevas este es un nro entre 0...1

        #con esto me aseguro que to estblezcan los valores iniciales del par
        #self.cargar_parametros_iniales()
    

        self.volumen=0 # el volumen del par, calculado en calcular valores que cambian poco y guardado en los datos del par

        #escala o temporalidad en la que se realiza el análisis de momento para dejarla cuardada en la entrada del trade como
        #para en qué temporalidad somos mas efectivos
        #tambien estoy pensando en poner mas lejanos en escalas grandes y mas ajustadon en escalas chicas
        self.escala_de_analisis='15m' 

        self.escala_de_salida='1m'

        self.oe = OrdenesExchange(self.client,self.par,self.log,obj_global)
        
        #self.actualizador = ActualizadorInfoPar(conn, self.oe ,self.log) #13/9/2021 no actualizamo  mas por ahora 


        

        
        #par,g: Global_State,log:Logger,ind_par
        self.libro2=Libro_Ordenes_DF(client,moneda,moneda_contra,25) #cleación del libro
        self.calculador_precio = Calculador_Precio_Compra(self.par,self.g,self.log,self.ind,self.libro2)

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


    def persistir_estado_en_base_datos(self,moneda,moneda_contra,precio,estado):

        self.db.persistir_estado(moneda,moneda_contra,float(precio),estado,self.funcion)


    #esta funciona se usa para cargar parámetros generales de todos los pares
    #que no estarán en la base de datos
    # ahora almacenandos en el obj global
    def cargar_parametros_json(self):

        self.reserva_btc_en_usd= self.g.reserva_btc_en_usd
        self.x_min_notional=self.g.x_min_notional
        
        if self.moneda_contra=='USDT':
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
        
        self.xobjetivo=p['xobjetivo']
        
        self.uso_de_reserva=p['uso_de_reserva']
        self.temporalidades=p['temporalidades'].split()
        self.max_entradas = p['max_entradas']
        
        cant=float(p['cantidad'])
        
        if cant>0:
            Par.lector_precios.usdt_cantidad(cant,self.par) #cantidad a comprar expresado en dolares
        
        #self.agregar_analizador('BTCUSDT') #lo mismo para este.

        #self.agregar_indicador(self.par,self.log)
        ind=self.ind
        #self.agregar_analizador(self.par)
        

        #como tomar cantidad pone en cero los trades en caso
        #de no tener nada, lo ejecuto aca para empezar 
        #sin trades en diccho caso.
        self.oe.tomar_cantidad(self.moneda)

        self.estado=-1 #-1 obliga a cargar el estado inicial de la funcion #p['estado']
        if p['estado']==4: #nunca empezamos vendiendo
            self.set_estado(-1)
        else:
            self.set_estado(p['estado'])


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
        
        if self.moneda_contra!='BTC': #para btc este dato se autoactualiza 
            self.cantidad_de_reserva=p['cantidad_de_reserva']
        self.xobjetivo=p['xobjetivo']
        

        self.e3_ganancia_recompra=p['e3_ganancia_recompra']  
        
        self.temporalidades=p['temporalidades'].split()
        self.max_entradas = p['max_entradas']
        self.uso_de_reserva=p['uso_de_reserva']

        self.objetivo_compra  = p['objetivo_compra']
        self.objetivo_venta   = p['objetivo_venta']
        
        self.xmin_impulso   = p['xmin_impulso']
        self.param_filtro_dos_emas_positivas   = ( p['param_filtro_dos_emas_positivas_rapida'], p['param_filtro_dos_emas_positivas_lenta'])
        
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
        return Par.lector_precios.valor_usdt(cant_final,self.par)

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
            self.db.trade_persistir(self.moneda,self.moneda_contra,self.escala_de_analisis,  self.analisis_provocador_entrada+'_'+self.calculo_precio_compra,float(orden['executedQty']),float(orden['price']),self.objetivo_venta,2,4,-4,self.texto_analisis_par(),strtime_a_fecha(orden['time']),orden['orderId'])
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
            for ana in ["ema_rapida_lenta_xvolumen","minimo_ema","vela_martillo_importante","patron_"]:
                if ana in self.analisis_provocador_entrada: # esto es viejo --> in "buscar_ema_positiva buscar_rebote_rsi":
                    metodo="market"
                    listo=True 
                    break

        if not listo:
            for ana in ['parte_muy_baja']:
                if ana in self.analisis_provocador_entrada: # esto es viejo --> in "buscar_ema_positiva buscar_rebote_rsi":
                    metodo="market" #metodo="libro_grupo_mayor"
                    listo=True 
                    break     

        if not listo:
            for ana in ['scalping_parte_muy_baja']:
                if ana in self.analisis_provocador_entrada: # esto es viejo --> in "buscar_ema_positiva buscar_rebote_rsi":
                    metodo="scalping"
                    listo=True 
                    break         
 
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
        self.tiempo_inicio_estado =  time.time()
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
            self.log.log(self.par,self.escala_de_analisis,self.analisis_provocador_entrada,f"px {self.precio} |||||XXXXXX|||||> Todo es Positivo, pero no hay fondos")
            self.estado_7_no_comprar()
                
    
    def estado_7_no_comprar(self):
        # si no compramos, controlamos si en necesario un cambio de estado.
        self.log.log(self.par,"----NO compramos----")
        self.trade_anterior_cerca_entonces_vender()  
        
        dormir=False
        if self.estado!=3:
            entradas = self.db.trades_cantidad(self.moneda,self.moneda_contra)
            if entradas==0:
                if self.db.trades_cantidad_de_pares_con_trades() >= self.g.maxima_cantidad_de_pares_con_trades:
                    self.log.log(f'maxima_cantidad_de_pares_con_trades superada: A dormir')  
                    dormir = True 
                if time.time() - self.tiempo_inicio_estado >  86400:     #  un día
                    self.log.log(f'mucho tiempo sin conseguir entradas ')  
                    dormir = True

            if dormir:
                minutos = self.g.horas_deshabilitar_par * 60 + random.randint(0, 45)
                self.db.set_no_habilitar_hasta(self.calcular_fecha_futura( minutos ),self.moneda,self.moneda_contra)            
                self.detener()

                
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
        if self.precio_salir_derecho_compra_anterior>0:
            variacion_pxant_px= variacion_absoluta(self.precio_salir_derecho_compra_anterior,self.precio)
            self.log.log(  "precio_salir_derecho_compra_anterior",self.precio_salir_derecho_compra_anterior,variacion_pxant_px)
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
        entradas = self.db.trades_cantidad(self.moneda,self.moneda_contra)
        
        if entradas >= self.max_entradas:      #ya tengo las entradas configuradas, no hago mas entradas
            self.log.log(f'entradas {entradas}, max_entradas {self.max_entradas}')
            return False
        
        if entradas==0 and self.db.trades_cantidad_de_pares_con_trades() >= self.g.maxima_cantidad_de_pares_con_trades:
            self.log.log(f'maxima_cantidad_de_pares_con_trades superada')  
            return False 

        if self.no_se_cumple_objetivo_compra():
            return False

        
        comprar= False
        escalas_a_probar = self.entradas_a_escalas(self.temporalidades,entradas)
        
        for esc in escalas_a_probar:
            # if not comprar: #and self.moneda!='BTC':
            #     ret = self.buscar_minimo_parte_muy_baja('1h',90,0.25)
            #     if ret[0]:
            #         self.escala_de_analisis = ret[1]
            #         self.sub_escala_de_analisis = ret[1]
            #         self.analisis_provocador_entrada=ret[2]
            #         comprar = True
            #         break
            if not comprar: #and self.moneda=='BTC':
                ret = self.ema_rapida_lenta_xvolumen('1h',p_xmin_impulso=self.xmin_impulso,em12=self.param_filtro_dos_emas_positivas)
                if ret[0]:
                    self.escala_de_analisis = ret[1]
                    self.sub_escala_de_analisis = ret[1]
                    self.analisis_provocador_entrada=ret[2]
                    comprar = True
                    break      
   
        if not comprar and entradas==0 and time.time() - self.tiempo_inicio_estado > 7200: # no está comprando, detengo el para para probar otro
            self.db.set_no_habilitar_hasta(self.calcular_fecha_futura(7200),self.moneda,self.moneda_contra)
            self.detener()
            
        return comprar  

    def filtro_parte_alta_rango(self,escala,cvelas):
        minimo,maximo = self.ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
        minimo_venta = maximo - (maximo - minimo) *.3
        ret = self.precio > minimo_venta
        self.log.log( f'parte_alta_rango min {minimo_venta} px {self.precio} {ret}'  )
        return ret 
    
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

    def no_se_cumple_minimo_local(self,escala):
        '''
          retorna True si el precio está por encima del minimo local 
        '''
        ret = False
        ind: Indicadores =self.ind
        px_minimo_local=ind.minimo_por_rsi(escala)
        if self.precio>px_minimo_local:
            ret = True
            self.log.log(f'Precio > que minimo local={px_minimo_local}')
        return ret    
    
    
    def no_se_cumple_objetivo_compra(self):

        '''
        si self.objetivo_compra>0 controlo que el precio esté por debajo caso contrario no se controla
        ''' 
        ret = False     
        if self.objetivo_compra>0:
            if self.precio > self.objetivo_compra:
                ret=True
                self.log.log(f'precio {self.precio} > {self.objetivo_compra} objetivo_compra')
        return ret    





    def no_se_cumple_objetivo_venta(self):
        '''
        si self.objetivo_venta>0 controlo que el precio esté por encima caso contrario no se controla
        si el precio < objetivo_venta no se cumple = True
        ''' 
        ret = False     
        if self.objetivo_venta_trade>0:
            if self.precio < self.objetivo_venta_trade:
                ret=True
                self.log.log(f'precio {self.precio} < {self.objetivo_venta_trade} objetivo_venta')
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

    def buscar_rsi_minimo_subiendo(self,escala): 
        ret=[False,'xx']
        ind: Indicadores = self.ind
        
        if ind.ema_rapida_mayor_lenta('4h',9,20,0.1):
            cvelas= 75
            rsi_para_comprar=50 
        else:
            cvelas= 190
            rsi_para_comprar=33 

        if not self.hay_precios_minimos(cvelas,escala):
            return ret       
        
        #px_minimo_local=ind.minimo_por_rsi(escala,cvelas)
        if self.entrada_por_regreso_rsi(escala,cvelas,rsi_para_comprar):
            if self.entrada_por_regreso_rsi('1m',cvelas,rsi_para_comprar):
                if self.filtro_pico_minimo_ema_low('1m'):
                    ret = [True,escala,'buscar_rsi_minimo_subiendo']
    
        self.log.log('---fin---buscar_rsi_minimo_subiendo-----')    


        return ret  

    def entrada_por_regreso_rsi(self,escala,cvelas,rsi_para_comprar,volumen_de_entrada=2):
        ind: Indicadores = self.ind
        ret = False
        
        px_minimo_local=ind.minimo_x_vol(escala,cvelas,5) 
        self.log.log(f'--> minimo_x_vol {escala} {px_minimo_local} cvelas={cvelas}')
        if px_minimo_local is None:
            return False

        rsi_min, pos_rsi_min, precio_rsi_min,rsi = ind.rsi_minimo_y_pos(escala,2)
        self.log.log('---> rsi_minimo_y_pos',rsi_min, pos_rsi_min, precio_rsi_min,rsi)
    
        if precio_rsi_min <= px_minimo_local and\
               pos_rsi_min >0 and rsi_min < rsi_para_comprar and\
               rsi_min < rsi and\
               rsi < 50:
        
            if self.filtro_volumen_encima_del_promedio(escala,4,volumen_de_entrada,pos_rsi_min):
                ret = True   

        return ret    

    def buscar_rsi_minimo_subiendo_alcista(self,escala): 
        ret=[False,'xx']
        ind: Indicadores = self.ind

        if ind.ema_rapida_mayor_lenta('1h',9,20,0.3):
            # autoconfig alcista
            velas_filtro_minimo =60        # el minimo será un minimo cercano. De esta manera se evita tener un mínimo viejo  y muy bajo 
            velas_del_final = 20           # para poder dejar de comprar rápidamente en una bajada
            rsi_max = 70                  
            volumen_de_entrada = 1.7
        else:
            # autoconfig bajista
            velas_filtro_minimo =100
            velas_del_final = 50
            rsi_max = 60
            volumen_de_entrada = 2

        if self.filtro_minimo_superado(velas_filtro_minimo,velas_del_final):    #el minimo reciente es menor que el minimo amplio, está cayendo. no compramos
            return ret
                
        if self.hay_rsis_sobrevendidos(rsi_max):
            return ret
        
        if self.entrada_por_regreso_rsi(escala,40,50,volumen_de_entrada):
            if self.filtro_pico_minimo_ema_low(escala):
                ret = [True,escala,'buscar_rsi_minimo_subiendo_alcista']
    
        return ret    

    def buscar_vela_martillo_importante(self,escala,cvelas_rango=90,cvelas_rango_importantes=90):
        ret=[False,'xx']
        ind: Indicadores = self.ind

        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,0.35):
            velas_importantes_condideradas = int (cvelas_rango_importantes / 4) +1
            velas = ind.velas_imporantes(escala,cvelas_rango_importantes,velas_importantes_condideradas)      #dos velas para el log, pero tomo la primera ( la mas cercana )
            self.log.log(f'velas_importante {velas[0]}')
            vela:Vela = velas[0][2]
            posicion = velas[0][0]
            vela_confirma:Vela = ind.ultimas_velas(escala,1,cerradas=True)[0]
            if posicion <= 3 and vela.martillo() and vela_confirma.signo == 1:
                recorrido_minimo = ind.recorrido_promedio(escala,50) * 3
                recorrido = vela.high - vela.low
                if recorrido > recorrido_minimo:
                    ret = [True,escala,f'buscar_vela_martillo_importante_{cvelas_rango}_{cvelas_rango_importantes}']
        return ret        
    
    def buscar_minimo_ema9(self,escala,cvelas_rango=90,porcentaje_bajo=.35):
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):     #importante estar en la parte baja.. pero baja!!
            if not ind.ema_rapida_mayor_lenta(escala,9,21):
                if self.filtro_pico_minimo_ema(escala,9,'close',6,2):
                    if filtro_zona_volumen(ind,self.log,escala,9):
                        if ind.no_hay_velas_mayores_al_promedio(escala,4,2):
                            ret = [True,escala,f'buscar_minimo_ema9_{cvelas_rango}_{porcentaje_bajo}']
        return ret        

    def buscar_patrones_en_parte_baja(self,escala,cvelas_rango=90,porcentaje_bajo=0.5):
        ret=[False,'xx']
        ind: Indicadores = self.ind
        
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):     #importante estar en la parte baja.. pero baja!!
            if ind.patron_verde_supera_roja(escala):
                ret = [True,escala,f'patron_verde_supera_roja_{cvelas_rango}_{porcentaje_bajo}']
            elif ind.patron_martillo_verde(escala):
                ret = [True,escala,f'patron_martillo_verde{cvelas_rango}_{porcentaje_bajo}']
            #elif ind.patron_frenada_de_gusano_en_desarrollo(escala):
            #    ret = [True,escala,f'patron_frenada_de_gusano_en_desarrollo_{cvelas_rango}_{cvelas_rango_importantes}']    
        return ret        

    def buscar_minimo_ema_pendiente_positiva(self,escala,cvelas_rango=90,porcentaje_bajo=.5):
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):     #importante estar en la parte baja.. pero baja!!
            if not ind.ema_rapida_mayor_lenta(escala,9,21):
                if filtro_pendientes_emas_positivas(ind,self.log,escala,9,4):                  #4 pendientes positivas
                    if filtro_zona_volumen(ind,self.log,escala,9):
                        if ind.no_hay_velas_mayores_al_promedio(escala,4,2):
                            ret = [True,escala,f'buscar_minimo_ema_pendiente_positiva{cvelas_rango}_{porcentaje_bajo}']
        return ret 
    
    def buscar_minimo_parte_muy_baja(self,escala,cvelas_rango=90,porcentaje_bajo=.2):
        self.log.log('===== buscar_minimo_parte_muy_baja =====')
        ret=[False,'xx']
        if self.filtro_tendencia_alcista():
            if not filtro_parte_baja_rango(self.ind,self.log,'1d',120,.38):    #previene que se compre en la parte alta de rango en 4 horas
                return ret  
            if not filtro_parte_baja_rango(self.ind,self.log,'15m',90,.38):    #previene que se compre en la parte alta de rango en 4 horas
                return ret    
        else:
            if not filtro_parte_baja_rango(self.ind,self.log,'1d',120,.24):    #previene que se compre en la parte alta de rango en 4 horas
                return ret 
            if not filtro_parte_baja_rango(self.ind,self.log,'4h',120,.24):    #previene que se compre en la parte alta de rango en 4 horas
                return ret   
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):     #importante estar en la parte baja.. pero baja!!
            ret = [True,escala,f'buscar_minimo_parte_muy_baja{cvelas_rango}_{porcentaje_bajo}']
        return ret    

    def scalping_parte_muy_baja(self,escala,cvelas_rango=90,porcentaje_bajo=.2,p_xmin_impulso=50,em12=(4,7)):
        self.log.log('====== scalping_parte_muy_baja ======')
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):                              #estoy en la parte baja del rango
            if filtro_xvolumen_de_impulso(ind,self.log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):                   #hay volumen 27x mayor en total durante la bajada
                if filtro_dos_emas_positivas(ind,self.log,escala,ema1_per=em12[0],ema2_per=em12[1]):                                #giro en el precio
                    ret = [True,escala,f'scalping_parte_muy_baja{cvelas_rango}_{porcentaje_bajo}']
        return ret      

    def ema_rapida_lenta_xvolumen(self,escala,p_xmin_impulso=50,em12=(4,7)):
        self.log.log('====== scalping_parte_muy_baja ======')
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,50,.618):
            if filtro_ema_rapida_lenta(ind,self.log,escala,rapida=em12[0],lenta=em12[1],diferencia=0.1):  
                if filtro_xvolumen_de_impulso(ind,self.log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):
                    ret = [True,escala,f'ema_rapida_lenta_xvolumen'] 

        return ret

            


    def buscar_rsi_minimo_super_volumen(self,escala): 
        ret=[False,'xx']
        ind: Indicadores = self.ind

        rsi_min, pos_rsi_min, precio_rsi_min,rsi = ind.rsi_minimo_y_pos(escala,2)
        self.log.log('---> rsi_minimo_y_pos',rsi_min, pos_rsi_min, precio_rsi_min,rsi)

        if pos_rsi_min >0 and rsi_min < 35 and\
               rsi_min < rsi and\
               rsi < 35:
            if self.filtro_volumen_encima_del_promedio(escala,cvelas=7,xvol=2,vela_ini=pos_rsi_min):
                if self.filtro_pico_minimo_ema(escala,3,'low',izquierda=9,derecha=2):
                    ret = [True,escala,'buscar_rsi_minimo_super_volumen']
        return ret        


    def filtro_minimo_superado(self,cvelas=240,velas_del_final=30):
        ind: Indicadores = self.ind
        #m_horas =   ind.minimo_x_vol('1m',choras  ,1)
        minimo = ind.minimo_x_vol('1m',cvelas ,1,velas_del_final)   #no tengo en cuenta los  ultimos 50 minutos
        if minimo:
            ret = self.precio < minimo
            
        else:
            ret = True # no tengo todos los datos, considero superado
            
        self.log.log(f'min velas({cvelas} menos {velas_del_final}) {minimo} {ret}')    
        return ret

    #def filtro_precio_cerca_de_ema(self,escala,periodos,cerca=0.5):


    def filtro_pico_minimo_ema(self,escala,periodos,origen='close',izquierda=15,derecha=2):
        ret = False
        picos_low=self.ind.lista_picos_minimos_ema(escala,periodos,100,origen,izquierda,derecha)
        if len(picos_low) >0:
            pico = picos_low[0] 
            if pico[0] <= 3:
                ret =True
            else:
                self.log.log(f'no se cumpe pico minimo {origen} {pico}')    
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
            if self.filtro_rsi_armonicos(escala,1,valor_maximo=rsi_inf+5):
                #if self.filtro_volumen_calmado(escala, 2 , 0.9):
                ret = [True,escala,'buscar_rsi_bajo']

        self.log.log('----------------------')    

        return ret


    def hay_precios_minimos(self,cvelas,escala):
        ind: Indicadores = self.ind
        ret = True
        escalas=['1d','4h','15m','5m'] 
        
        if escala not in escalas:
            escalas.append(escala)
        for e in escalas:
            pxmin = ind.minimo_x_vol(e,cvelas,3) 
            if not self.precio_cerca(pxmin,self.g.escala_entorno[e]):
                ret =False
                self.log.log(f'no se cumple pxmin cerca {e} {pxmin} < {self.precio}')
                break
        
        return ret    

    def hay_rsis_sobrevendidos(self,max_rsi=69.5): 
        ind: Indicadores = self.ind
        ret = False
        escalas=['1d','4h','15m','5m'] 
        for e in escalas:
            rsi = ind.rsi(e)
            if rsi > max_rsi:
                ret = True
                self.log.log(f'rsi {e} {rsi} sobrevendido')
        return ret        
   

    def buscar_rebote_rsi(self,escala):
        ret=[False,'xx']
        if self.no_se_cumple_minimo_local(escala):
            return ret
        
        self.log.log('---buscar_rebote_rsi',escala)
        if self.filtro_rsi_armonicos(escala,2,valor_maximo=30): 
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

    def filtro_volumen_encima_del_promedio(self,escala,cvelas,xvol,vela_ini):
        ind: Indicadores = self.ind
        ret = ind.volumen_por_encima_media(escala,cvelas,xvol,vela_ini)    
        self.log.log( f'{ret}<---volumen_encima_del_promedio {escala} {cvelas} {xvol} {vela_ini}  ')
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
    
    def precio_cerca(self,px,porcentaje=0.30):
        return self.precio < px or (self.precio - px) / self.precio *100 < porcentaje 

    def precio_cerca_por_debajo(self,px,porcentaje=0.30):
        return self.precio < px and (px - self.precio) / self.precio *100 < porcentaje 

    def precio_objetivo_superado(self,escala):
        ind = self.ind
        objetivo_venta = ind.maximo_x_vol(escala,150,1)
        
        ret =  self.objetivo_venta > self.precio
        if ret:
            self.log.log(f'objetivo superado= {objetivo_venta}')
        return ret    

    def precio_sobre_ema_importante(self):
        ind = self.ind
        ret = False
        emas_importantes=[('1d',20),('1d',50),('4h',20),('4h',50)]    
        for em in emas_importantes:
            if self.precio_cerca(ind.ema(em[0],em[1])):
                self.log.log(f'precio cerca de ema{em}')
                ret = True
        return ret 

    def precio_bajo_ema_importante(self,escala):
        ind = self.ind
        ret = False
        emas_importantes=[('1d',20),('1d',50),('4h',20),('4h',50)]    
        for em in emas_importantes:
            escala=em[0]
            periodos=em[1]
            if self.precio_cerca_por_debajo(ind.ema(escala,periodos)):
                self.log.log(f'precio bajo de ema{em}')
                ret = True
        return ret  

    def evaluar_si_hay_que_vender(self,escala,gan,duracion_trade):
        self.log.log(f'senial de entrada {self.senial_entrada}')
        ind: Indicadores =self.ind

        self.escala_de_salida = escala

        self.log.log(f'escala_de_salida {self.escala_de_salida}' )    

        if not filtro_parte_alta_rango(ind,self.log,self.escala_de_salida,45):
            return False   

        gan_min = calc_ganancia_minima(self.g,self.g.ganancia_minima[escala],self.escala_de_salida,duracion_trade)
        precio_bajista = self.el_precio_es_bajista('4h') and self.el_precio_es_bajista(self.escala_de_salida)
        precio_no_sube = ind.no_sube(self.escala_de_salida)
        tiempo_trade_superado = duracion_trade > self.g.tiempo_maximo_trade[self.escala_de_salida]
        duracion_en_velas = int(duracion_trade/self.g.escala_tiempo[self.escala_de_salida])
        self.log.log(f'gan_min {gan_min} gan {gan} px_bajista {precio_bajista} px_no_sube {precio_no_sube}' )
        self.log.log(f' duracion {duracion_trade} velas {duracion_en_velas} t_superado {tiempo_trade_superado}')
                 
        if gan < 0.3 or self.no_se_cumple_objetivo_venta():
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



        rsi_max,rsi_max_pos,rsi = ind.rsi_maximo_y_pos(self.escala_de_salida,5)
        self.log.log(f'rsi {rsi} rsi_max {rsi_max} rsi_max_pos {rsi_max_pos}')


        lista_max = ind.lista_picos_maximos_ema(self.escala_de_salida,3,10,'close')

        if lista_max:
            pos_max = lista_max[0][0] 
            if pos_max <= 3 and rsi > 70:
                self.log.log(f'{marca_salida} rsi > 70 y picoema {lista_max}')
                return True

        if rsi_max > 90 and rsi_max > rsi and  1<= rsi_max_pos <= 3 and gan>gan_min: ## and self.filtro_volumen_calmado(self.escala_de_analisis):
            self.log.log(f'{marca_salida} rsi_max  > 90 {rsi_max}')
            return True

        if rsi_max > 70 and rsi_max > rsi and 1<= rsi_max_pos <= 4 and precio_no_sube: 
            self.log.log(f'{marca_salida} rsi_max > 70 {rsi_max}')
            return True
        
        if rsi > 65  and self.filtro_volumen_calmado(self.escala_de_salida,3,0.7):                        #0.8 baja la barrera que tiene que superar el volumen para considirarse importante
            self.log.log(f'{marca_salida} rsi escala >65 {rsi}, volumen_calmado 3 0.7')
            return True

        if rsi_max > 53 and rsi_max > rsi and 1<= rsi_max_pos <= 3 and precio_bajista:
            self.log.log(f'{marca_salida} rsi_max > 53 {rsi_max} ,precio_bajista')
            return True

        if precio_no_sube and self.precio_objetivo_superado(self.escala_de_salida):
            return True
    
        if rsi_max > 50 and rsi_max > rsi and 1<= rsi_max_pos <= 3 and self.precio_bajo_ema_importante(self.escala_de_salida):
            return True

        var = variacion_absoluta(ind.ema(self.escala_de_salida,50) ,self.precio  )
        inf = self.g.escala_ganancia[self.escala_de_salida] / -10
        if rsi_max > 40 and 1<= rsi_max_pos <=5 and precio_no_sube and inf  <= var <= 0:
            self.log.log(f'{marca_salida} rsi_max= {rsi_max} > 40 and rsi_max_pos {rsi_max_pos} <=5 and precio_no_sube and var {inf} <= {var} <= 0')
            return True    
        
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
        minimo,velas_bajada = ind.minimo_en_ma(escala,6,'close',cvelas=posicion_minimo+1) 
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
        pmaximo, velas_subida = ind.maximo_en_ema(escala,periodos=7,datos='close',cvelas=posicion_maximo+1) 
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
        rsi_min,rsi_min_pos,_,rsi= ind.rsi_minimo_y_pos(escala,  pos_rsi_inferior[1]    )
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
    
    def filtro_tendencia_alcista(self):
        ind: Indicadores =self.ind
        if ind.ema_rapida_mayor_lenta('4h',20,50,1): #and ind.ema_rapida_mayor_lenta('1d',20,50,0.7):
            ret = True
            self.log.log('Tendencia_Alcista!')
        else:
            ret = False 
            self.log.log('Tendencia_Bajista')
        return ret     

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
       
        filtro_ok = rsi < valor_maximo 
        
        self.log.log(self.txt_resultado_filtro(filtro_ok,self.indentacion)+'rsi',escala,'max',valor_maximo,rsi)  

        return filtro_ok

    
    def filtro_rsi_armonicos_deprecasted(self, escala,valor_maximo=30):
        ''' busca que todos RSI sean inferiores a 35 para retornar True, caso contrario False '''
        ret = True
        for esc in self.g.lista_rsi_armonicos[escala]:
            if not self.filtro_rsi(esc,valor_maximo):
                ret = False
                break
        return ret    

    def filtro_rsi_armonicos(self, escala,cantidad_de_armonicos=1,valor_maximo=30):
        c=0
        lista_armonicos=[]
        
        #costruccion de lista de armónicos hacia abajo
        z=1
        while c < cantidad_de_armonicos:
            esc=self.g.zoom(escala,z)
            if esc==escala: #no ha mas chica
                break
            else:
                lista_armonicos.append(esc)
                c +=1
                z +=1
        
        # no alcanzó sigo construyendo la lista hacia arriba
        z=1
        while c < cantidad_de_armonicos:
            esc=self.g.zoom_out(escala,z)
            if esc==escala: #no haya mas grande
                break
            else:
                lista_armonicos.append(esc)
                c +=1
                z +=1

        #verificacion de los rsi armonicos
        self.log.log(f'filtro_rsi_armonicos {lista_armonicos}')
        ret = True
        for esc in lista_armonicos:
            if not self.filtro_rsi(esc,valor_maximo):
                ret = False
                break 

        return ret    





    

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
        objetivo_venta = self.calc_objetivo_venta(self.escala_de_analisis)
        
        self.db.trade_persistir(self.moneda,self.moneda_contra,self.escala_de_analisis,self.analisis_provocador_entrada,can_comprada,precio_orden,objetivo_venta,gi,gs,tp,self.texto_analisis_par(),strtime_a_fecha(orden['time']),orden['orderId'])
        
        #se compró, hay que pasar al estado de esperar a que suba 
        self.log.log('enviar_correo_filled_compra...')
        self.enviar_correo_filled_compra(txt_filled)
        if self.funcion=='comprar+ya':
            self.cambiar_funcion('vender')
        else:    
            self.iniciar_estado( self.estado_siguiente() )

    def calc_objetivo_venta(self,escala):
        if self.objetivo_venta >0: 
            ret = self.objetivo_venta                       #objetivo venta parametrizado
        else:    
            ret = 0    #self.ind.maximo_x_vol(escala,100,3)       #objetivo venta calculado
        return ret


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


    # ESTADO 3 - Accion #
    def estado_3_accion(self):
        self.retardo_dinamico(1)
        tiempo_en_estado = int (time.time() - self.tiempo_inicio_estado)
        duracion_trade =  calc_tiempo_segundos(  self.fecha_trade , datetime.now())
        self.actualizar_precio_ws()
        gan=self.ganancias() #creo esta variable para no llamar reiteradamente a la funcion
        self.set_tiempo_reposo(gan)
        
        self.log.log(  "___E.3 Esp.Ven. Ti:",tiempo_en_estado,self.par,self.escala_de_analisis,self.senial_entrada)
        
        # partir de acá controlo condiciones de venta o salida
        self.log.log(  "---> Control de condiciones de salida --->" )
       
        self.actualizar_precio_ws() 

        #### INICIAR STOPLOSS#####
        self.iniciar_stop_loss_en_caso_de_ser_posible()
        
        ### control del STOP LOSS ###
        self.controlar_stop_loss()

        #### INICIAR LIQUIDEZ#####
        #if self.hay_que_tratar_de_tomar_ganancias(gan,atr):
        if not self.generar_liquidez and self.evaluar_si_hay_que_vender(self.escala_de_analisis,gan,duracion_trade):
            self.generar_liquidez = True
            if self.stoploss_habilitado == 1:
                self.subir_stoploss(True)
            else:
                self.iniciar_stoploss()    
            self.tiempo_reposo = 0
            return

        # PORNER A RECOMPRAR en caso de pérdidas
        # acá  si pasamos cierto umbral de pérdidas, ponemos a recomprar
        if self.momento_de_recomprar(self.escala_de_analisis,gan,duracion_trade):
            #self.enviar_correo_generico(f'RECOMPRA.')
            self.tiempo_reposo = 0
            self.iniciar_estado(7)
            return
        
        self.log.log("FIN E3. Acciones")

    def iniciar_stop_loss_en_caso_de_ser_posible(self):
        if self.stoploss_habilitado == 0:

            if not self.ind.ema_rapida_mayor_lenta('4h',10,55,.5):     #esta bajista en 4h
                if self.precio > self.precio_salir_derecho and self.ind.rsi(self.escala_de_analisis) > 69:
                    self.log.log(f'hay precio para stoploss y rsi alto')
                    self.iniciar_stoploss()   
                    return

            precio_minimo_sl_positivo = self.precio_salir_derecho * (1+self.g.ganancia_minima[self.escala_de_analisis]/100)
            self.log.log(f'precio {self.precio}  precio_minimo_sl_positivo {precio_minimo_sl_positivo}')
            if self.precio < precio_minimo_sl_positivo:    #caso stoploss negativo
                sl_negativo = self.calculo_stoploss_negativo()
                gan_sl_negativo = calculo_ganancias(self.g,self.precio_compra,sl_negativo)
                self.log.log(f'sl_negativo {sl_negativo}  gan_sl_negativo {gan_sl_negativo}')
                if  gan_sl_negativo > -10:
                    self.stoploss_negativo = 1
                    self.iniciar_stoploss()
                    
            else:                              #caso stoploss positivo
                self.iniciar_stoploss()    


    # def iniciar_stop_loss_en_caso_de_ser_posible(self):
    #     ''' si estoy en positivo y alcista, calculo un precio_seguro para poner el stoploss y si el precio está por encima 
    #         del precio_seguro, inicio el stoploss
    #         precio_seguro es aquel menos probable a ser alcanzadoen caso de que el precio baje.
    #         sino no estoy alcista, apensa puesa salir derecho clavo stoploss
    #     '''
    #     if self.stoploss_habilitado == 0 and self.precio > self.precio_salir_derecho:
    #         self.log.log(f'iniciar_stop_loss_en_caso_de_ser_posible para {self.senial_entrada}')
            
    #         if self.ind.ema_rapida_mayor_lenta2('1d',10,55,1): 
    #             velas_maximo=80       #++++++80++++++#_____35_____#
    #             velas_maximo_ini=35
    #             velas_minimo=20        #-----20----#1# 
    #             velas_minimo_ini=1     
    #             velas_recorrido=200
    #         else:
    #             velas_maximo=100       #+++++++++100++++++++#___30___#
    #             velas_maximo_ini=30
    #             velas_minimo=30        #-----30----#1# 
    #             velas_minimo_ini=1     
    #             velas_recorrido=120

    #         if filtro_precio_mayor_minimo(self.ind,self.log,self.escala_de_analisis,velas_minimo,velas_minimo_ini):
    #             if filtro_precio_mayor_maximo(self.ind,self.log,self.escala_de_analisis,velas_maximo,velas_maximo_ini):
    #                 if self.precio >= self.precio_salir_derecho + self.ind.recorrido_maximo(self.escala_de_analisis,velas_recorrido):
    #                     self.iniciar_stoploss()


    def controlar_stop_loss(self): 
        if self.stoploss_habilitado == 0:
            return
        ind = self.ind    
        vela:Vela = ind.ultimas_velas('1m',1)[0]
        if self.precio < self.stoploss_actual or vela.low < self.stoploss_actual or self.ct_controlar_stoploss.tiempo_cumplido():
            self.ct_controlar_stoploss.reiniciar()
            self.controlar_orden_stop_loss()
            

    def controlar_orden_stop_loss(self):
        
        orden=self.oe.consultar_estado_orden(self.ultima_orden)
        self.log.log(  f"controlar_orden_stop_loss {self.par} {orden['estado']}" )
        
        if orden['estado']=='FILLED':
            self.log.log(  "FILLED" )
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
                if self.db.trades_cantidad(self.moneda,self.moneda_contra) > 0  or\
                    self.todo_bonito_para_seguir_comprado():
                    self.iniciar_estado( self.estado_siguiente() )
                else:
                    self.dormir_un_tiempo_prudencial()    
            return
        
        elif orden['estado']=='CANCELED': #Se dio un caso que apareció una orden cancelada... en este caso tratamos de vender nuevamente.
            if orden['ejecutado']>0:
                self.db.trade_sumar_ejecutado(self.idtrade,orden['ejecutado'],orden['precio'],strtime_a_fecha(orden['time']),orden['orderId'])
                self.cant_moneda_compra= self.cant_moneda_compra - orden['ejecutado']
                self.enviar_correo_error('Orden cancelada, controlar que pasó')
                self.estado_0_inicio()
                return
            else:
                self.ultima_orden={'orderId':0}
                self.stoploss_habilitado=0
                self.stoploss_actual=0

        elif orden['estado']=='NEW':
            if self.precio < self.stoploss_actual:
                ultima = self.ultima_orden
                if self.cancelar_ultima_orden():
                    order_cancelada=self.oe.consultar_estado_orden(ultima)
                    todo_mal=False
                    if order_cancelada['estado']=='CANCELED':
                        self.ultima_orden={'orderId':0}
                        self.stoploss_habilitado=0
                        self.stoploss_actual=0
                        if order_cancelada['ejecutado'] > 0:
                            todo_mal=True
                    else:
                        todo_mal=True 
                    if todo_mal:           
                        self.enviar_correo_error('stoploss NO SE PUEDO CANCELAR CORRECTAMENTE resolver en forma manual')
                        self.deshabilitacion_de_emergencia()
            else:    
                self.log.log( "NEW, intentamos subir el sl" )
                self.subir_stoploss(False)

        elif orden['estado']=='PARTIALLY_FILLED': #ojo hay que cancelar, y luego leer cuanto fue lo que se alanzó vender.
            self.log.log(  "bucles   =",self.bucles_partial_filled )
            self.log.log(  "ejecutado=",orden['ejecutado'] )
            if self.bucles_partial_filled > 400: #15 seg cada iter 
                ultima = self.ultima_orden
                if self.cancelar_ultima_orden():
                    order_cancelada=self.oe.consultar_estado_orden(ultima)
                    if order_cancelada['estado']=='CANCELED':
                        #agrega al trade la cantidad vendida (ejecutada) que en este caso es el total.
                        self.db.trade_sumar_ejecutado(self.idtrade,order_cancelada['ejecutado'],order_cancelada['precio'],strtime_a_fecha(orden['time']),orden['orderId'])
                        self.cant_moneda_compra= self.cant_moneda_compra - orden['ejecutado']
                    
                self.enviar_correo_error('stoploss PARTIALLY_FILLED resolver en forma manual')
                self.deshabilitacion_de_emergencia()
                return
                
            self.bucles_partial_filled+=1    
 
    def momento_de_recomprar(self,escala,gan,duracion_trade):
        
        gan_limite = self.g.escala_ganancia[escala] * -1.5
        self.log.log( f'momento_de_recomprar?  gan {gan}, gan_limite {gan_limite} duracion {duracion_trade}' )
        #if self.moneda=='BTC' < 0.5 and duracion_trade > 60:    #experimental, esto podría comprar demasiado
        #    recomprar = True
        #else:    
        recomprar =  gan < gan_limite and duracion_trade > 60
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
            ret = ahora - self.tiempo_inicio_stoploss
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
           

    def iniciar_stoploss(self,stoploss=None):
        self.log.log(self.par,'iniciar_stoploss....')

        if stoploss is None:
            stoploss=self.calcular_stoploss() 

        derecho_gan_min = self.precio_salir_derecho * (1+self.g.ganancia_minima[self.escala_de_analisis]/100)
        if self.stoploss_negativo == 0 and  stoploss < derecho_gan_min: # abortamos, hemos calculado no es válido
            #este stoploss calculado es inválido, pero si hay un stoploss puesto de antes válido, lo deja
            self.log.log('No se pude poner stoploss ',stoploss,' < ',derecho_gan_min,'derecho_gan_min'  )
            return
                
        if self.cancelar_ultima_orden():
            resultado = self.ajustar_stoploss(stoploss)
            if resultado =='OK':
                self.enviar_correo_generico(f"SL.INI. {self.ultima_orden['orderId']}")
        else:
            self.intentar_recuperar_venta()        


    def px_stoploss_positivo(self):
        ''' calcular un precio entre self.precio y self.precio_salir_derecho
            que tenga la probabilidad mas baja (especulada) de que self.precio
            retroceda y se ejecute el stoploss
        '''
        sl = self.ind.stoploss_ema(self.escala_de_analisis,self.precio_salir_derecho,10,5)

        if sl > self.stoploss_actual:
            self.log.log(f'sl de {self.stoploss_actual} --> {sl}')
        else:    
            sl = self.stoploss_actual    

        return sl 

    def subir_stoploss(self,forzado=False):
        if not forzado and not self.ct_subir_stoploss.tiempo_cumplido():         #para evitar subir el stoploss por este método, muy seguido
            return
        nuevo_stoploss = self.px_stoploss_positivo()
        if nuevo_stoploss + self.tickSize * 2 < self.precio:
            if self.stoploss_habilitado==1 and nuevo_stoploss > self.stoploss_actual:
                if self.cancelar_ultima_orden():
                    resultado = self.ajustar_stoploss(nuevo_stoploss)
                    if resultado == "OK":
                        ret='sl subido ' + str(nuevo_stoploss) 
                        self.ct_subir_stoploss.reiniciar()
                    else:    
                        ret='falló subir el stoploss'
                else:
                    self.intentar_recuperar_venta()    
            else:
                ret=f'no se puede subir sl a {nuevo_stoploss}  stoploss_actual={self.stoploss_actual}'    
        else:
            ret=f'no se puede subir sl a {nuevo_stoploss} muy cerca del precio {self.precio}'    

        return ret
    
    def subir_stoploss_viejo(self,tikcs,forzado=False):
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
            self.ct_subir_stoploss = Controlador_De_Tiempo(60)
            self.ct_controlar_stoploss = Controlador_De_Tiempo(60)
            self.ct_subir_stoploss_uno = Controlador_De_Tiempo(60)
            self.bucles_partial_filled = 0
        else:
            self.stoploss_habilitado=0
            self.stoploss_actual=0
            self.log.log('No puedo poner stoploss',nuevo_stoploss,resultado)    

        return resultado    


    # previene que el exchangue de el error de min_notional
    def monto_moneda_contra_es_suficiente_para_min_motional(self,cantidad,precio_vta):   
        valor=cantidad * precio_vta
        if valor < self.min_notional:
            self.log.err( "Min Notional ",self.min_notional," y ",valor, self.moneda_contra)
            return False
        else:
            return True    
    
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
        tiempo  = self.g.escala_tiempo["1d"] + random.randint(3600, 7200)
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
        for cvelas in range(50,300,50):
            sl = self.ind.minimo(self.escala_de_analisis,cvelas)  / 1.01
            if sl < self.precio:
                break
        
        if sl > self.precio:
            sl = self.precio - self.ind.recorrido_maximo(self.escala_de_analisis,50)
        return sl

    def calcular_stoploss(self):
        self.actualizar_precio_ws()
        self.ultimo_calculo_stoploss = time.time()
     
        if self.stoploss_negativo == 1 and self.precio < self.precio_salir_derecho * (1+self.g.ganancia_minima[self.escala_de_analisis]/100) :
            return self.calculo_stoploss_negativo()
     
        st = self.calculo_basico_stoploss(self.generar_liquidez) 

        st =  self.st_correccion_final(st)
        
        return   st    

    def calculo_basico_stoploss_viejo(self):
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


    def calculo_basico_stoploss__viejo(self,generar_liquidez=False):
        '''
        Trata de conseguir un sl sobre una ema importante
        caso contrario establece el precio salir derecho
        '''
        ind = self.ind            

        if generar_liquidez:
            periodos=[22,17,12,7]
        else:
            periodos=[207,107,57,27]     
        
        sl = self.stoploss_actual
        
        per_ema = 0
        for p in periodos:
            ema = ind.ema(self.escala_de_analisis,p)
            self.log.log( f'--> {ema} ema({per_ema})') 
            if self.precio > ema and sl < ema:
               sl = ema
               per_ema = p
               break

        if sl == 0:
            self.precio_salir_derecho

        self.log.log( f'calculo_basico_stoploss {sl} ema({per_ema})')    

        return sl    

    def calculo_basico_stoploss(self,generar_liquidez=False):
        '''
        Trata de conseguir un sl basado en rangos
        '''
        sl = self.stoploss_actual

        if generar_liquidez:
            sl_nuevo = self.precio - self.ind.recorrido_minimo(self.escala_de_analisis,100)
        else:
            sl_nuevo = self.precio - self.ind.recorrido_maximo(self.escala_de_analisis,200)
        
        self.log.log(f'sl_nuevo={sl_nuevo}')

        if sl_nuevo < self.precio_salir_derecho and self.precio > self.precio_salir_derecho and self.stoploss_negativo==0:
            ex_sl_nuevo = sl_nuevo
            sl_nuevo =self.precio_salir_derecho + (self.precio-self.precio_salir_derecho) / 2  
            self.log.log(f'sl_nuevo={ex_sl_nuevo} < precio_salir_derecho, recalculo={sl_nuevo}')
      
        if  sl_nuevo > sl:
            sl = sl_nuevo

        sl = self.st_correccion_final(sl)    

        self.log.log( f'calculo_basico_stoploss(generar_liquidez={generar_liquidez}) ret={sl} ')    

        return sl    

    def calculo_stoploss_scalping(self):
        sl = self.precio - self.ind.recorrido_minimo(self.escala_de_analisis,30)
        if sl < self.precio_salir_derecho:
            sl = self.calculo_precio_de_venta(0.15)
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

        if st < self.precio_salir_derecho and self.stoploss_negativo==0:
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
    
    
    def porcentaje_en_ticksize(self,valor,porcentaje):
        vporcentaje = valor * porcentaje / 100
        cant_ticks = int(vporcentaje / self.tickSize)
        if cant_ticks == 0: #corrección para que de al menos 1 tick  
            cant_ticks = 1
        return (cant_ticks * self.tickSize)    

   
    def coef_stoploss_seguro(self): #a medida que van pasando los bucles (el tiempo) se pone mas nervioso y baja las pretensiones
        if self.estado_bucles<150: 
           coef=1.02
        elif self.estado_bucles>=300 and self.estado_bucles<600:
            coef=1.015
        else:    
            coef=1.01
        return coef        


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
                if self.db.trades_cantidad(self.moneda,self.moneda_contra) > 0  or\
                    self.todo_bonito_para_seguir_comprado():
                    self.iniciar_estado( self.estado_siguiente() )
                else:
                    self.dormir_un_tiempo_prudencial()    
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
    
    def todo_bonito_para_seguir_comprado(self):
        return fauto_compra_vende.habilitar_pares.hay_precios_minimos_como_para_habilitar(self.ind,self.g,self.log)  or\
            (fauto_compra_vende.habilitar_pares.el_precio_no_esta_cerca_del_maximo(self.ind,self.log) and\
             fauto_compra_vende.habilitar_pares.para_alcista_como_para_habilitar(self.ind,self.g,self.log) )
 
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
        objetivo_venta = self.calc_objetivo_venta(self.escala_de_analisis)

        self.db.trade_persistir(self.moneda,self.moneda_contra,escala ,senial_entrada, ejecutado ,precio,objetivo_venta ,gi,gs,tp,
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
        self.objetivo_venta_trade=trade['objetivo_venta']

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

        titulo=self.par+' [Estado '+ str(self.estado)+'] '+sgan+ f' % {self.escala_de_salida}'
        texto=titulo+'\n'
        texto+=" Precio Compra: " + self.format_valor_truncando( self.precio_compra,8) + '\n'
        texto+=" Precio  Venta: " + self.format_valor_truncando( self.precio_venta,8) +" "+ sgan+ ' %  '+gan_moneda_contra +' m$c ' +ganusdt +' usdt\n'

        self.log.log(texto)
        self.log_resultados.log(texto)

        #2/9/2019 no persisto mas esto se deduce de los trades
        #persistir en la base.       
        #cant=self.tomar_cantidad(self.moneda) 
        #self.db.persistir_ganancias(ganusdt,self.moneda,self.moneda_contra)

       
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
                st=f'[sl {self.format_valor_truncando( self.stoploss_actual,self.cant_moneda_precision)}]  '
            else:
                st=' '    
            #stop_loss_calculado=self.calcular_stoploss()
            tiempo_trade=self.calc_tiempo_trade()

            st+=' ' + tiempo_trade # + ' ' + str(round(self.pstoploss,2))

            return self.linea( f"Px: {self.format_valor_truncando( self.precio,8)}  {self.ganancias()} {st} [{self.escala_de_salida}] " )    
        except Exception as e:
            return str(e)   
    
    def calc_tiempo_trade(self):   
        try:
            tiempo_trade=datetime.now().replace(microsecond=0) - self.fecha_trade   #esto es un timedelta
            h, resto = divmod(tiempo_trade.seconds, 3600)
            m, _ = divmod(resto, 60)
            tiempo_trade=f'{tiempo_trade.days}d {h}h {m}m'
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
        if self.estado==3:
            #ind=self.ind
            texto = self.texto_analisis_moneda_e3()
            self.log.log( texto )
        
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


