import json
import os
from metricas import Metricas

## variables globales
class Global_State:
    # variables globales
    fee = 0.001
    pares = {}
    pares_control = {}
    
    se_puede_operar = False
    log_level = 2
    trabajando = True

    mostrar_cola = 0                    #habilita mostrar la cola de uso? qué es la cola de uso?.. documentar!
    
    cant_pares_activos = 0
    max_pares_activos_config = 20       # pares activos configurados
    min_pares_activos_config = 10       # pares activos que se recalculan  por el sensor de rendimiento
    max_pares_activos = 10              # pares activos que se recalculan  por el sensor de rendimiento

    max_mem=1.4                         # maxima cantidad de memoria consumida por el bot

    rankig_por_volumen = {}
    
    #variables auto_compra_vende
    tiempo_envio_reporte_correo=3600
    
    # variables globales de pares
    horas_deshabilitar_par = 4               #tiempo en horas que como minimo se deshabita un par
    reserva_btc_en_usd=0                     #no comprar mas si queda menos una cantidad de btc expresada en usdt
    reserva_usdt=0                           #no comprar si queda menos de 
    x_min_notional=1                         #multiplicador de la cantidad minima de compra
 
    maxima_cantidad_de_pares_con_trades=1    #cantidad maxima de pares con trades que están activos


    #otras variables     
    ret_fibo = (0.236,0.382,0.5,0.618,0.786,1,1.618,2.618)


    ema_pendiente_maxima={'1m':0.0009,'3m':0.00093,'5m': 0.00095 ,'15m':0.00098 ,'30m':0.00099 ,'1h':0.001 ,'2h':0.00102,'4h':0.00107,'1d':0.00111,'1w':0.00119,'1M':0.00156}
    
    #usada en tres_emas_favorables
    ema_poca_diferencia ={'1m':0.016 ,'3m':0.020 ,'5m': 0.083   ,'15m':0.04    ,'30m':0.5     ,'1h':1     ,'2h':1.5    ,'4h':2      ,'1d':3      ,'1w':4      ,'1M':5}

    falta_de_moneda={'USDT':False,'BTC':False}

    max_compras_simultaneas={'USDT':10,'BTC':10}
    pares_en_compras={'USDT':0,'BTC':0}

    escala_anterior ={'1m':'xx','3m':'1m','5m':'3m' ,'15m':'5m' ,'30m':'15m','1h':'30m','2h':'1h','4h':'2h','1d':'4h','1w':'1d','1M':'1w'}
    escala_siguiente={'1m':'3m','3m':'5m','5m':'15m','15m':'30m','30m':'1h' ,'1h':'2h' ,'2h':'4h','4h':'1d','1d':'1w','1w':'1M','1M':'xx'}
    escala_tiempo  = {'1m':60  ,'3m':180 ,'5m': 300 ,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,'1w':604800,'1M':2419200}
    escala_ganancia ={'1m':.5  ,'3m':0.7  ,'5m': .9  ,'15m': 2   ,'30m':2.5 ,'1h':3 ,'2h':3.5, '4h':4  ,'1d':5  , '1w':15,'1M':30}
    escala_entorno  ={'1m':.25 ,'3m':0.35 ,'5m': .45 ,'15m': 0.55,'30m':0.75,'1h':1 ,'2h':1.25,'4h':1.5,'1d':2.5, '1w':3 ,'1M':5 }
    
    escala_pend_ema ={'1m':.5  ,'3m':0.7  ,'5m': .9  ,'15m': 2   ,'30m':2.5 ,'1h':3 ,'2h':3.5, '4h':4  ,'1d':5  , '1w':15,'1M':30}


    hay_pump = {'velas':5,'xatr':12,'xvol':12}

    #tiempo maximo que debe durar una entrada
    tiempo_maximo_trade  ={ '1m':escala_tiempo['1d']    ,'3m':escala_tiempo['1d']     ,'5m':escala_tiempo['1d']     ,'15m':escala_tiempo['1d'],\
                           '30m':escala_tiempo['1d']    ,'1h':escala_tiempo['1d'] * 2 , '2h':escala_tiempo['1d'] * 3,\
                            '4h':escala_tiempo['1d'] * 5,'1d':escala_tiempo['1d'] * 15, '1w':escala_tiempo['1d'] * 90,\
                            '1M':escala_tiempo['1M'] * 12}

    lista_rsi_armonicos  = {'1m' :['3m' ,'5m'],
                            '3m' :['5m' ,'15m'],  
                            '5m' :['15m','30m'],
                            '15m':['5m' ,'30m'],
                            '30m':['15m','1h' ],
                            '1h' :['30m','2h' ],
                            '2h' :['1h' ,'4h' ],
                            '4h' :['2h' ,'1h','15m'],
                            '1d' :['4h' ,'2h','1h','15m' ],
                            '1w' :['1d' ,'4h' ],
                            '1M' :['1w' ,'1d' ]}                        
    
    #ganancia_minima en la que se comienza a considerar poner stoploss
    ganancia_minima ={'1m':0.5,'3m':0.7,'5m': 0.9 ,'15m':1 ,'30m':1.25 ,'1h':1.5 ,'2h':2,'4h':4,'1d':5,'1w':10,'1M':20}
    
    velas_hora  = {'1m':60 ,'3m':20 , '5m': 12 ,'15m':4,'30m':2,'1h':1,'2h':0.5,'4h':0.25,'1d':0.041666667,'1w':0.005952381,'1M':0.001388889}

    #cuantas rango, volatilidad
    escala_prango = {'1m':1 ,'3m':1.25,'5m':1.5 ,'15m':2,'30m':2.5,'1h':2.7,'2h':2.9,'4h':3,'1d':4,'1w':5,'1M':6}

    escalas_comunes_rangos={'1h':50,'4h':40,'1d':30,'1w':15}

    #numero que indica el límite a partir del cual e adx se considera con fuerza
    confirmacion_adx = 20

    metricas = Metricas()

    def __init__(self,gestor_de_posicion=None,config_file=None):
        if not config_file:
            config_file =  self.dirlogs = os.path.join( os.getcwd() , os.getenv('CONFIG_FILE', 'config.json')   )         
        self.cargar_parametros_de_config_json(config_file)
        self.max_pares_activos = self.max_pares_activos_config
    
    def cargar_parametros_de_config_json(self,config_file):
        parconfig = self.cargar_config_json(config_file)
        if parconfig != None:
            try:
                self.trabajando = bool(parconfig['trabajando'])
                self.max_pares_activos_config = int(parconfig['max_pares_activos'])
                self.min_pares_activos_config = int(parconfig['min_pares_activos'])
                self.log_level = int(parconfig['log_level'])
                self.mostrar_cola = int(parconfig['mostrar_cola'])
                self.maxima_cantidad_de_pares_con_trades = int(parconfig['maxima_cantidad_de_pares_con_trades'] )
                self.tiempo_envio_reporte_correo = int(parconfig['tiempo_envio_reporte_correo'])

                self.reserva_btc_en_usd        = parconfig['reserva_btc_en_usd']
                self.reserva_usdt              = parconfig['reserva_usdt']
                self.x_min_notional            = parconfig['x_min_notional'] 
                self.horas_deshabilitar_par    = int(parconfig['horas_deshabilitar_par'])
                self.max_compras_simultaneas   = parconfig['max_compras_simultaneas']
                self.max_inversion_btc         = float(parconfig['max_inversion_btc'])
                self.max_inversion_usdt        = float(parconfig['max_inversion_usdt'])
                self.hay_pump                  = parconfig['hay_pump'] 
                self.escala_pend_ema           = parconfig['escala_pend_ema'] 
                
                
                
            except Exception as e:
                print ( "cargar_parametros_de_config_json:",str(e),'\n',config_file )     
                




    # def actualizar_posicion(self):
    #     btc_operable,btc_transado,usdt_operable,usdt_transado = self.gestor_de_posicion.actualizar_posicion()
    #     self.set_posicion(btc_operable,btc_transado,usdt_operable,usdt_transado)

    def calculo_ganancia_total(self,pxcompra,pxventa,cantidad):
        comision  = pxcompra * cantidad * self.fee
        comision += pxventa  * cantidad * self.fee
        gan = cantidad * (pxventa - pxcompra) - comision 
        return gan

    def calculo_ganancia_porcentual(self,pxcompra,pxventa):
        ''' ganancia representada en porcentaje '''
        comision  = pxcompra * self.fee
        comision += pxventa  * self.fee
        gan= pxventa - pxcompra - comision 
        return round(gan/pxventa*100,2)


    def cargar_config_json(self,archivo):
        try:
           with open(archivo,'r') as f:
                config = json.load(f)
                f.close() 
        except  Exception as e:
            print(str(e),'\n',archivo)
            config = None   
        return config             
    
    def menor_tiempo(self,temporalidades):
        ''' retorna el mentor tiempo de una lista de temporalidades '''
        t = self.escala_tiempo['1M']
        for e in temporalidades:
            if self.escala_tiempo[e] < t:
                t = self.escala_tiempo[e]

        return t 
    
    # def set_posicion(self,btc_operable,btc_transado,usdt_operable,usdt_transado):
    
    #     self.btc_operable = btc_operable
    #     self.btc_transado = btc_transado
        
    #     self.usdt_operable = usdt_operable
    #     self.usdt_transado = usdt_transado

    #     self.invertido_btc  =  btc_transado / (btc_transado + btc_operable)
    #     self.invertido_usdt =  usdt_transado / (usdt_transado + usdt_operable) 

    

    def posicion_ranking(self,moneda,moneda_contra):
        #retorna el valor de la clave que es la posicion en el ranking por volumen
        #pero retorna un valor obsenamente grande cuando no está en el ranking
        #usa el metodo get() del diccionario
        return self.rankig_por_volumen.get( moneda+moneda_contra,9999999 )  

    def zoom(self,escala,x):
        esc=escala
        for i in range(x):
            e=self.escala_anterior[esc]
            if e == 'xx':
                esc=escala
                break
            else:
                esc=e
        return esc

    def zoom_out(self,escala,x):
        esc=escala
        for _ in range(x):
            e=self.escala_siguiente[esc]
            if e == 'xx':
                esc=escala
                break
            else:
                esc=e
        return esc    