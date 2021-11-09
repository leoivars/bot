from logger import Logger
import os
def reporte_resumen_errores():
    log = Logger('resumen_reporte_errores.log')
    log.log('Resumen de Errores')
    dirlogs = log.dirlogs
    lista_logs = os.listdir(dirlogs)
    lista_logs=limpiar_lista(lista_logs,log.nombrearchivolog)
    errores={}
    for flog in lista_logs:
        resumir_errores(dirlogs+flog,errores)

    err_ordenados =  sorted(errores.items(), key=lambda x: x[1], reverse=True) 
    ret=''
    for l in err_ordenados:
        log.log(l[0],l[1]) 
        ret +=f'{l[1]}: {l[0]}\n'

    return ret   


def resumir_errores(flog,errores):
    '''lee el archivo log buscando Error,error.. y los agrega al diccionario de errores'''
    with open(flog) as archivo_log:
        for linea in archivo_log:
            for str in ['Error','error']:
                if str in linea:
                    agregar_error(linea,errores)
                    break


def agregar_error(linea,errores):
    lin = linea[10:].replace('\n','') #saco la fecha y los saltos de linea que existan
    try:
        errores[lin] += 1
    except:
        errores[lin] = 1

def limpiar_lista(lista_logs,mi_log):
    '''elimina de la lista todos los elementos que no nos interesan para rastrear errores'''
    nueva_lista=[]
    for log in lista_logs:
        if log != mi_log and log.endswith('.log'):
            nueva_lista.append(log)
    return nueva_lista        
         


