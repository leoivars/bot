#from abc import ABC,abstractmethod
from datetime import timedelta
import time

from pymysql.constants.ER import NO
from funciones_utiles import strtime_a_obj_fecha, timestampk_to_strtime
from mercado_back_testing import Mercado_Back_Testing
from acceso_db_conexion import Conexion_DB
from acceso_db import Acceso_DB
from variables_globales import VariablesEstado
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra


class Estrategia():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    def __init__(self,par,log,estado_general, mercado):
        self.log: Logger = log
        self.g: VariablesEstado = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        self.escala_de_analisis ='?'
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def decision_de_compra(self):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        ind = self.ind
        comprar= False
        
        if not comprar:
            for esc in ['1m','15m','1h']:
                ret = self.buscar_rsi_bajo(esc)
                if ret[0]:
                    #if ind.control_de_inconsistemcias(esc) == -1: #no hay inconsitencias
                    self.escala_de_analisis = ret[1]
                    self.sub_escala_de_analisis = ret[1]
                    self.analisis_provocador_entrada='buscar_rsi_bajo'
                    comprar = True
                    break                

        return comprar 

    def decision_venta(self,pxcompra,gan_min,escala=None):
        if escala is None:
            escala = self.escala_de_analisis
        px = self.ind.precio(escala)    
        gan=self.g.calculo_ganancia_porcentual(pxcompra, px )
        if gan >gan_min and self.ind.ema_rapida_menor_lenta(self.g.zoom_out(escala,1),9,20):
            ret = True
        elif gan> 0 and self.ind.sar(escala) > px:
            ret = True
        else:

            ret = False

        return ret        

    def precio_de_compra(self):
        px,_=self.calculador_px_compra.calcular_precio_de_compra('ema_9',self.escala_de_analisis)
        return px

    def precio(self,escala=None):
        if escala is None:
            escala = self.escala_de_analisis
        return self.ind.precio(escala)

        

    def stoploss(self):
        cvelas = 120
        atr = self.ind.atr(self.escala_de_analisis) 
        pmin = self.ind.min(self.g.zoom_out(self.escala_de_analisis,1),cvelas)
        #minimo encontrado  menos atr * 2
        sl = pmin - atr * 2 
        return sl

    def buscar_rsi_bajo(self,escala):   
        ret=[False,'xx']
        #self.log.log('0. buscar_rsi_bajo',escala)
        ind = self.ind
        rsi = ind.rsi(escala)
        #self.log.log(f'_.rsi {escala} {rsi}')
        if rsi < 36:
            #defino patron
            patrones = self.determinar_patron_rsi()
            for p in patrones:
                if p['escala']==escala:
                    ok, salida_log = ind.detectar_patron_rsi(p)
                    self.log.log(m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S') ,  salida_log)
                    if ok:
                        #self.log.log('1.rsi_sar_OK')
                        ret = [True,escala,'buscar_rsi_bajo']
        return ret    

    def determinar_patron_rsi(self):
        ind= self.ind
        #p= {45: 20, 35: 1, 30: 1, 25: 1, 20: 0, 'rsi': 34}
        #p= {45: 17, 35: 9, 30: 7, 25: 5,  20: 3, 'rsi': 34}    
        #p= {45: 30, 35: 21, 30: 12, 25: 5,  20: 2, 'rsi': 34}
        ##  una entrada ne 4 horas muy linda   ###p= {45: 30, 35: 21, 30: 12, 25: 5, 20: 2, 'rsi': 36}
        #p= {45: 40, 35: 20, 30: 10, 25: 5, 20: 2, 'rsi': 35}
        #p= { 45: 18, 35: 11, 30: 10, 25: 8, 20: 3, 'escala': '15m' ,'cvelas': 20,'rsi': 20}
        
        p=[ {45: 38, 35: 21, 30: 12, 25: 9,  20: 2, 'escala': '15m' ,'cvelas': 55, 'rsi': 20},
            {45: 37, 35: 16, 30: 9,  25: 2,  20: 0, 'escala': '1h', 'cvelas': 50, 'rsi': 26}, 
            {45: 24, 35: 20, 30: 18, 25: 10, 20: 1, 'escala': '1h', 'cvelas': 30,'rsi': 23},
            {45: 26, 35: 20, 30: 13, 25: 9,  20: 5, 'escala': '1m' ,'cvelas': 30,'rsi': 26}
          ] 
        
        #p=[{45: 26, 35: 20, 30: 13, 25: 9, 20: 5, 'escala': '1m' ,'cvelas': 30,'rsi': 26}]  
          #{45: 26, 35: 20, 30: 13, 25: 9, 20: 5, 'rsi': 25.72818080486207}
        # casi ok #  p= {45: 24, 35: 20, 30: 18, 25: 10, 20: 1, 'escala': '1h', 'cvelas': 30,'rsi': 23}
        if ind.ema_rapida_mayor_lenta('1d',9,55):
            if ind.ema_rapida_mayor_lenta('4h',9,55):
                if ind.ema_rapida_mayor_lenta('1h',9,55):
                    p=[{ 45: 20, 35: 12, 30: 6  ,25: 2, 20: 0, 'escala': '15m' ,'cvelas': 40,'rsi': 35}]
                    
                    
        return p    


if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log')
    g = VariablesEstado()
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn.pool)
    

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    fecha_fin =  strtime_a_obj_fecha('2021-01-01 00:00:00')
    fin_test  =  strtime_a_obj_fecha('2021-06-21 23:59:00')
    pares=['BTCUSDT']
    escalas = ['1m']
    escalas_mercados = ['1m','5m','15m','30m','1h','2h','4h','1d','1w']

    m=Mercado_Back_Testing(log,g,db)
    m.inicar_mercados(fecha_fin,200,pares,escalas_mercados)
    estrategia = Estrategia('BTCUSDT',log,g,m)

    un_minuto = timedelta(minutes=1)
    tres_minutos = timedelta(minutes=3)
    cinco_minutos = timedelta(minutes=5)
    diez_minutos = timedelta(minutes=10)
    
    comprado=False
    comp_px = 0
    comp_stop_loss =0
    ganancia =0
    gananciap =0
    entradas=0
    ganadas=0
    perdidas=0
    cantidad=0.0001
    gan_min=0

    sql ='select open_time from velas where id_par_escala=1   and rsi < 30 order by open_time'

    for par in pares:
        for esc in escalas:
            id_par_escala=db.get_id_par_escala(par,esc)
            sql=f'select open_time from velas where id_par_escala={id_par_escala}  and rsi < 60 order by open_time'
            cursor=db.ejecutar_sql_ret_cursor(sql)




    comprado=False
    comp_px = 0
    comp_stop_loss =0
    ganancia =0
    gananciap =0
    entradas=0
    ganadas=0
    perdidas=0
    cantidad=0.0001
    gan_min=0