# # -*- coding: UTF-8 -*-
from mercado import Mercado
import sys
import os
import gc
from datetime import datetime
import time
import _thread
from pws import Pws
from logger import Logger
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from controlador_de_tiempo import Controlador_De_Tiempo
from variables_globales import  VariablesEstado
from fauto_compra_vende.habilitar_pares import habilitar_deshabilitar_pares_periodicamente
from fauto_compra_vende.funciones_principales import crear_cliente, esperar_correcto_funcionamiento,controlar_estado0,esperar_a_que_todos_mueran
from fauto_compra_vende.materializar_pares import materializar_pares_desde_db
from fauto_compra_vende.reportes import reporte_correo,reporte_de_ciclo
from fauto_compra_vende.funciones_logs import mostrar_informacion

pws=Pws()
client = crear_cliente(pws)
e = VariablesEstado()                            #Objeto con información global del bot
log=Logger('auto_compra_vende.log')              #log para este modulo
log.set_log_level(e.log_level)

esperar_correcto_funcionamiento(client,e,log)    #antes de hacer algo mas controlo que el exchange esté funcionando

conn=Conexion_DB(log)                            #apertura del pull de conexiones
hpdb = Acceso_DB(log,conn.pool)                  #objeto de acceso a datos hpdb hilo principal db

logm=Logger('mercado.log')                        #log para para mercado 
logm.set_log_level(e.log_level)
mercado = Mercado(logm,e,client)                 #objeto encargado de la obtención de datos desde el exchange

try:
    cuenta_de_reinicios= int(sys.argv[1])        #cuenta de reinicios pasado como parámetros
    inicio_funcionamiento = datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S.%f')     #fecha para cacular cuanto tiempo lleva funcionando pasad como parametro
except:    
    cuenta_de_reinicios=0
    inicio_funcionamiento = datetime.now()   

_thread.start_new_thread( habilitar_deshabilitar_pares_periodicamente, (e,conn) )       # habilitador de pares

materializar_pares_desde_db(True,log,conn,e,mercado,client)     #materializacion inicial de pares

ti_mail = Controlador_De_Tiempo(7200)           #para enviar mails periódicamente
reporte_correo(log,hpdb,e,mercado,inicio_funcionamiento,cuenta_de_reinicios)                       #mail al inicio, situación de arranque    

while e.trabajando:                              #bucle princpipal 
    try:
        mostrar_informacion(e,log)

        if ti_mail.tiempo_cumplido():
            reporte_correo(log,hpdb,e,mercado,inicio_funcionamiento,cuenta_de_reinicios) 
            #ti_mail.intervalo += 60 #voy subiendo para darle cada vez menos bola

        materializar_pares_desde_db(False,log,conn,e,mercado,client)
        controlar_estado0(e,log)
        
        log.log( reporte_de_ciclo(e,mercado,inicio_funcionamiento,cuenta_de_reinicios) )

        time.sleep(49)
        esperar_correcto_funcionamiento(client,e,log)
    
        # si trabajando en config.json = 0, hace un shutdown
        log.log('cargar_configuraciones_json')
        e.cargar_configuraciones_json()

    except Exception as ex:
        log.log('Error', str(ex))   

    
log.log("Cerrando todo...")
esperar_a_que_todos_mueran(e,log)
log.log('FIN - FIN - Me morí.')

os._exit(1)

## ----------FIN--------------##
    
