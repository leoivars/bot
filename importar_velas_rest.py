# # -*- coding: UTF-8 -*-
# pragma pylint: disable=no-member

from logger import Logger
from velaset import VelaSet
from vela import Vela
from binance.client import Client
import time
import random
import traceback
from datetime import datetime,timedelta
from funciones_utiles import str_fecha_hora_a_timestamp, strtime_a_fecha, strtime_a_obj_fecha
from acceso_db_modelo import Acceso_DB

class Actualizador_Rest:
        
    def __init__(self,client,db,log):
        self.db: Acceso_DB  = db
        self.log = log
        self.actualizado={'1m':0,'3m':0,'5m':0,'15m':0,'30m':0,'1h':0,'2h':0,'4h':0,'1d':0,'1w':0,'1M':0}
        self.client: Client = client

     
    def control_de_inconsistemcias(self,escala):
        self.log.log('ini inconsistencia',self.par)
        ifea = self.velas[escala].inconsistencias()
        if ifea > -1:
            hora_fea = self.velas[escala].df.index[ifea]
            print('---> inconsitencai:',hora_fea)
            self.log.log('inconsistencia',self.par)
            self.actualizado[escala] = hora_fea /1000 -1
            self.carga_de_actualizacion_escala(escala)

        return ifea 
    
    
    def get_velas_from_exchange(self,par,escala,ini,fin):
            
        klines= None
        err=False
        try: 
            rango_fin=fin
            rango_ini=ini
            if escala=='1m':
                print('-----1m----')
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1MINUTE, rango_ini,rango_fin) 
            elif escala=='5m':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_5MINUTE, rango_ini,rango_fin) 
            elif escala=='3m':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_3MINUTE, rango_ini,rango_fin)     
            elif escala=='15m':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_15MINUTE, rango_ini,rango_fin) 
            elif escala=='30m':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_30MINUTE, rango_ini,rango_fin) 
            elif escala=='1h':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1HOUR, rango_ini,rango_fin ) 
            elif escala=='2h':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_2HOUR, rango_ini,rango_fin )     
            elif escala=='4h':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_4HOUR, rango_ini,rango_fin ) 
            elif escala=='1d':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1DAY, rango_ini,rango_fin)
            elif escala=='1w':
                klines =self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1WEEK, rango_ini,rango_fin) 
            elif escala=='1M':
                klines=self.client.get_historical_klines(par, Client.KLINE_INTERVAL_1MONTH, rango_ini,rango_fin)     

            #print ('klines',klines)
            if type(klines) is list:
                if len(klines)>0:
                    self.actualizar_db(par,escala,klines)
                    del klines
            else:
                err=True
            
        except Exception as e:
            #self.log.log( e  )
            txt_error = str(e)
            
            #tb = traceback.format_exc()
            #self.log.log( tb)
            #self.log.log('klines',klines,self.par,rango_pedido,rango_ini,rango_fin)
            err=True
            #self.crear_cliente() #boora y crea un nuevo cliente
            self.log.err( "...Error actualización",par,"._escala(",escala,"), rango(",ini,fin,"), --Err:",txt_error)

    def actualizar_db(self,par,escala,set_velas_web):
        id_par_escala = self.db.get_id_par_escala(par,escala)
        
        for vela_web in (set_velas_web):
            self.ingresar_vela(id_par_escala,vela_web)

        self.db.fxdb.commit()    

        print('cantidad de velas obtenidas:',len(set_velas_web))
    
    def ingresar_vela(self,id_par_escala,vela_web): 
        open_time=int(vela_web[0])
        open=float(vela_web[1])
        high=float(vela_web[2])
        low=float(vela_web[3])
        close=float(vela_web[4])
        volume=float(vela_web[5])
        close_time=int(vela_web[6])
        #print(open_time,open,high,low,close,volume,close_time)
        self.imprimir_vela(id_par_escala,open_time,open,high,low,close,volume,close_time)
        self.db.crear_actualizar_vela(id_par_escala,open_time,open,high,low,close,volume,close_time)
            

    def imprimir_vela(self,id_par_escala,open_time,open,high,low,close,volume,close_time):
        print(id_par_escala,open_time,strtime_a_fecha(open_time),open,high,low,close,volume,close_time)



if __name__=='__main__':
    from variables_globales import VariablesEstado
    from pws import Pws
    from pymysql.constants.ER import NO
    from acceso_db_sin_pool_conexion import Conexion_DB_Directa
    from acceso_db_sin_pool_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB

    client = Client()
    log=Logger('Importar_velas.log') 
    
    conn=Conexion_DB_Directa(log)                          
    fxdb=Acceso_DB_Funciones(log,conn)        
    db = Acceso_DB(log,fxdb)   
    
    act = Actualizador_Rest(client,db,log)

    # fini=str_fecha_hora_a_timestamp('2021-06-07 00:00:00') * 1000 
    # ffin=str_fecha_hora_a_timestamp('2021-06-07 00:59:00') * 1000

    # print(strtime_a_fecha(fini) )
    # print(strtime_a_fecha(ffin) )

    # print(fini,ffin)
    
    #pedido máximo en días por escala
    #deltas = {'2h':120}
    deltas = {'15m':15,'30m':30,'1h':60,'2h':120,'4h':240,'1d':1440,'1w':10080,'1M':43200}
    
    #UTC	2021-06-13T07:02:34Z
    ####  fini='2021-11-01 00:00:00' desde acá tengo  pares=['XMRUSDT','BTCUSDT','CELRUSDT']
    #fini='2021-11-01 00:00:00' pares=[ 'ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT','XMRUSDT','BTCUSDT','CELRUSDT']
    fini='2022-03-13 00:00:00'
    ffin='2022-03-13 23:59:59' 
    
    #pares=['BTCUSDT','BNBUSDT','XRPUSDT']
    #pares=['BTCUSDT','BNBUSDT']
    pares=[ 'ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT','XMRUSDT','BTCUSDT','CELRUSDT']
    # fini='202-01-01 00:00:00' 
    # ffin='2021-07-01 00:00:00' 
    obj_fini=strtime_a_obj_fecha(fini)
    obj_ffin=strtime_a_obj_fecha(ffin)
    

    for par in pares:
        for escala in deltas.keys():
            delta = deltas[escala]
            ini = obj_fini
            while True:
                fin = ini +  timedelta( days= delta ) 
                print(str(ini),'...',str(fin))
                act.get_velas_from_exchange(par,escala,str(ini),str(fin))
                #controlo condiciones de salida
                if fin >= obj_ffin:
                    break
                else:
                    ini= fin
                
        

