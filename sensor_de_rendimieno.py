from pool_indicadores import Pool_Indicadores
from variables_globales import  VariablesEstado
from funciones_utiles import cpu_utilizada,memoria_consumida
import time

def sensor_de_rendimiento(g:VariablesEstado,ind_pool:Pool_Indicadores):
    ''' si el bot está tranquilo sube la cantidad de pares a monitorear
        caso contrario puede bajar la cantidad de pares
        el minimo de pares activos sera g.max_pares_activos_config
    '''
    cola = ind_pool.estado_cola()
    cpu = cpu_utilizada()
    mem = memoria_consumida()
    if cola < 5 and cpu < 20 and mem < g.max_mem:
        aumentar_max_pares( 3 , g)
    elif cola < 20 and cpu < 40 and mem < g.max_mem:
        aumentar_max_pares( 1 , g)
    elif cola >80:
        disminuir_max_pares( 10 ,g ) 
    elif cola >60:
        disminuir_max_pares( 5 , g )
    elif cola >55 or cpu > 70:
        disminuir_max_pares( 1 , g )    
        
def disminuir_max_pares(cantidad, g:VariablesEstado): 
    if g.max_pares_activos >= g.max_pares_activos_config + cantidad:
        g.max_pares_activos = len(g.pares) - cantidad
    else: 
        g.max_pares_activos = g.max_pares_activos_config

def aumentar_max_pares(cantidad, g:VariablesEstado): 
    if len(g.pares) >=  g.max_pares_activos - cantidad: # estoy cerca del límite, aumento
        g.max_pares_activos += cantidad

def sensar_rendimiento_periodicamente(g:VariablesEstado,ind_pool:Pool_Indicadores):
    while g.trabajando:
        sensor_de_rendimiento(g,ind_pool)
        time.sleep(30)             

