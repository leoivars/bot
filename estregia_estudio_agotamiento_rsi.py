#from abc import ABC,abstractmethod
from datetime import timedelta
import time
from funciones_utiles import strtime_a_obj_fecha, timestampk_to_strtime
from mercado_back_testing import Mercado_Back_Testing
from acceso_db_conexion_mysqldb import Conexion_DB
from acceso_db_mysqldb import Acceso_DB
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
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        self.escala_de_analisis ='?'
        #print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def super_decision_de_compra(self):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        ind = self.ind
        comprar= False
        
        if not comprar:
            for esc in ['1m']:
                p = ind.analisis_rsi2(esc,40,rsi=None,vela_ini=0)
                self.log.log (self.mercado.fecha_fin.strftime('%Y-%m-%d %H:%M:%S'), p )

              

        return comprar   ,p

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
        px,_=self.calculador_px_compra.calcular_precio_de_compra('mercado',self.escala_de_analisis)
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
        if sl > 10:
            sl = 10
        return sl


    def determinar_patron_rsi(self):
        ind= self.ind
        #p= {45: 20, 35: 1, 30: 1, 25: 1, 20: 0, 'rsi': 34}
        #p= {45: 17, 35: 9, 30: 7, 25: 5,  20: 3, 'rsi': 34}    
        #p= {45: 30, 35: 21, 30: 12, 25: 5,  20: 2, 'rsi': 34}
        ##  una entrada ne 4 horas muy linda   ###p= {45: 30, 35: 21, 30: 12, 25: 5, 20: 2, 'rsi': 36}
        p= {45: 40, 35: 20, 30: 10, 25: 5, 20: 2, 'rsi': 35}
        if ind.ema_rapida_mayor_lenta('1d',9,55):
            if ind.ema_rapida_mayor_lenta('4h',9,55):
                if ind.ema_rapida_mayor_lenta('1h',9,55):
                    p={ 45: 20, 35: 12, 30: 6  ,25: 2, 20: 0, 'rsi': 35}
                    
                    
        return p    


if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log')
    g = VariablesEstado()
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn)
    

    
    fecha_fin =  strtime_a_obj_fecha('2021-06-21 00:00:00')
    fin_test  =  strtime_a_obj_fecha('2021-06-22 00:00:00')
    pares=['BTCUSDT']
    escalas_mercados = ['1m','5m','15m','30m','1h','4h','1d']
    escalas = ['1m'] 
    escalas_mercados = ['1m','5m','15m','30m','1h','4h','1d']

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
    
    patron_ganancia=[]
    for par in pares:
        for esc in escalas:
            id_par_escala=db.get_id_par_escala(par,esc)
            sql=f'select open_time,rsi from velas where id_par_escala={id_par_escala}  and rsi between  21 and 22 order by open_time'
            cursor=db.ejecutar_sql_ret_cursor(sql)
            for reg in cursor:
                open_time=reg[0]
                m.actualizar_mercados_a_vela(open_time)
                txtf=  timestampk_to_strtime(  m.open_time_ultima_vela(par,esc)  )
                #print (txtf,'rsi',reg[1])
                
                estrategia.escala_de_analisis=esc
                c,p=estrategia.super_decision_de_compra()
                comp_px=estrategia.precio_de_compra()
                comp_stop_loss = estrategia.stoploss()
                comprado = True
                gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))

                vel=0

                while comprado and vel <60:
                    px_vta=estrategia.precio()
                    gan=g.calculo_ganancia_porcentual(comp_px,px_vta)
                    log.log (f'{txtf} -comprado-> {gan}% precio {px_vta}')
                    if estrategia.decision_venta(comp_px,gan_min) or px_vta < comp_stop_loss or vel > 10:
                        ganancia += g.calculo_ganancia_total(comp_px,px_vta,cantidad)
                        gananciap+=gan
                        if gan >0:
                            ganadas+=1
                        else:
                            perdidas+=1    
                        entradas+=1
                        
                        log.log (f'----->Termina operacion gan {gan} entradas {entradas}')
                        comprado = False
                    m.avanzar_tiempo(tres_minutos)
                    m.actualizar_mercados()     
                    txtf=  timestampk_to_strtime(  m.open_time_ultima_vela(par,esc) )
                    vel +=1
                patron_ganancia.append([p,gan])    


    patron_ganancia.sort(key=lambda x:x[1])
    for pg in patron_ganancia:
        log.log(pg)
    log.log (f'----->Fin Simulación ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas}')



    







