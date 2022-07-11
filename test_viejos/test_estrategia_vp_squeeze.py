import sys
sys.path.append('..')  

from estrategia_vp_squeeze import Estrategia
from datetime import timedelta
import time
from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing
from variables_globales import Global_State
from logger import Logger
from binance.client import Client #para el cliente
from pws import Pws
import os

if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log','/mnt/ramdisk/')
    log_resultados=Logger(f'estrategia_resultados.log','/mnt/ramdisk/')
    pws=Pws()
    
    from pymysql.constants.ER import NO
   
    from acceso_db_sin_pool_conexion import Conexion_DB_Directa
    from acceso_db_sin_pool_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB

    from periodos_a_analizar import Periodos_a_analizar

    #client = Client(pws.api_key, pws.api_secret)

    conn=Conexion_DB_Directa(log)                          
    fxdb=Acceso_DB_Funciones(log,conn)        
    db = Acceso_DB(log,fxdb)   

    g = Global_State()
    periodo=Periodos_a_analizar()

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    #parametros de al simulacion
    dict_avances ={'1m' : timedelta(minutes=1),
                   '3m' : timedelta(minutes=3),
                   '5m' : timedelta(minutes=5),
                   '15m': timedelta(minutes=15),
                   '1h' : timedelta(hours=1),
                   '2h' : timedelta(hours=2),
                   '4h' : timedelta(hours=4),
                   '1d' :  timedelta(days=1)}
    
    
    
    escala_simulacion='5m'
    tiempo_avance = dict_avances[escala_simulacion]
    trades=[]
    max_trades=0
    escalas=[escala_simulacion]
    escalas_mercados=[escala_simulacion]
    
    #descripcion_periodo,fecha_fin,fin_test = periodo.bajada_12_dias_Junio_05_17_2022()
    #descripcion_periodo,fecha_fin,fin_test = periodo.rango_bajada_rango_junio_22()
    descripcion_periodo,fecha_fin,fin_test = periodo.rango_subida_julio22()
    #descripcion_periodo,fecha_fin,fin_test = periodo.bajada_micro_18_junio_2022()
    #descripcion_periodo,fecha_fin,fin_test = periodo.bueno_30k_66k()

    lista_pares=['DOTUSDT']

    for par in lista_pares:

        pares=[par]
        m=Mercado_Back_Testing(log,g,db)
        estrategia = Estrategia(par,log,g,m,escala_simulacion)
        

   
    comprado=False
    esperando_compra=False
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
        print( f'                                                        {txtf}-------> ganancia= {round(gananciap,2)} entradas {entradas} trades {len(trades)} {trades} '  )
        
        if not comprado and trades:          # veo si puedo volver de un trade anterior 
            px_vta = estrategia.precio()
            px_guardado = trades[-1]
            gan = g.calculo_ganancia_porcentual(px_guardado,px_vta)
            if gan >0 :
                comprado = True
                vendido = False
                recomprado = False
                stoploss = 0
                log.log (f'-evento- recupero  gan {gan} entradas {entradas}')
                comp_px = px_guardado
                trades.pop()

        if not comprado:
            if trades:
                ultima_compra=trades[-1]
            else:
                ultima_compra=None
                
            # si estoy comprando veo si compré
            if esperando_compra:
                if comp_px <= estrategia.precio(): #doy por comprada la orden
                    esperando_compra = False
                    comprado =True
                    recomprado = False
                    stoploss = 0
                    comprado = True
                    log.log (f'-evento- gogogo-->   entradas {entradas} comp_px {comp_px}    ',txtf,estrategia.escala_de_analisis,estrategia.par)
                    log.log (f'comp_px {comp_px}, stop_loss {stoploss}')
            else: # si no estoy comprando veo si es momento de comprar
                if estrategia.decision_de_compra():
                    esperando_compra = True
                    comp_px = estrategia.precio_de_compra()    
                    log.log('decision_de_compra')
                else:
                    esperando_compra = False
                    comp_px = 0

        
        else: # estoy comprado
            px_vta = estrategia.precio()
            vendido = False
            recomprado = False
            gan = g.calculo_ganancia_porcentual(comp_px,px_vta)
            log.log (f'{txtf} -comprado-> {gan}%  sl {stoploss} ')    
            
            if gan <0 and  estrategia.decision_recompra(comp_px):
                log.log (f'-evento- recompra gan {gan} entradas {entradas} comp_px {comp_px} ')
                recomprado = True
                comprado = False
                trades.append(comp_px)
                max_trades=max(max_trades,len(trades))

            #establecimiento de stoploss
            if stoploss == 0:
                sl = estrategia.stoploss(comp_px) 
                if sl < px_vta and  g.calculo_ganancia_porcentual(comp_px,sl) >=0:
                    stoploss = sl
                    log.log (f'-evento- stoploss_iniciado gan {gan} stoploss {stoploss}')   
            #control de stoploss        
            elif stoploss>0 and px_vta <= stoploss:
                gan =  g.calculo_ganancia_porcentual(comp_px,stoploss)
                vendido = True
                log.log (f'-evento- stoploss tocado gan {gan} entradas {entradas}')
                    
            #venta        
            if not recomprado and not vendido and  estrategia.decision_venta(comp_px):
                vendido = True

            # subir stoploss
            if not recomprado and not vendido and stoploss>0:
                sl = estrategia.stoploss_subir(stoploss)
                if  stoploss >0 and stoploss < sl < px_vta:
                    gan =  g.calculo_ganancia_porcentual(comp_px,sl)
                    log.log (f'-evento- stoploss_subido {stoploss} a {sl} gan {gan}  ')
                    stoploss = sl

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

        
        m.avanzar_tiempo(tiempo_avance)
        
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

    txt_log_paremtros = f'{descripcion_periodo}: escala={estrategia.escala_rapida}  fechas {fecha_fin}-{fin_test}'
    txt_log_datos     = f'{par} ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas} trades {len(trades)} max_trades {max_trades} '  
    txt_log_fin = txt_log_datos + ' ' + txt_log_paremtros + ' ' + estrategia.file
    log_resultados.log (txt_log_fin) 
    db.backtesting_agregar_resultado(par,txt_log_fin,ganadas,perdidas,gananciap,len(trades))
    os.system('play ~/audios/sms-alert-1-daniel_simon.wav 2> /dev/null')

 