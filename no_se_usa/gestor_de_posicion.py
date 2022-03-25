
from logger import Logger
import time
from no_se_usa.acceso_db import Acceso_DB
#from pool_indicadores import Pool_Indicadores
from no_se_usa.acceso_db import Acceso_DB
from binance.client import Client
from funciones_utiles import cpu_utilizada
from acceso_db_conexion import Conexion_DB


class Gestor_de_Posicion:
    ''' Clase encargada de gestionar la posicion: Cuanto tengo en usdt, cuanto tengo en btc, cuanto tengo expuesto 
    y determinar el tamaño de la compra '''

    def __init__(self,log,client,conn): #ind...>indicadores previamente instanciado y funcionando
        self.log = log
        self.client = client
        self.db =  Acceso_DB(log,conn.pool)

    def tomar_cantidades(self,parametro_asset):
        
        ret=0
        ejecutado=False
        while not ejecutado:
            #self.__empezar('tomar_cantidad_disponible')
            try:
                balance = self.client.get_asset_balance(asset=parametro_asset)
                print(balance)
                ret=float(balance['free']),float(balance['locked'])
                ejecutado=True
            except Exception as e:
                self.log.err( e )
                self.log.err('Error tomar_cantidad_disponible, esperando 10 segundos.')
                time.sleep(10)
            #self.__terminar()
        
        return ret      

    def actualizar_posicion(self):
        usdt_disponible,usdt_ordenes = self.tomar_cantidades('USDT')
        usdt_operable = usdt_disponible + usdt_ordenes
        usdt_transado = self.db.total_moneda_contra_en_trades('USDT')
        
        btc_disponible, btc_ordenes = self.tomar_cantidades('BTC')
        btc_comprado_para_trade = self.db.total_moneda_en_trades('BTC')
        btc_operable = btc_disponible + btc_ordenes - btc_comprado_para_trade 
        btc_transado = self.db.total_moneda_contra_en_trades('BTC')
        
        # print('usdt',usdt)
        # print('btc',btc)
        # print('contra_usdt')
        # print('invertido_btc',invertido_btc)
        # print('invertido_usdt',invertido_usdt)

        # esto está mal, hay que conservar esto valores dentro del gestor de posición propiamente dicho
        # no está bueno que tire los valores a otro lado.
        return btc_operable,btc_transado,usdt_operable,usdt_transado
    
#TEST

if __name__=='__main__':
    from pws import Pws
    from variables_globales import Global_State
    pws=Pws()
    client = Client(pws.api_key, pws.api_secret)
    #base de datos
    log = Logger('actualizar_info_pares_deshabilitados')
    conn=Conexion_DB(log)
    db=Acceso_DB(log,conn.pool)
    gp = Gestor_de_Posicion(log,client,db)
    g = Global_State(gp)
    #web soket de monitor de precios
    #mo_pre=MonitorPreciosWs(log)

    print(gp.actualizar_posicion())


