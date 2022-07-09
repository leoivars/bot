import sys
sys.path.append('..')  

from estrategia import Estrategia
from datetime import timedelta
import time
from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing
from variables_globales import Global_State
from logger import Logger
from binance.client import Client #para el cliente
from pws import Pws


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

 