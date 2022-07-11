from indicadores2 import Indicadores #Clase que toma datos de las velas del exchange y produce información (la version1 deprecated)
from logger import Logger #clase para loggear
#from Monitor_precios_ws import MonitorPreciosWs
import time
from pws import Pws
from binance.client import Client #para el cliente

class Pool_Indicadores:
    ind_pool={} #pool de indicadores. Se ponen aca para que todos los objetos de la clase puedan acceder a los indicadores
    client= None
    log =None
    btc_apto_para_altcoins = False
    btc_alcista = {'1d':False,'4h':False,'1h':False,'15m':False,'5m':False} 
    btc_macd_ok = {'1d':False,'4h':False,'1h':False,'15m':False,'5m':False} 
    btc_en_rango = False
    btc_rsi_ok = False
    btc_con_velas_verdes = True 
    btc_con_pendiente_negativa = True
    
    def __init__(self,log,mo_pre,estado_general):

        self.log=log
        self.estado_general = estado_general
        
        self.client=None
        self.crear_cliente()

        self.indicador('BTCUSDT')
        self.mo_pre : MonitorPreciosWs = mo_pre
        

    def crear_cliente(self):
        if self.client != None:
            self.log.err( "Re creando Cliente")
            time.sleep(35)
            self.client = None
            del self.client 
        pws=Pws()
        while self.estado_general.trabajando:
            try:
                self.client= Client(pws.api_key, pws.api_secret, { "timeout": (10, 27)})  #timeout=(3.05, 27
                break
            except Exception as e:
                time.sleep(35)
                self.log.err( "XXX No se puede crear Cliente",str(e))
                self.client = None
                del self.client     

    def indicador(self,par):
        if not par in self.ind_pool:
            self.ind_pool[par]=Indicadores(par,self.log,self.estado_general,self.client)
        return self.ind_pool[par]    

    def eliminar_indicador(self,par):
        if par in self.ind_pool:
            self.ind_pool[par] = None
            del self.ind_pool[par]
    def estado_cola(self):
        primer_key_disponible =  list( Pool_Indicadores.ind_pool.keys() ) [0]
        ind_par: Indicadores = self.ind_pool[ primer_key_disponible ]
        return ind_par.mercado.actualizador_rest.cola.largo()

    def demora_cola(self):
        primer_key_disponible =  list( Pool_Indicadores.ind_pool.keys() ) [0]
        ind_par: Indicadores = self.ind_pool[ primer_key_disponible ]
        return ind_par.mercado.actualizador_rest.cola.demora_de_cola()

    def mostrar_cola(self):
        primer_key_disponible =  list( Pool_Indicadores.ind_pool.keys() ) [0]
        ind_par: Indicadores = self.ind_pool[ primer_key_disponible ]
        return ind_par.mercado.actualizador_rest.cola.mostrar_cola()

    def loggeame_la_cola(self):
        self.log.log(self.mostrar_cola())

    def morir(self):
        for i in Pool_Indicadores.ind_pool.keys():
             Pool_Indicadores.ind_pool[i] = None

        Pool_Indicadores.ind_pool = {}  

    def actualizar_btc_con_pendiente_negativa(self):
        ind: Indicadores = self.indicador('BTCUSDT')
        ind.prioridad = 1
        pen=ind.pendientes_ema('1h',20,1)
        if pen[0] < 0:
            Pool_Indicadores.btc_con_pendiente_negativa = True
        else:
            Pool_Indicadores.btc_con_pendiente_negativa = False

    def actualizar_btc_alcista(self):
        btc: Indicadores = self.indicador('BTCUSDT')
        rapida=10
        lenta=55
        btc.prioridad = 1
        
        for esc in Pool_Indicadores.btc_alcista.keys():
            Pool_Indicadores.btc_alcista[esc] = btc.ema_rapida_mayor_lenta(esc,rapida,lenta)

    def actualizar_btc_macd_ok(self):
        btc: Indicadores = self.indicador('BTCUSDT')
        btc.prioridad = 1
        for esc in Pool_Indicadores.btc_alcista.keys():
            mdd = btc.macd_describir(esc) 
            Pool_Indicadores.btc_macd_ok[esc] = mdd[1]==1 # el histograma del macd está en amumento
        
       
    def actualizar_btc_con_velas_verdes(self):
        btc: Indicadores = self.indicador('BTCUSDT')
        btc.prioridad = 1
        escalas=['15m','1h','4h']
        positivas=0
        for esc in escalas:
            if btc.sentido_vela(esc,0) == 1: #vela en desarrollo positiva
                positivas += 1

        if positivas > 1: #o sea cuando es igual a 2 o 3 
            Pool_Indicadores.btc_con_velas_verdes = True
        else:
            Pool_Indicadores.btc_con_velas_verdes = False         

    def actualizar_parametros_btc(self):
        self.log.log( "actualizar_parametros_btc ini")
        self.actualizar_btc_alcista()
        self.actualizar_btc_macd_ok()
        self.actualizar_btc_en_rango()
        self.actualizar_btc_apto_para_altcoins()
        self.actualizar_btc_rsi_ok()
        self.actualizar_btc_con_velas_verdes()
        self.actualizar_btc_con_pendiente_negativa()
        self.log.log( "actualizar_parametros_btc fin")

    def actualizar_btc_rsi_ok(self):
        btc: Indicadores = self.indicador('BTCUSDT')
        btc.prioridad = 1
        escalas=['15m','1h','4h','1d']
        rsiok=True
        for esc in escalas:
            rsi=btc.rsi(esc)
            if rsi>70 or rsi<30:
                rsiok = False

        Pool_Indicadores.btc_rsi_ok = rsiok            

    def actualizar_btc_en_rango(self):
        escala='30m'
        btc: Indicadores = self.indicador('BTCUSDT')
        btc.prioridad = 1
        rango= False
        if 31 <= btc.rsi(escala) <= 69:
            if btc.pendiente_positiva_ema(escala,55):
                rango=True
            else:    
                hmacd = btc.macd_describir(escala)
                rango = (hmacd[1] == 1 or hmacd[0] == 1 ) #pendiente positiva o macd positivo
        #else:
        #    self.log.log("No_apto: filtro estado.general ",estado)  

        #actualizar el estado
        Pool_Indicadores.btc_en_rango = rango
    
    #def actualizar_btc_en_rango(self):
    #    escala='15m'
    #    cvelas=7 #7 velas
    #    btc: Indicadores = self.indicador('BTCUSDT')
    #    btc.prioridad = 1
    #    prango=btc.rango_minimo_promedio('1d',100)
    #    btc.prioridad = 1
    #    rango, rango_cvelas, cvelas_rango = btc.rango(escala,prango,cvelas)
    #    if cvelas_rango >= cvelas: 
    #       self.log.log("BTC_esta_en_un_rango_OK",prango,rango_cvelas,cvelas_rango)
    #        Pool_Indicadores.btc_en_rango = True
    #    else:
    #        #self.log.log("el_precio_esta_en_un_rango_NOok",rango,rango_cvelas,cvelas_rango)
    #        Pool_Indicadores.btc_en_rango = False       


    def actualizar_btc_apto_para_altcoins(self):
        btc: Indicadores = self.indicador('BTCUSDT')
        btc.prioridad = 1
        apto = True
        escala = "15m"

        sqz = btc.squeeze_describir(escala)
        if sqz[0] == -1: #pendiente negativa
            pend_negativa = not  btc.pendiente_positiva_ema(escala,55)
            adx = btc.adx(escala)
            if pend_negativa and adx[0]> 23 and adx[1] > 0: #pendiente negativa con adx creciendo
                apto = False

        Pool_Indicadores.btc_apto_para_altcoins = apto
    
    
    # def actualizar_btc_apto_para_altcoins(self):
    #     btc: Indicadores = self.indicador('BTCUSDT')
    #     btc.prioridad = 2
        
    #     rsi= btc.rsi('15m') 
    #     pre= btc.precio('15m')
        
    #     rsi_min_15=30
    #     rsi_max_15=80
    #     rsi_max_1d=85
    #     rsi_max_1w=75
        

    #     apto=btc.pendiente_positiva_ema('15m',55)   
    #     #if not apto:
    #     #    self.log.log("pendiente_positiva_ema()",apto) 

    #     if apto:
    #         estado=self.mo_pre.estado_general('BTC')
    #         tot = estado['nobajando'] + estado['bajando']
    #         try:
    #             if estado ['nobajando'] / tot < 0.40: #nobajando debe ser mayor o igual al 55 de todos los pares detectados contra btc
    #                 apto = False
    #                 self.log.log("No_apto: filtro estado.general ",estado)        
    #         except:
    #             apto = False

    #     if apto:
    #         if rsi < rsi_min_15 or rsi > rsi_max_15 :
    #             apto= False
    #             self.log.log("filtro btc.rsi('15m') rsi, rsi_max_15, rsi_min_15,pre",rsi,rsi_min_15,rsi_max_15,pre)
        
    #     if apto:
    #         rsi = btc.rsi('1d')
    #         if rsi > rsi_max_1d and btc.compara_rsi('1d',1)[0]>=0:
    #             apto= False
    #             self.log.log("No_apto: filtro btc.rsi('1d') >",rsi_max_1d,rsi)
        
    #     if apto:
    #         rsi = btc.rsi('1w') 
    #         if rsi > rsi_max_1w and btc.compara_rsi('1w',1)[0]>=0:
    #             apto= False
    #             self.log.log("No_apto: filtro btc.rsi('1w') ",rsi_max_1w,rsi)
        

        #self.log.log('btc_apto_para_altcoins',apto) 
        
        #Pool_Indicadores.btc_apto_para_altcoins = apto

        

        

        

