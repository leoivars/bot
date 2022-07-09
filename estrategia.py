#from abc import ABC,abstractmethod
from asyncore import loop
from datetime import timedelta
import time

from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing

from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from binance.client import Client #para el cliente
from fpar.filtros import filtro_parte_baja_rango, filtro_xvolumen_de_impulso,filtro_dos_emas_positivas,filtro_parte_alta_rango,filtro_de_rsi_minimo_cercano,filtro_tres_emas_positivas
from fpar.filtros import filtro_ema_positiva
from fpar.ganancias import calculo_ganancias,precio_de_venta_minimo


from pws import Pws

class Estrategia():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    def __init__(self,par,log,estado_general, mercado):
        self.nombre='parte_baja_ema_rsi'
        self.log: Logger = log
        self.g: Global_State = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        self.escala_de_analisis ='?'
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        
        #print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def decision_de_compra(self,escala,cvelas_rango,coef_bajo,ema):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        return self.filtros_decision(escala,cvelas_rango,coef_bajo,ema)

    def decision_venta(self,pxcompra,gan_min,escala):
        ind: Indicadores =self.ind

        #no decido vender si no estoy al menos en ganancia minima
        gan =   calculo_ganancias(self.g,pxcompra,ind.precio(escala))   
        gan_min = self.g.ganancia_minima[escala]
        if gan < gan_min:
            return False
        
        #no vendo si  el precio no es bajista y no he superado la ganancia minima multiplicada 
        precio_bajista = ind.el_precio_es_bajista(escala)
        if gan < gan_min * 3 and not precio_bajista:
            return False

        self.log.log(f'gan_min {gan_min} gan {gan} px_bajista {precio_bajista}' ) 
        marca_salida='S>>>'    

        rsi_max,rsi_max_pos,rsi = ind.rsi_maximo_y_pos(escala,5)
        self.log.log(f'rsi {rsi} rsi_max {rsi_max} rsi_max_pos {rsi_max_pos}')
        
        if rsi_max > 60 and rsi_max > rsi and 1<= rsi_max_pos <= 3 and precio_bajista:
            self.log.log(f'{marca_salida} rsi_max > 70 {rsi_max} ,precio_bajista')
            return True
        
        return False

    def precio_de_compra(self,escala):
        return self.precio(escala)

    def precio(self,escala=None):
        if escala:
            return self.ind.precio(escala)
        else:    
            return self.ind.precio_mas_actualizado()

    def decision_recompra(self,escala,precio_compra):
        ''' He comprado y el precio ha bajado. Si es suficientemente bajo, tomo la desición de hacer otra compra.
            No tengo claro si esta desición es parte de la estrategia o la manejo por fuera.
            ¿La decisión de compra es un stoploss fracasado?
        '''
        gan_limite = self.g.escala_ganancia[escala] * -4
        gan = self.g.calculo_ganancia_porcentual(precio_compra,self.precio())
        vol_calmado = self.ind.volumen_calmado(escala,2)
        
        self.log.log(f'gan_limite {gan_limite} gan {gan} vol_calmado {vol_calmado}')

        ret = gan < gan_limite and vol_calmado
        
        return ret           

    def stoploss(self,escala):
        sl = self.ind.minimo(escala,cvelas=3)  
        #recorrido = self.ind.recorrido_maximo(escala,290)
        precio = self.precio()
        if sl > precio:
            sl = precio - self.ind.recorrido_promedio(escala,50)
        return sl

    def stoploss_subir(self,sl_actual,pxcompra):
        #minimo = self.ind.minimo(self.escala_de_analisis,cvelas=3)  
        px_salir_derecho = precio_de_venta_minimo(self.g,0.1,pxcompra)
        precio = self.precio()
        sl = 0
        if precio > px_salir_derecho :
            sl = px_salir_derecho + (  (precio - px_salir_derecho) /2 )

        if sl > sl_actual:
            self.log.log(f'sl de {sl_actual} --> {sl}')
        else:    
            sl = sl_actual    

        return sl    

    def filtros_decision(self,escala,cvelas_rango=90,porcentaje_bajo=.2,ema_per=5):
        ret=False
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):
            if filtro_ema_positiva(self.ind,self.log,escala,ema_per):
                if filtro_de_rsi_minimo_cercano(self.ind,self.log,escala,rsi_inferior=30,pos_rsi_inferior=(2,5),max_rsi=55):
                    ret = True
        return ret    

def cerrar_opercion(gan,ganancia,gananciap,ganadas,perdidas,entradas,comprado):
    ganancia += g.calculo_ganancia_total(comp_px,px_vta,cantidad)
    gananciap+=gan
    if gan >0:
        ganadas+=1
    else:
        perdidas+=1    
    entradas+=1
    log.log (f'----->Termina operacion gan {gan} entradas {entradas}') 
    comprado=False


if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log','/mnt/ramdisk/')
    log_resultados=Logger(f'estrategia_resultados.log','/mnt/ramdisk/')
    pws=Pws()
    
    from pymysql.constants.ER import NO
   
    from acceso_db_sin_pool_conexion import Conexion_DB_Directa
    from acceso_db_sin_pool_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB

    client = Client(pws.api_key, pws.api_secret)

    conn=Conexion_DB_Directa(log)                          
    fxdb=Acceso_DB_Funciones(log,conn)        
    db = Acceso_DB(log,fxdb)   

    g = Global_State()

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    #parametros de al simulacion
    trades=[]
    escalas=['1m']
    escalas_mercados=['1m']
    emas12=[(5,10)]
    vemas=[10]
    vcvelas=[200]
    
    #coficientes_bajo=[0.786,0.618,.5,0.382,0.236]
    coficientes_bajo=[0.382]
    #emas12=[(4,7)]
    xmin_impulsos = [25]
    #xmin_impulsos = [15]
    fecha_fin =  strtime_a_obj_fecha('2022-05-28 00:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    fin_test  =  strtime_a_obj_fecha('2022-06-02 16:20:00')
    #fecha_fin =  strtime_a_obj_fecha('2022-03-14 00:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    #fin_test  =  strtime_a_obj_fecha('2022-03-16 00:00:00')
    txt_test = 'baja_emarl_xvolumen'


    #lista_pares=['XMRUSDT','BTCUSDT','CELRUSDT']
    #lista_pares=[ 'ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']
    lista_pares=['BTCUSDT']
    #lista_pares=['CELRUSDT','ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']

    db.backtesting_borrar_todos_los_resultados()

    for par in lista_pares:

        pares=[par]
        m=Mercado_Back_Testing(log,g,db)
        estrategia = Estrategia(par,log,g,m)
        un_minuto = timedelta(minutes=1)
        tres_minutos = timedelta(minutes=3)
        cinco_minutos = timedelta(minutes=5)
        diez_minutos = timedelta(minutes=10)
        una_hora = timedelta(hours=1)
        dos_horas = timedelta(hours=2)
        

        tot= len(escalas) * len (xmin_impulsos) * len(vemas) * len(coficientes_bajo) * len(vcvelas)
        c=0

    esc='1m' 
    cvelas=200
    
    coef_bajo=.5
    ema=5

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
              
    m.inicar_mercados(fecha_fin,300,pares,escalas_mercados)
    while m.fecha_fin < fin_test:
        txtf = m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')
        print(f'-------------------------------------------------{txtf}----{esc}--cvelas{cvelas}-ema{ema}--coef {coef_bajo}-------')
        
        if not comprado and trades:          # veo si puedo volver de un trade anterior 
            px_vta = estrategia.precio()
            comp_px = trades[-1]
            gan = g.calculo_ganancia_porcentual(comp_px,px_vta)
            if gan >0 :
                comprado = True
                log.log ('recupero  gan {gan} entradas {entradas}')
                trades.pop()

        if not comprado:
            if estrategia.decision_de_compra(esc,cvelas,coef_bajo,ema):
                comp_px = estrategia.precio_de_compra(esc)
                comp_stop_loss = estrategia.stoploss(esc)
                comprado = True
                #gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))
                log.log (f'gogogo-->   entradas {entradas}     ',txtf,estrategia.escala_de_analisis,estrategia.par)
                log.log (f'comp_px {comp_px}, comp_sto_loss {comp_stop_loss}')
        else: # estoy comprado
            px_vta = estrategia.precio(esc)
            vendido = False
            recomprado = False
            gan = g.calculo_ganancia_porcentual(comp_px,px_vta)
            log.log (f'{txtf} -comprado-> {gan}%  sl {comp_stop_loss} ')    
            
            if estrategia.decision_recompra(esc,comp_px):
                log.log ('recompra gan {gan} entradas {entradas}')
                recomprado = True
                comprado = False
                trades.append(comp_px)
                    
            if not recomprado and not vendido and  estrategia.decision_venta(comp_px,gan_min,esc):
                vendido = True

            if vendido:
                log.log ('venta  gan {gan} entradas {entradas}')
                gananciap += gan
                if gan >0:
                    signo='+'
                    ganadas+=1
                else:
                    perdidas+=1 
                    signo='-'   
                entradas+=1
                
                log.log (f'----->Termina operacion {signo} gan {gan} entradas {entradas}') 
                comprado=False
                
        m.avanzar_tiempo(un_minuto)
        m.actualizar_mercados()  

    if comprado:   #guardo compra abierta    
        
        gananciap+=gan
        if gan >0:
            ganadas+=1
        else:
            perdidas+=1    
        entradas+=1
        log.log (f'----->Termina operacion gan {gan} entradas {entradas}') 
        comprado=False

    txt_log_paremtros = f'{txt_test}: escala={esc} cvelas={cvelas} coef_bajo {coef_bajo} ema {ema}  fechas {fecha_fin}-{fin_test}'
    txt_log_datos     = f'{par} ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas} trades {len(trades)} {trades} '  
    txt_log_fin = txt_log_datos,txt_log_paremtros
    log.log(txt_log_fin)
    log_resultados.log (txt_log_fin) 
    db.backtesting_agregar_resultado(par,txt_log_paremtros,ganadas,perdidas,gananciap)

 