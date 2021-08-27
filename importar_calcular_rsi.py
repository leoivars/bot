#from abc import ABC,abstractmethod
from datetime import timedelta
import time

from pymysql.constants.ER import NO
from funciones_utiles import strtime_a_obj_fecha,timestampk_to_strtime
from mercado_back_testing import Mercado_Back_Testing
from acceso_db_conexion_mysqldb import Conexion_DB
from acceso_db_mysqldb import Acceso_DB
from variables_globales import VariablesEstado
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra


class Actualizador():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    def __init__(self,par,log,estado_general, mercado):
        self.log: Logger = log
        self.g: VariablesEstado = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        
    def rsi(self,escala):
        rsi = self.ind.rsi(escala)
        return rsi


        #codigo para actualizar el rsi en la base


if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log')
    g = VariablesEstado()
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn)
    

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    fecha_fin =  strtime_a_obj_fecha('2020-10-01 00:00:00')
    pares=['BTCUSDT']
    #escalas = ['15m']
    escalas = ['1m','5m','15m','30m','1h','2h','4h','1d','1w']
    #escalas = ['30m','1h','2h','4h','1d','1w']
    m=Mercado_Back_Testing(log,g,db)
    m.inicar_mercados(fecha_fin,200,pares,escalas)
    act = Actualizador('BTCUSDT',log,g,m)

    for par in  pares:
        for esc in escalas:
            idpar_esc=db.get_id_par_escala(par,esc)
            while m.avanzar_vela(par,esc,idpar_esc):
                rsi = act.rsi(esc)
                db.actualizar_velas_rsi(idpar_esc,m.open_time_ultima_vela(par,esc),rsi)
                print(par,esc,m.fecha_fin_tsb,timestampk_to_strtime(m.fecha_fin_tsb),rsi)
            db.commit()    
            

