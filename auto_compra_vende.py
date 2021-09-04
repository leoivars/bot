# # -*- coding: UTF-8 -*-
from mercado import Mercado
import sys
import os
from velaset import VelaSet
from par import Par
from datetime import datetime, timedelta
import time
from binance.client import Client #para el cliente
import _thread
#import threading
#import json
from pws import Pws
from indicadores2 import Indicadores
from logger import *
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from ordenes_binance import OrdenesExchange
from actualizador_info_par import ActualizadorInfoPar
from par_propiedades import Par_Propiedades
from pool_indicadores import Pool_Indicadores
#from Monitor_precios_ws import MonitorPreciosWs
from controlador_de_tiempo import Controlador_De_Tiempo
from correo import Correo
from reporte_estado import ReporteEstado
from variables_globales import  VariablesEstado

from funciones_utiles import memoria_consumida,cpu_utilizada,calc_tiempo

from actualizar_info_pares_deshabilitados import actualizar_info_pares_deshabilitados,actualizar_ranking_por_volumen_global
from reconfigurar_pares_top import reconfigurar_pares_top

from gestor_de_posicion import Gestor_de_Posicion

from sensor_de_rendimieno import sensar_rendimiento_periodicamente

#import tracemalloc
import gc
import types
#import mem_top
#import traceback

#tracemalloc.start()

# import logging 
# logging.basicConfig(filename='./logs/auto_compra_vende.log',level=logging.DEBUG)


pws=Pws()
log=Logger('auto_compra_vende.log') 

 
c=True
while c:
    try:
        #client = Client(pws.api_key, pws.api_secret,{ "timeout": 15})
        client = Client(pws.api_key, pws.api_secret,{ "timeout": 30})
        c=False
    except Exception as e:
        print('no se puede crear cliente')
        print( str(e) )
        print (time.time())
        time.sleep(30)


#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
hpdb = Acceso_DB(log,conn.pool)  #hpdb hilo principal db

gestor_de_posicion = Gestor_de_Posicion(log,client,conn)
e = VariablesEstado(gestor_de_posicion)

logm=Logger('merado.log') 
logm.set_log_level(e.log_level)
mercado = Mercado(logm,e,client)


log.set_log_level(e.log_level)


# def demora_cola():
#     cola = IndPool.estado_cola()
#     demora = IndPool.demora_cola()
#     demora_de_cola = int(cola * demora)
#     return demora_de_cola

#retorna la variacion entre compra y ventan %
def var_compra_venta(px_compra,px_venta):
    return ( px_venta/px_compra -1   ) * 100   
    

def precio(par,escala):
        try:
            vs: VelaSet = mercado.par_escala_ws_v[par][escala][1]
            px = vs.ultima_vela().close
        except:
            px = -1
        return px 

def actualizar_info_pares_deshabilitados_periodicamente(e:VariablesEstado,IndPool:Pool_Indicadores,conn,client):
    time.sleep(300)# espero 5 minutitos antes de empezar a hacer algo 
    db = Acceso_DB(log,conn.pool)
    while e.trabajando:
        if e.se_puede_operar: 
            tiempo = actualizar_info_pares_deshabilitados(e,IndPool,conn,client)

            actualizar_ranking_por_volumen_global(e,IndPool,conn,client)
            
            if IndPool.btc_apto_para_altcoins:
                temporalidades='1h 4h 1d'
            else:
                temporalidades='4h 1d'      

            reconfigurar_pares_top(30,temporalidades ,'USDT',db,e)
            reconfigurar_pares_top(15,temporalidades,'BTC',db,e)


        time.sleep(1800 + tiempo) 

def materializar_pares_desde_db(inico=False,db:Acceso_DB=None,e:VariablesEstado=None):

    log.log('materializar_pares_desde_db.ini')
    #poner_pares_control_en_falso, luego si está query pasa a verdadero
    for k in e.pares_control.keys():
        e.pares_control[k]=False

    pares_activos=db.get_cuenta_pares_activos()
    
    #if inico:
    #    dict_pares_activos=db.lista_de_pares_activos_con_trades()
    #else:    
    dict_pares_activos=db.lista_de_pares_activos()

    #log.log('materializando...')
    
    for r in dict_pares_activos:
        par=str(r['moneda'].upper()+r['moneda_contra'].upper())
        #pongo en verdadero su variable de control para que pueda vivir.
        e.pares_control[par]=True   
        # creo el objeto si no está
        if not par in e.pares: 
        
            log.log(par,'lanzado',par,'Balance=',r['balance'])
            
            nuevo_par=Par(client,r['moneda'].upper(),r['moneda_contra'].upper(),conn,e,mercado)
            nuevo_par.set_log_level(e.log_level)
            
            # e.pares[par][0] es el obj par
            # e.pares[par][1] es el obj proceso
        
            e.pares[par]= [ nuevo_par, None ] #[par,proceso]
            _thread.start_new_thread(e.pares[par][0].trabajar,())
            #e.pares[par][1] = threading.Thread( target=e.pares[par][0].trabajar,args=() )   
            #e.pares[par][1].start()
            
            if inico: #realizo una pequeña demora para no meter tanta presion en el inicio
                time.sleep(.05)
            else:
                time.sleep(.01) 
            #mostrar_informacion()
        
    e.cant_pares_activos = pares_activos
    
   
    # detener inactivos 
    for k in e.pares_control.keys():
        if not e.pares_control[k]:
            log.log('XXXXX--> Detener:',k)
            e.pares[k][0].detener()
        else:
            e.pares[k][0].set_log_level(e.log_level)    

    eliminar_pares_muertos()       

def eliminar_pares_muertos():
    eliminar=[]
    #  detecto los pares muertos
    for k in e.pares.keys():
        if not e.pares[k][0].estoy_vivo:
            eliminar.append(k)  
            
    # ahora los elimino
    for k in (eliminar):
        del e.pares_control[k]
        e.pares[k][0]= None
        del e.pares[k] 

    if len(eliminar) > 0:
        gc.collect() # ha eliminadoun par, que tiene indicadores que tienen velas... quiero esa memoria de vuelta porque soy probre

#************************************************************************************************************************************************

def linea(*args):
    lin = ' '.join([str(a) for a in args])       
    lin += '\n'
    return lin

def control_BTC_invertido(): #Recáculo de los btc que tiene nque estan en reserva según lo que tengo comprado contra BTC
    btc=BTC_invertido()
    
    log.log('BTC expuesto',btc) 
    
    btcexponer=0.01
    if btc!=0:
        if abs(e.BTC_invertido_actual-btc)/btc > 0.1: #si hay una diferencia mayor al 10%
           e.BTC_invertido_actual=btc
           btcexponer=0.01 - btc
           e.pares['BTCUSDT'][0].cantidad_de_reserva=btcexponer - btc   
           log.log('Cambio de BTC disponibe',btcexponer)
           e.pares['BTCUSDT'][0].forzar_sicronizar=True
    elif btc==0 and  e.BTC_invertido_actual!=0:
        e.BTC_invertido_actual=0
        e.pares['BTCUSDT'][0].cantidad_de_reserva=btcexponer 
        log.log('Cambio de BTC disponibe',btcexponer)
        e.pares['BTCUSDT'][0].forzar_sicronizar=True
         


def BTC_invertido(): #Recáculo de los btc que tiene nque estan en reserva según lo que tengo comprado contra BTC
    btc=0
    for k in e.pares_control.keys():
        if k.endswith('BTC') and (e.pares[k][0].estado==3 or e.pares[k][0].estado==4):
            btc+=e.pares[k][0].cant_moneda_compra * e.pares[k][0].precio
            log.log('BTC_invertido()',k,e.pares[k][0].cant_moneda_compra,e.pares[k][0].precio,e.pares[k][0].cant_moneda_compra * e.pares[k][0].precio,btc)
    return btc        


def controlar_estado0():
     # detener inactivos
    for k in e.pares_control.keys():
        if e.pares[k][0].estado==0:
            log.log('######---OJO---######',k,'E.0')

        
def log_pares_estado(estado,maximo_a_mostrar=999):
    lin=''
    tot=0
    maxlin=0
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            if maxlin < maximo_a_mostrar:
                lin+=k.ljust(9,' ') + ' ' +p.mostrar_microestado()
                maxlin += 1
            tot += 1

    lin= 'En Estado ' + str(estado) + ' total=' + str(tot) + '\n' + lin        
    return lin        
    #log.log(lin)

def log_cuenta_pares_estado(estado):
    lin='En Estado '+ str(estado) +'= '
    cuenta=0
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            cuenta+=1
    return lin        
    #log.log(lin)

def cuenta_pares_estado2():
    '''cuenta los pares en estado 2 para cada moneda contra
       en la que se opera.
       estos valores son luego utilizado en par 
       para no supera la cantidad de pares simultaneos
       comprando
    '''
    cp = {'BUSD':0,'USDT':0,'BTC':0}

    for k in e.pares_control.keys():
        p = e.pares[k][0]
        if p.estado == 2:
            if p.moneda_contra == "USDT":
                cp["USDT"] += 1
            elif p.moneda_contra == "BTC":
                cp["BTC"] += 1

    e.pares_en_compras = cp            
    

def log_pares_estado_ordenado_por_ganancia(estado,cant=15):
    lin='En Estado '+ str(estado) +'\n'
    #obengo pares en estado 3 y sus ganancias
    pares_en_estado={}    
    
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            pares_en_estado[k]=p.ganancias()
    #recorro la lista obtenida en ordenada por su valor (ganancia)
    c = 0
    for k in sorted(pares_en_estado, key=pares_en_estado.get, reverse=True):
        p=e.pares[k][0]
        #if pares_en_estado[k] > -2: #filtro para mostrar solos los positivos o los que estan por ser positivos
        lin+=k.ljust(9,' ') + ' ' +p.mostrar_microestado()
        c = c +1
        if c > cant: #solo motrar los primeros cant
            break
    
    return lin        
    #log.log(lin)

def log_pares_senial_compra():
    e.cant_pares_con_senial_compra=0
    e.pares_con_senial_compra=[]
    #lin='Con Señal de Compra \n'
    try:    
        for k in e.pares_control.keys():
            p=e.pares[k]
            if p.senial_compra:
                #lin+=linea(k.ljust(9,' ') , p.mostrar_microestado() )
                e.cant_pares_con_senial_compra+=1
                e.pares_con_senial_compra.append(k)
        #log.log(lin)
        
        #27/08/19probando si esto pono lento a todo!#procesar_necesidades_de_liquidez()    
    except Exception as ex:
        log.log( "Error en log_pares_senial_compra:",ex )
        

def log_pares_estado7():
    estado=7
    lin='En Estado 7\n'
    #obengo pares en estado 7 y sus filtros superados
    pares_en_estado={}    
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            if p.e7_filtros_superados > 10:
                pares_en_estado[k]=p.e7_filtros_superados
    #recorro la lista obtenida en ordenada por su valor (ganancia)
    col=0
    for k in sorted(pares_en_estado, key=pares_en_estado.get, reverse=True):
        
        if pares_en_estado[k]>0:
            lin+=k.ljust(9,' ') + ' ' + str (pares_en_estado[k] )
            col+=1
        
            if col==4:
                lin+='\n'
                col=0
            else:
                lin+='|'    


    return lin        
    #log.log(lin)    

        

def log_trades_activo_contra(moneda_contra):
    lin=''
    for r in hpdb.get_monedas_con_trades_activos(moneda_contra):
        lin+=' '+r['moneda'].lower()
    log.log('trades_activos_'+moneda_contra.lower(),lin)    
  
def log_trades_activos():
    log_trades_activo_contra('BTC')
    log_trades_activo_contra('USDT')
    log_trades_activo_contra('PAX')


def mostrar_informacion():
    
    #log_pares_senial_compra() #este debe ir primero porque establece las necesidadas de liquidez
    #log_cuenta_pares_estado(2)


    log.log(  log_pares_estado_ordenado_por_ganancia(3)  )
    log.log(  log_pares_estado(2,100)  )
    log.log(  log_pares_estado(9,20)  )
    #log.log(  log_pares_estado7() )

def reporte_peores(horas_hacia_atras):
    peores = hpdb.ind_historico_peores(horas_hacia_atras)
    lin=''
    if peores != None:
        for p in peores:
            lin += p[0]+p[1]+ ' ' +str(p[2]) + ' ' + str(p[3])+'\n'

    return 'Peores Monedas: ' +str(horas_hacia_atras)+' horas\n' + lin    
    
def reporte_de_inactivos():
    
    reporte=''

    lista_pares = e.pares.keys()
    for k in lista_pares:
        p=e.pares[k][0]
        tiempo_inactivo = p.log.tiempo_desde_ultima_actualizacion()

        if tiempo_inactivo > p.tiempo_reposo * 2 + 1200:
            reporte += linea( k,'inactivo------>',int(tiempo_inactivo),'s.')
            reporte += p.log.tail()
            p.deshabiliar_brutalmente(20)


    return reporte        


def reporte_de_muerte():
    reporte = linea('Acaba de morir el monitor de Precios! Reiniciamos el Bot')
    reporte = log.tail()
    titulo='REINICIO '+ datetime.datetime.now().strftime('%m%d %H:%M')
    texto=titulo+'\n' + reporte
    correo=Correo(log)
    correo.enviar_correo(titulo,texto)

def reporte_correo():
    
    reporte  = reporte_de_ciclo() +'\n'
    
    reporte += reporte_de_inactivos() +'\n' #reporto pares inactivos por mas de 30 minutos (1800 s)

    reporte += log_pares_estado_ordenado_por_ganancia(3,199)
    reporte += log_pares_estado(2)+'\n'
    #reporte += log_pares_estado(8)
    #reporte += log_pares_estado(7) +'\n'

    #reporte += reporte_peores(2)+'\n'
    #reporte += reporte_peores(24)+'\n'
 
    
    #reporte del mes actual
    rep = ReporteEstado(log,conn,e)
    hoy = datetime.datetime.today()
    mes = hoy.month
    anio = hoy.year
    
    #reporte de meses anteriores
    for _ in range(0,24):
        reporte += ' *********** Mes ' + str(mes) + ' Año ' + str(anio)  +'************\n' 
        reporte += rep.reporte(mes,anio)  +'\n'
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1

    titulo='Reporte estado '+ datetime.datetime.now().strftime('%m%d %H:%M')
    texto=titulo+'\n' + reporte
    correo=Correo(log)
    correo.enviar_correo(titulo,texto)

def reporte_de_ciclo():
    reporte= linea ('T.Func:', calc_tiempo(inicio_funcionamiento,datetime.datetime.now()),' Reinicios:',cuenta_de_reinicios)
    
    #txt_btc_volatil='_' if IndPool.btc_apto_para_altcoins else '!'
    #estado_general = mo_pre.estado_general()
  
    #reporte+=linea('invertido en btc ...........:', round(e.invertido_btc*100,2) ,'max',round(e.max_inversion_btc * 100 ,2) )
    #reporte+=linea('invertido en usdt...........:', round(e.invertido_usdt *100,2), 'max', round(e.max_inversion_usdt * 100 ,2) ) 
    # reporte+=linea('btc_apto_para_altcoins......:',IndPool.btc_apto_para_altcoins)
    # reporte+=linea('btc_alcista.................:',IndPool.btc_alcista)
    # reporte+=linea('btc_macd_ok.................:',IndPool.btc_macd_ok)
    # reporte+=linea('btc_en_rango................:',IndPool.btc_en_rango)
    # reporte+=linea('btc_rsi_ok..................:',IndPool.btc_rsi_ok)
    # reporte+=linea('btc_con_velas_verdes........:',IndPool.btc_con_velas_verdes)
    # reporte+=linea('btc_con_pendiente_negativa..:',IndPool.btc_con_pendiente_negativa)
    

    #reporte+=linea('Est Gral.: Bajan',estado_general['bajando'],' noBaj',estado_general['nobajando'])
    reporte+=linea('..M:',memoria_consumida(),'GB CPU=',cpu_utilizada(),'.e49s.')
    
    #cola = IndPool.estado_cola()
    #demora = IndPool.demora_cola()
    #demora_de_cola = int(cola * demora)
    #reporte+=linea('Cola =',cola,'demora=',demora,'espera=', demora_de_cola)
    reporte+=linea('::PARES activos',len(e.pares),'max',e.max_pares_activos,'BTCUSDT',round(precio('BTCUSDT','1m'),2) )
    #if demora_de_cola > 60:
    #    IndPool.loggeame_la_cola() #hay que mirar el log del pool de indicadores para ver este logueo.
    
    return reporte





def esperar_correcto_funcionamiento(e:VariablesEstado):
    # esperamos el corremto funcionamiento del systema
    
    while True:
        
        try:
            if client.get_system_status() ['status']==0:
                print('Sistema OK. Comenzamos!')
                e.se_puede_operar = True
                break
            else:
                print('Sistema en mantenimiento...')
                t=300
                e.se_puede_operar = False
        except:
            print('no responde client.get_system_status()...')
            t=10

        time.sleep(t)
    e.se_puede_operar = True
    log.log( 'todo ok, se puede operar' )


def matar(par):
    #e.parer[par][0].detener()
    #e.pares[par][1].join()
    e.pares[par][0].detener()
    e.pares[par][0] = None
    #del e.pares[par]
    #del e.pares_control[par]
    gc.collect()


def esperar_a_que_todos_mueran():
     # detener inactivos
    alguno_vivo = True 
    c=300 
    while alguno_vivo and c>0:
        #log.log('Esperando para salir',c)
        alguno_vivo = False
        for k in e.pares_control.keys():
            if e.pares[k][0].estoy_vivo:
                log.log(k,'Vivo')
                alguno_vivo = True
                break
        time.sleep(1)
        c-=1
    
    #declaro muerto lo que exista
    lista_pares=e.pares_control.keys()
    for k in lista_pares:
        e.pares[k][0].estoy_vivo = False

    eliminar_pares_muertos()    
    
    log.log('todos muertos!')        



# def controlar_correcto_funcionamiento():
#     controlar_correcto_funcionamiento_monitor_de_precios()
#     controlar_correcto_funcionamiento_poll_indicadores()

# def controlar_correcto_funcionamiento_monitor_de_precios():
#     #control de correcto funcionamiento del monitor de precios
#     #si no ha recibido datos en mas de 90 segundos, lo reinicio.
#     if mo_pre.ultima_actualizacion() > 90:
#         log.log('Monitor de precios no está funcionado bien, reiniciando...')
#         #mo_pre.detener()
#         reporte_de_muerte()
#         e.trabajando = False # esta hace que se muera todo

#def controlar_correcto_funcionamiento_poll_indicadores():
#    #control de correcto funcionamiento del monitor de precios
#    #si no ha recibido datos en mas de 90 segundos, lo reinicio.
#    if IndPool.estado_cola() > 600:
#        log.log('El pool de indicadores creció demasiado, reiniciamos')
#        reporte_de_muerte()
#        e.trabajando = False # esta hace que se muera todo    


def actualizar_posicion_periodicamente(e,gestor_de_posicion):
    e.actualizar_posicion()
    periodo = 300
    time.sleep( periodo )  # unos segundos para que levante todo
    
    while e.trabajando:
        if e.se_puede_operar: 
            try:
                e.actualizar_posicion()
            except Exception as ex:
                print(str(ex))

        time.sleep( periodo )  # unos segundos para que levante todo



def deshabiliar_pares_en_compra_temporalmente(e,log):
    pares_en_compra=[]
    monedas_contra=[]
    #  detecto determino los pares en compra
    for k in e.pares.keys():
        p=e.pares[k][0] # lo pongo en p para referenciarlo amigablemente
        if p.estoy_vivo and p.estado==2:
            try:
                coef = float(1-p.precio_compra/p.precio)
                pares_en_compra.append([p,coef])
                if p.moneda_contra not in monedas_contra:
                    monedas_contra.append(p.moneda_contra)
            except Exception as e:
                log.log(str(e))

    pares_en_compra.sort(key=lambda x:x[1],reverse=True)   #ordeno por el segundo elemento de la tupla  
    
    #log para ver como queda esto
    for p in (pares_en_compra):
        log.log (p[0].moneda, p[0].moneda_contra,p[1])
   
    #recorro en forma inversa y detengo 1 par de cada moneda contra
    # lo que llevan mucho tiempo o cuyo precio de compra está muy alejado del precio y por lo tanto será muy dificil comprar
    log.log('monedas_contra',monedas_contra)
    for mc in monedas_contra:
        log.log('moneda_contra',mc)
        if e.falta_de_moneda[mc]:
            e.falta_de_moneda[mc]=False #declaro satisfecha la demanda
            for x in pares_en_compra:
                p=x[0]
                if p.moneda_contra == mc:
                    coef=x[1]
                    ahora = time.time()
                    tiempo_en_estado = int(ahora - p.tiempo_inicio_estado)
                    #log.log(p.moneda,p.moneda_contra,'t.estado=',tiempo_en_estado,'coef=',coef)
                    if tiempo_en_estado > 3600 or coef>0.15:
                        p.detener_estado_2(horas=e.horas_deshabilitar_par)
                        log.log('deteniendo...',p.moneda,p.moneda_contra,x[1])
                        break
                
def deshabiliar_pares_en_compra_temporalmente_periodicamente(e:VariablesEstado):
    periodo = 600
    time.sleep( periodo )  # unos segundos para que levante todo
    loglocal=Logger('deshabiliar_pares_en_compra_temporalmente_periodicamente.log')

    while e.trabajando:
        if e.se_puede_operar: 
            #loglocal.log('inicio: deshabiliar_pares_en_compra_temporalmente_periodicamente')         
            try:
                deshabiliar_pares_en_compra_temporalmente(e,loglocal) 
            except Exception as ex:
                loglocal.log(str(ex))

            #loglocal.log('fin: deshabiliar_pares_en_compra_temporalmente_periodicamente')             

        time.sleep( periodo )  # unos segundos para que levante todo


try:
    #cuenta de reinicios pasado como parámetros
    cuenta_de_reinicios= int(sys.argv[1])
    #fecha para cacular cuanto tiempo lleva funcionando pasad como parametro
    inicio_funcionamiento = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S.%f')
except:    
    cuenta_de_reinicios=0
    inicio_funcionamiento = datetime.datetime.now()


# deshabilito todo para ir habilitando en la medida de lo positble
# hpdb.deshabilitar_todos_los_pares()

#habilito los pares que tengo
#hpdb.habilitar_pares_que_tengo()

esperar_correcto_funcionamiento(e)

#web soket de monitor de precios
#mo_pre=MonitorPreciosWs(log)
#mo_pre.empezar()

#pool de indicadores para pares lindos.
#logpool=Logger('pool_indicadores.log') 
#IndPool=Pool_Indicadores(logpool,mo_pre,e)

#actualización inicial del estado de btc
#IndPool.actualizar_parametros_btc()

#Actualizacion inicial del ranking, necesaria antes de empezar a materializar pares
#actualizar_ranking_por_volumen_global(e,IndPool,conn,client)

materializar_pares_desde_db(True,hpdb,e)

# sensor de rendimiento, hilo que aumenta o disminuye la cantidad de pares
#_thread.start_new_thread( sensar_rendimiento_periodicamente,(e,IndPool) ) 

# deshabilitador de pares que se pasarían la vida intentando comprar sin hacerlo para dar lugar a nuevas oportunidades
#_thread.start_new_thread(deshabiliar_pares_en_compra_temporalmente_periodicamente,(e,)) 

# actualizo la posicion global
#_thread.start_new_thread(actualizar_posicion_periodicamente,(e,gestor_de_posicion)) 

# hilo actualizador de estadísticas para los pares que no están habilitados
#_thread.start_new_thread(actualizar_info_pares_deshabilitados_periodicamente,(e,IndPool,conn,client))

# habilitador de pares que no estan en buena situacion
#_thread.start_new_thread(habilitar_pares_feos_periodicamente,()) 

# habilitador de pares muy activos

# habilitador de pares con trades positivos
#_thread.start_new_thread(habilitar_pares_con_trades_positivos_periodicamente,()) 

#_thread.start_new_thread(habilitar_pares_muy_activos_periodicamente,()) 


ti_mail = Controlador_De_Tiempo(14400)
#ti_mail = Controlador_De_Tiempo(600)
reporte_correo()

#bucle princpipal
while e.trabajando:
    try:
        #set_log_levels()
        #IndPool.actualizar_parametros_btc()

        mostrar_informacion()

        if ti_mail.tiempo_cumplido():
            reporte_correo()
            #ti_mail.intervalo += 60 #voy subiendo para darle cada vez menos bola

        materializar_pares_desde_db(False,hpdb,e)
        controlar_estado0()
        
        cuenta_pares_estado2()

        log.log( reporte_de_ciclo() )
       
    except Exception as exppal:
        log.log('Error', str(exppal))   

    time.sleep(49)
    esperar_correcto_funcionamiento(e)
    
    # si trabajando en config.json = 0, hace un shutdown
    log.log('cargar_configuraciones_json')
    e.cargar_configuraciones_json()
    log.log('controlar_correcto_funcionamiento')
    #controlar_correcto_funcionamiento()  


log.log("Cerrando todo...")
#mo_pre.detener()
esperar_a_que_todos_mueran()
log.log("todoslisto para salir...")

# mo_pre.morir()
# del mo_pre
# IndPool.morir() 
# del IndPool

# pragma pylint: disable=no-member


log.log('FIN - FIN - Me morí.')

os._exit(1)



## ----------FIN--------------##
    
