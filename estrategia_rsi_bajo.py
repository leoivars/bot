#from abc import ABC,abstractmethod
from datetime import timedelta
import time

from pymysql.constants.ER import NO
from funciones_utiles import strtime_a_obj_fecha,variacion_absoluta
from mercado_back_testing import Mercado_Back_Testing
from acceso_db_sin_pool_conexion import Conexion_DB
from acceso_db_sin_pool_funciones import Acceso_DB

from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from binance.client import Client #para el cliente



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

        self.cantidad_compra_anterior=1
        self.precio_salir_derecho_compra_anterior=34224.30


    def decision_de_compra(self):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        
        comprar= False
        
        if not comprar:
            for esc in ['1m']:
                ret = self.buscar_rsi_bajo(esc)
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

    def buscar_rsi_bajo(self,escala):   
        ret=[False,'xx']
        self.log.log('0. buscar_rsi_bajo',escala)
        ind: Indicadores =self.ind
        
        pemas = ind.pendientes_ema(escala,8,2)
        pemas_ok = (pemas[0] > 0 and pemas[1] > 0  ) #la pendiente de la penultima ema 8 positiva
        self.log.log(f'{pemas_ok} <--pemas_ok  pemas -->{pemas}')
        
        if pemas_ok:
            
            if self.filtro_de_diferencias_de_compra(escala):
                rsi_min,rsi_min_pos,rsi= ind.rsi_minimo_y_pos(escala,20)
                self.log.log(f'{escala} rsi_min {rsi_min} pos {rsi_min_pos} rsi {rsi}')
                if rsi_min <39 and 2 < rsi_min_pos < 15:
                    self.log.log('1.rsi_bajo_cercano')
                    sar = ind.sar(escala)
                    if sar < self.precio:
                        self.log.log('2.Sar OK')
                        ret = [True,escala,'buscar_rsi_bajo']

        return ret 

    def filtro_de_diferencias_de_compra(self,escala):
        ind:Indicadores=self.ind
        emas_ok = ind.ema_rapida_mayor_lenta(escala,50,200)
        dmr = -0.49 if emas_ok else -1.47  #dmc = diferencia minima compra
        _,var_px_rsi = ind.buscar_precio_max_rsi(escala,57,55)
        ok_var_px_rsi = (var_px_rsi < dmr )
        self.log.log(f'{ok_var_px_rsi} <--ok_para_entrar:  dmr {dmr} < {var_px_rsi} variacion px ')   

        if self.cantidad_compra_anterior > 0:
            self.log.log('pxcompant,px',self.precio_salir_derecho_compra_anterior, self.precio)
            vpa = variacion_absoluta( self.precio_salir_derecho_compra_anterior, self.precio  )
            ok_vpa = (emas_ok and vpa < -0.49) or (not emas_ok and vpa < -1.47)
            self.log.log(f'{ok_vpa} <--ok_vpa: emas_ok --> {emas_ok}, var_px_comp_ant {vpa}') 
        else:
            ok_vpa = True

        return ok_var_px_rsi and ok_vpa #ok en la variacion del precio por rsi y la variacion del precio de la compra anterior    


    

        


    

            

        
        
        
        
        
        
       


if __name__=='__main__':
    from variables_globales import Global_State
    from gestor_de_posicion import Gestor_de_Posicion
    from binance.client import Client #para el cliente
    from pws import Pws
    
    log=Logger(f'estrategia_{time.time()}.log')
    pws=Pws()
 
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn)

    client = Client(pws.api_key, pws.api_secret)
    p = Gestor_de_Posicion(log,client,conn)
    g = Global_State(p)
    

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    fecha_fin =  strtime_a_obj_fecha('2021-07-01 04:00:00-03:00')
    fin_test  =  strtime_a_obj_fecha('2021-07-01 15:00:00-03:00')
    pares=['BTCUSDT']
    observaciones='  buscar_dos_emas_rsi '
    escalas = ['1m','5m','15m','30m','1h','2h','4h','1d','1w']
    #escalas = ['1m','5m','15m','30m','1h']

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
        log.log('fecha:',txtf)
        estrategia.precio = estrategia.ind.precio('1m')
        if not comprado:
            if estrategia.decision_de_compra():
                log.log ('gogogo-->',txtf,estrategia.escala_de_analisis,estrategia.par)
                comp_px=estrategia.precio_de_compra()
                comp_stop_loss = estrategia.stoploss()
                comprado = True
                gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))
        else:
            px_vta=estrategia.precio
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


        m.avanzar_tiempo(un_minuto)
        m.actualizar_mercados()    

    log.log (f'----->Fin Simulación ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas}')    
    log.log (f'observaciones: {observaciones}')
