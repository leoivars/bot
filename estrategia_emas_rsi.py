#from abc import ABC,abstractmethod
from datetime import timedelta
import time

from pymysql.constants.ER import NO
from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing
from acceso_db_sin_pool_conexion import Conexion_DB
from acceso_db_sin_pool_funciones import Acceso_DB
from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra


class Estrategia():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    def __init__(self,par,log,estado_general, mercado):
        self.log: Logger = log
        self.g: Global_State = estado_general
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
            for esc in ['1m']:
                ret = self.buscar_dos_emas_rsi(esc)
                if ret[0]:
                    #if ind.control_de_inconsistemcias(esc) == -1: #no hay inconsitencias
                    self.escala_de_analisis = ret[1]
                    self.sub_escala_de_analisis = ret[1]
                    self.analisis_provocador_entrada='buscar_dos_emas_rsi'
                    comprar = True
                    break                

        return comprar 

    def decision_venta(self,pxcompra,gan_min,escala=None):
        if escala is None:
            escala = self.escala_de_analisis
        px = self.ind.precio(escala)    
        gan=self.g.calculo_ganancia_porcentual(pxcompra, px )
        if gan >gan_min and self.ind.ema_rapida_menor_lenta(self.g.zoom_out(escala,1),9,20):
            self.log.log('venta--ema_rapida_menor_lenta')
            ret = True
        elif gan> 0 and self.ind.sar(escala) > px:
            self.log.log('venta--sar')
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

    def buscar_tres_emas_rsi(self,escala):   
        ret=[False,'xx']
        #self.log.log('0. buscar_rsi_bajo',escala)
        ind = self.ind
        rsi = ind.rsi(escala)
        #self.log.log(f'_.rsi {escala} {rsi}')
        if 40 < rsi < 70:
            if ind.variacion_px_actual_px_minimo(self.g.zoom_out( escala,3 ), 48)  < 10:
                if ind.tres_emas_favorables2(escala,9,20,55):
                    ret = [True,escala,'buscar_tres_emas_rsi']
        return ret  

    def buscar_dos_emas_rsi(self,escala):   
        ret=[False,'xx']
        #self.log.log('0. buscar_rsi_bajo',escala)
        ind = self.ind
        rsi = ind.rsi(escala)
        #self.log.log(f'_.rsi {escala} {rsi}')
        if 40 < rsi < 70:
            if ind.variacion_px_actual_px_minimo(self.g.zoom_out( escala,3 ), 48)  < 10:
                if ind.tres_emas_favorables2(escala,9,20,55):
                    ret = [True,escala,'buscar_dos_emas_rsi']
        return ret      

    

        


    

            

        
        
        
        
        
        
       


if __name__=='__main__':
    log=Logger(f'estrategia_emas_rsi{time.time()}.log')
    g = Global_State()
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn)
    

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    fecha_fin =  strtime_a_obj_fecha('2021-06-24 23:00:00')
    fin_test  =  strtime_a_obj_fecha('2021-06-26 11:00:00')
    pares=['BTCUSDT']
    observaciones='  buscar_dos_emas_rsi '
    #escalas = ['1m','5m','15m','30m','1h','2h','4h','1d','1w']
    escalas = ['1m','5m','15m','30m','1h']

    m=Mercado_Back_Testing(log,g,db)
    m.inicar_mercados(fecha_fin,250,pares,escalas)
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

    while m.fecha_fin < fin_test:
        txtf = m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')
        print (txtf)
        if not comprado:
            if estrategia.decision_de_compra():
                log.log ('gogogo-->',txtf,estrategia.escala_de_analisis,estrategia.par)
                comp_px=estrategia.precio_de_compra()
                comp_stop_loss = estrategia.stoploss()
                comprado = True
                gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))
        else:
            px_vta=estrategia.precio()
            gan=g.calculo_ganancia_porcentual(comp_px,px_vta)
            log.log (f'{txtf} -comprado-> {gan}%  px={px_vta}')
            if estrategia.decision_venta(comp_px,gan_min) or px_vta < comp_stop_loss:
                ganancia += g.calculo_ganancia_total(comp_px,px_vta,cantidad)
                gananciap+=gan
                if gan >0:
                    ganadas+=1
                else:
                    perdidas+=1    
                entradas+=1
                log.log (f'----->Termina op gan {gan} entradas {entradas} ganadas {ganadas} perdidas {perdidas} ganancia= {gananciap}')
                comprado = False


        m.avanzar_tiempo(tres_minutos)
        m.actualizar_mercados()    

    log.log (f'----->Fin Simulación ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas}')    
    log.log (f'observaciones: {observaciones}')
