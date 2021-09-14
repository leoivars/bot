
from mercado import Mercado
from variables_globales import VariablesEstado
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from logger import Logger
from funciones_utiles import linea
from par import Par
from correo import Correo
from datetime import datetime #, timedelta
from fauto_compra_vende.funciones_logs import log_pares_estado_ordenado_por_ganancia,log_pares_estado
from reporte_estado import ReporteEstado
from datetime import datetime
from funciones_utiles import memoria_consumida,cpu_utilizada,calc_tiempo,linea

def reporte_de_inactivos(e):
    reporte=''
    lista_pares = e.pares.keys()
    for k in lista_pares:
        p: Par =e.pares[k][0]
        tiempo_inactivo = p.log.tiempo_desde_ultima_actualizacion()

        if tiempo_inactivo > p.tiempo_reposo * 2 + 1200:
            reporte += linea( k,'inactivo------>',int(tiempo_inactivo),'s.')
            reporte += p.log.tail()
            p.deshabiliar_brutalmente(20)

    return reporte   

def reporte_de_muerte(log):
    reporte = linea('Acaba de morir el monitor de Precios! Reiniciamos el Bot')
    reporte = log.tail()
    titulo='REINICIO '+ datetime.now().strftime('%m%d %H:%M')
    texto=titulo+'\n' + reporte
    correo=Correo(log)
    correo.enviar_correo(titulo,texto)

def reporte_correo(log:Logger,db:Acceso_DB,e:VariablesEstado,mercado:Mercado,inicio_funcionamiento,cuenta_de_reinicios):
    
    reporte  = reporte_de_ciclo(e,mercado,inicio_funcionamiento,cuenta_de_reinicios) +'\n'
    
    reporte += reporte_de_inactivos(e) +'\n' #reporto pares inactivos por mas de 30 minutos (1800 s)

    reporte += log_pares_estado_ordenado_por_ganancia(e,3,199)
    reporte += log_pares_estado(e,2)  +'\n'
    #reporte += log_pares_estado(8)
    #reporte += log_pares_estado(7) +'\n'

    #reporte += reporte_peores(2)+'\n'
    #reporte += reporte_peores(24)+'\n'
 
    
    #reporte del mes actual
    rep = ReporteEstado(log,db,e)
    hoy = datetime.today()
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

    titulo='Reporte estado '+ datetime.now().strftime('%m%d %H:%M')
    texto=titulo+'\n' + reporte
    correo=Correo(log)
    correo.enviar_correo(titulo,texto)

def reporte_de_ciclo(e:VariablesEstado,mercado:Mercado,inicio_funcionamiento,cuenta_de_reinicios):
    reporte= linea ('T.Func:', calc_tiempo(inicio_funcionamiento,datetime.now()),' Reinicios:',cuenta_de_reinicios,'\n')
    reporte+=linea('..M:',memoria_consumida(),'GB CPU=',cpu_utilizada(),'.e49s.','\n')
    #cola = IndPool.estado_cola()
    #demora = IndPool.demora_cola()
    #demora_de_cola = int(cola * demora)
    #reporte+=linea('Cola =',cola,'demora=',demora,'espera=', demora_de_cola)
    reporte+=linea('::PARES activos',len(e.pares),'max',e.max_pares_activos,'BTCUSDT',round(mercado.precio('BTCUSDT','1m'),2),'\n' )
    #if demora_de_cola > 60:
    #    IndPool.loggeame_la_cola() #hay que mirar el log del pool de indicadores para ver este logueo.
    return reporte

