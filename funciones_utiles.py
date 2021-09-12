from datetime import timedelta,datetime
import os
from psutil import Process
import psutil


def calcular_fecha_futura(minutos_al_futuro):
        ahora = datetime.now()
        fecha_futura = ahora + timedelta(minutes = minutos_al_futuro)
        return  fecha_futura  

def memoria_consumida():
    pid = os.getpid()
    py = psutil.Process(pid)
    memoryUse = py.memory_info()[0]/2.**30  # memory use in GB...I think
    return round(memoryUse,3)
 
def cpu_utilizada():
    cpu=psutil.cpu_percent()     
    return round(cpu,2)

def calc_tiempo(time_ini,time_fin):   
    try:
        tiempo  = time_fin.replace(microsecond=0) - time_ini
        stiempo = str(tiempo.days)+'d/'+str(divmod(tiempo.seconds,3600)[0])+'h'
    except:
        stiempo='--' 
    return  stiempo     

def calc_tiempo_segundos(time_ini,time_fin):   
    try:
        tiempo:timedelta  = time_fin.replace(microsecond=0) - time_ini
        ret = tiempo.total_seconds()
    except:
        ret=0 
    
    

    return  ret     

def str_fecha_hora_a_timestamp(str_fecha_hora):
    date_time_obj = datetime.strptime(str_fecha_hora, '%Y-%m-%d %H:%M:%S')
    return date_time_obj.timestamp()

def strtime_a_obj_fecha(strtime):
    fecha=datetime.fromisoformat(strtime)
    return fecha

def strtime_a_fecha(strtime):
    fecha=datetime.fromtimestamp(int(strtime)/1000)
    return fecha.strftime('%Y-%m-%d %H:%M:%S')

def timestampk_to_strtime(timestampk):
    fecha=datetime.fromtimestamp(timestampk/1000)
    return fecha.strftime('%Y-%m-%d %H:%M:%S %z')


def str_fecha_hora_mysql():
    fecha = datetime.now()
    return fecha.strftime('%Y-%m-%d %H:%M:%S')

def strtime_a_time(strtime):
    fecha=datetime.fromtimestamp(int(strtime)/1000)
    return fecha

def str_fecha():
    hoy = datetime.today()
    return "{}/{}/{}".format(  hoy.day, hoy.month, hoy.year )    

def format_valor_truncando(valor,digitos_decimales):
    if digitos_decimales>0:
        svalor='{0:.9f}'.format(valor)
        punto=svalor.find('.')
        dec=len(svalor[ punto+1:])
        if dec>digitos_decimales: dec=digitos_decimales
        return svalor[0:punto+1+dec]+"0"*(digitos_decimales-dec)
    else:
        return str(int(valor))


def mes_anio_actuales():
    hoy = datetime.today()
    return hoy.month, hoy.year    

def variacion(a,b):
    '''retorna un número positivo que indica la variación entre los dos numeros en %
       siempre el nro mas pequeño se usa como x, como una variacion hacia arriba'''
    if a < b:
        x=a
        y=b
    else:
        x=b
        y=a        

    if y==0:
        y = 0.00000000001
    return round(abs( 1-x/y   ) * 100 ,2)

def variacion_absoluta(x,y):
    '''retorna un nro que expresa el % de variación entre x e y
    si x < y retorna numeros positivos indicando que el aumento de x hacia y
    si x = y retorna 0
    si x > y retorna numeros negativos indicando una disminucion de x hacia y
    '''
    if y==0:
        y = 0.00000000001
    return round( ( 1-x/y   ) * 100 ,2)



def compara(a,b):
    '''
    retorna en porcentaje como es b respecto de a
    si a es > b = -100...0 
    si a < b = 0.01... 
    
    '''
    return ((b-a) /a) * 100

def signo(numero):
    if numero >0 :
        return 1
    else:
        return -1        

def linea(*args):
        lin = ' '.join([str(a) for a in args])       
        return lin        

if __name__ == '__main__':
    fecha = str_fecha_hora_a_timestamp('2021-06-13 01:00:00') 
    print (  fecha*1000)
 