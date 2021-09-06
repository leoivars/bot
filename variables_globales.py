#from gestor_de_posicion import Gestor_de_Posicion
import time
import json
from threading import Lock
from metricas import Metricas

## variables globales
class VariablesEstado:
    # variables globales
    fee = 0.001
    pares = {}
    pares_control = {}
    BTC_invertido_actual = -100
    cant_pares_con_senial_compra = 0

    pares_con_senial_compra = []
    ultima_habilitacion=time.time() - 7200
    se_puede_operar = False
    log_level = 2
    trabajando = True

    mostrar_cola = 0
    
    cant_pares_activos = 0
    max_pares_activos_config = 20 #estos son los pares activos configurados
    min_pares_activos_config = 10 # estos son los pares activos que se recalculan  por el sensor de rendimiento
    max_pares_activos = 10 # estos son los pares activos que se recalculan  por el sensor de rendimiento

    max_mem=1.4

    rankig_por_volumen = {}
    max_inversion_btc  = 0.20
    max_inversion_usdt = 0.20

    # invertido_btc=0   # se actualiza en auto_compra_vende
    # invertido_usdt=0  # se actualiza en auto_compra_vende
    # btc_operable=0
    # btc_transado=0
    # usdt_operable=0
    # usdt_trandado=0

    
    
    # variables globales de pares
    horas_deshabilitar_par = 4
    reserva_btc_en_usd=0
    reserva_usdt=0
    volumen_minimo_btc=0
    volumen_minimo_usd=0
    x_min_notional=1
    riesgo_tomar_perdidas=-7
    macd_min_rsi_verde=40
    macd_min_rsi__rojo=25
    inc_px_atrb = 30 
    valor_buscar_rsi_bajo=25
    resta_caza_rsi_bajo = 7
    macd_min_rsi_deep_verde=30
    macd_min_rsi_deep__rojo=24
    rb_gan_infima=1
    rb_gan_segura=1.5
    maxima_cantidad_de_pares_con_trades=1


    #variables multiplicadoras de patr
    x_neg_patr_comp_ant = -3
    x_neg_patr = -6
    x_gan_patr_sar = 3
    x_gan_patr_ema = 15

     
    ret_fibo = (0.236,0.382,0.5,0.618,0.786,1,1.618,2.618)


    ema_pendiente_maxima={'1m':0.0009,'5m': 0.00095 ,'15m':0.00098 ,'30m':0.00099 ,'1h':0.001 ,'2h':0.00102,'4h':0.00107,'1d':0.00111,'1w':0.00119,'1M':0.00156}
    
    #usada en tres_emas_favorables
    ema_poca_diferencia ={'1m':0.016 ,'5m': 0.083   ,'15m':0.04    ,'30m':0.5     ,'1h':1     ,'2h':1.5    ,'4h':2      ,'1d':3      ,'1w':4      ,'1M':5}

    falta_de_moneda={'USDT':False,'BTC':False}

    max_compras_simultaneas={'USDT':10,'BTC':10}
    pares_en_compras={'USDT':0,'BTC':0}

    escala_anterior ={'1m':'xx','5m':'1m' ,'15m':'5m' ,'30m':'15m','1h':'30m','2h':'1h','4h':'2h','1d':'4h','1w':'1d','1M':'1w'}
    escala_siguiente={'1m':'5m','5m':'15m','15m':'30m','30m':'1h' ,'1h':'2h' ,'2h':'4h','4h':'1d','1d':'1w','1w':'1M','1M':'xx'}
    escala_tiempo  ={'1m':60 ,'5m': 300 ,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,'1w':604800,'1M':2419200}
    escala_ganancia  ={'1m':.1 ,'5m': .5 ,'15m':.7,'30m':1,'1h':2,'2h':4,'4h':6,'1d':7,'1w':10,'1M':30}

    hay_pump = {'velas':5,'xatr':12,'xvol':12}

    #tiempo maximo que debe durar una entrada
    tiempo_maximo_trade  ={'1m':60 * 14,'5m': 300 * 14 ,'15m':900 * 14,'30m':1800 * 14,'1h':3600 * 14,'2h':7200 * 14,'4h':14400 * 14,'1d':86400 * 14,'1w':604800 * 14,'1M':2419200 * 14}
    
    #ganancia_minima en la que se comienza a considerar poner stoploss
    ganancia_minima ={'1m':0.1,'5m': 0.2 ,'15m':0.3 ,'30m':0.4 ,'1h':0.5 ,'2h':0.6,'4h':1.2,'1d':3,'1w':10,'1M':20}
    
    velas_hora  = {'1m':60 ,'5m': 12 ,'15m':4,'30m':2,'1h':1,'2h':0.5,'4h':0.25,'1d':0.041666667,'1w':0.005952381,'1M':0.001388889}

    #cuantas rango, volatilidad
    escala_prango = {'1m':1 ,'5m':1.5 ,'15m':2,'30m':2.5,'1h':2.7,'2h':2.9,'4h':3,'1d':4,'1w':5,'1M':6}

    escalas_comunes_rangos={'1h':50,'4h':40,'1d':30,'1w':15}

    #numero que indica el límite a partir del cual e adx se considera con fuerza
    confirmacion_adx = 20

    metricas = Metricas()

    def __init__(self,gestor_de_posicion=None):
        self.cargar_configuraciones_json()
        self.max_pares_activos = self.max_pares_activos_config
        #self.gestor_de_posicion: Gestor_de_Posicion = gestor_de_posicion
    
    def cargar_parametros_json_de_par(self):
        parconfig = self.cargar_config_json('par.json')
        #print(parconfig)
        if parconfig != None:
            try:
                VariablesEstado.reserva_btc_en_usd        = parconfig[0]['reserva_btc_en_usd']
                VariablesEstado.reserva_usdt              = parconfig[0]['reserva_usdt']
                VariablesEstado.volumen_minimo_btc        = parconfig[0]['volumen_minimo_btc']
                VariablesEstado.volumen_minimo_usd        = parconfig[0]['volumen_minimo_usd']
                VariablesEstado.x_min_notional            = parconfig[0]['x_min_notional']
                VariablesEstado.riesgo_tomar_perdidas     = parconfig[0]['riesgo_tomar_perdidas']
                VariablesEstado.inc_px_atrb               = parconfig[0]['inc_px_atrb'] 
                VariablesEstado.confirmacion_adx          = parconfig[0]['confirmacion_adx']    
                VariablesEstado.macd_min_rsi_verde        = parconfig[0]['macd_min_rsi_verde']    
                VariablesEstado.macd_min_rsi__rojo        = parconfig[0]['macd_min_rsi__rojo']
                VariablesEstado.valor_buscar_rsi_bajo     = parconfig[0]['valor_buscar_rsi_bajo']
                VariablesEstado.resta_caza_rsi_bajo       = parconfig[0]['resta_caza_rsi_bajo'] 
                VariablesEstado.macd_min_rsi_deep_verde   = parconfig[0]['macd_min_rsi_deep_verde'] 
                VariablesEstado.macd_min_rsi_deep__rojo   = parconfig[0]['macd_min_rsi_deep__rojo'] 
                VariablesEstado.rb_gan_infima             = parconfig[0]['rb_gan_infima']   
                VariablesEstado.rb_gan_segura             = parconfig[0]['rb_gan_segura'] 
                VariablesEstado.ema_pendiente_maxima      = parconfig[0]['ema_pendiente_maxima'] 
                VariablesEstado.horas_deshabilitar_par    = int(parconfig[0]['horas_deshabilitar_par'])
                VariablesEstado.max_compras_simultaneas   = parconfig[0]['max_compras_simultaneas']
                VariablesEstado.max_inversion_btc         = float(parconfig[0]['max_inversion_btc'])
                VariablesEstado.max_inversion_usdt        = float(parconfig[0]['max_inversion_usdt'])
                VariablesEstado.hay_pump                  = parconfig[0]['hay_pump'] 
                VariablesEstado.x_neg_patr                = float(parconfig[0]['x_neg_patr'])
                VariablesEstado.x_gan_patr_sar            = float(parconfig[0]['x_gan_patr_sar'])
                VariablesEstado.x_gan_patr_ema            = parconfig[0]['x_gan_patr_ema'] 
                VariablesEstado.x_neg_patr_comp_ant       = parconfig[0]['x_neg_patr_comp_ant'] 
                VariablesEstado.maxima_cantidad_de_pares_con_trades = parconfig[0]['maxima_cantidad_de_pares_con_trades'] 
            except Exception as e:
                print ( "cargar_parametros_json_de_par:",str(e) )     
                




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

    
    def cargar_configuraciones_json(self):
        self.cargar_parametros_json_de_par()
        self.cargar_parametros_de_config_json()
    
    def cargar_parametros_de_config_json(self):
        config = self.cargar_config_json('config.json')
        try:
            if config != None:
                self.trabajando = bool(config[0]['trabajando'])
                self.max_pares_activos_config = int(config[0]['max_pares_activos'])
                self.min_pares_activos_config = int(config[0]['min_pares_activos'])
                self.log_level = int(config[0]['log_level'])
                self.mostrar_cola = int(config[0]['mostrar_cola'])
        except  Exception as ex:
            print(str(ex))    

    def cargar_config_json(self,archivo):
        with open(archivo,'r') as f:
            try:
                config = json.load(f)
            except  Exception as e:
                print(str(e))
                config = None   
            f.close() 
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
                #esc=escala
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