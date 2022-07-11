import sys
from tracemalloc import stop
sys.path.append('..')  

from estrategia02 import Estrategia
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

    
    #periodo larguísimo desde 47k a 27k
    # fecha_fin =  strtime_a_obj_fecha('2022-05-04 09:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    # fin_test  =  strtime_a_obj_fecha('2022-06-11 10:24:00')

    #periodo largo con altibajos y precio bajando en rango
    #descripcion_periodo='Bajada Mayo 22'
    #fecha_fin =  strtime_a_obj_fecha('2022-05-04 09:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    #fin_test  =  strtime_a_obj_fecha('2022-06-11 10:24:00')

    descripcion_periodo='Rango Mayo 10 Junio 09'
    fecha_fin =  strtime_a_obj_fecha('2022-05-10 00:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    fin_test  =  strtime_a_obj_fecha('2022-06-09 23:59:00')

    #descripcion_periodo='Mayo 22 8 días bajada'
    #fecha_fin =  strtime_a_obj_fecha('2022-05-04 08:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    #fin_test  =  strtime_a_obj_fecha('2022-05-12 05:00:00')
    
    # descripcion_periodo='Junio 22 un día bajada'
    # fecha_fin =  strtime_a_obj_fecha('2022-06-10 03:22:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    # fin_test  =  strtime_a_obj_fecha('2022-06-11 19:15:00')

    #descripcion_periodo='Junio 12 20 horas de bajada con trampa'
    #fecha_fin =  strtime_a_obj_fecha('2022-06-12 00:00:00')  
    #fin_test  =  strtime_a_obj_fecha('2022-06-12 20:00:00')
   
    #lista_pares=['XMRUSDT','BTCUSDT','CELRUSDT']
    #lista_pares=[ 'ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']
    lista_pares=['BTCUSDT']
    #lista_pares=['CELRUSDT','ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']

    #db.backtesting_borrar_todos_los_resultados()

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
              
    m.inicar_mercados(fecha_fin,1000,pares,escalas_mercados)
    while m.fecha_fin < fin_test:
        txtf = m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')
        print( f'                                                        {txtf}-------> ganancia= {gananciap} entradas {entradas} trades {len(trades)} {trades} '  )
        
        if not comprado and trades:          # veo si puedo volver de un trade anterior 
            px_vta = estrategia.precio()
            comp_px = trades[-1]
            gan = g.calculo_ganancia_porcentual(comp_px,px_vta)
            if gan >0 :
                comprado = True
                log.log ('-evento- recupero  gan {gan} entradas {entradas}')
                trades.pop()

        if not comprado:
            if trades:
                ultima_compra=trades[-1]
            else:
                ultima_compra=None

            if estrategia.decision_de_compra(esc,ultima_compra):
                comp_px = estrategia.precio_de_compra(esc)
                stoploss = 0
                comprado = True
                #gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))
                log.log (f'-evento- gogogo-->   entradas {entradas}     ',txtf,estrategia.escala_de_analisis,estrategia.par)
                log.log (f'comp_px {comp_px}, stop_loss {stoploss}')
        else: # estoy comprado
            px_vta = estrategia.precio(esc)
            vendido = False
            recomprado = False
            gan = g.calculo_ganancia_porcentual(comp_px,px_vta)
            log.log (f'{txtf} -comprado-> {gan}%  sl {stoploss} ')    
            
            if gan <0 and  estrategia.decision_recompra(esc,comp_px):
                log.log ('-evento- recompra gan {gan} entradas {entradas}')
                recomprado = True
                comprado = False
                trades.append(comp_px)

            # #establecimiento de stoploss
            # if stoploss == 0:
            #     sl = estrategia.stoploss(esc) 
            #     if sl < px_vta and  g.calculo_ganancia_porcentual(comp_px,sl) >0:
            #         stoploss = sl   
            # #control de stoploss        
            # elif px_vta <= stoploss:
            #     gan =  g.calculo_ganancia_porcentual(comp_px,stoploss)
            #     vendido = True
            #     log.log (f'-evento- stoploss tocado gan {gan} entradas {entradas}')
                    
            #venta        
            if not recomprado and not vendido and  estrategia.decision_venta(esc,comp_px):
                vendido = True

            # # subir stoploss
            # if not recomprado and not vendido and stoploss>0:
            #     sl = estrategia.stoploss_subir(esc,stoploss,comp_px)
            #     if  stoploss < sl < px_vta:
            #         gan =  g.calculo_ganancia_porcentual(comp_px,sl)
            #         log.log (f'-evento- stoploss_subido {stoploss} a {sl} gan {gan}  ')
            #         stoploss = sl

            if vendido:
                log.log (f'-evento- venta  gan {gan} entradas {entradas}')
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

    txt_log_paremtros = f'{descripcion_periodo}: escala={esc}  fechas {fecha_fin}-{fin_test}'
    txt_log_datos     = f'{par} ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas} trades {len(trades)} '  
    txt_log_fin = txt_log_datos + ' ' + txt_log_paremtros + ' ' + estrategia.file
    log_resultados.log (txt_log_fin) 
    db.backtesting_agregar_resultado(par,txt_log_fin,ganadas,perdidas,gananciap,len(trades))

 