from variables_globales import Global_State
from logger import Logger
import time
from no_se_usa.acceso_db import Acceso_DB

from no_se_usa.acceso_db import Acceso_DB

from funciones_utiles import cpu_utilizada

from acceso_db_conexion import Conexion_DB

    

def reconfigurar_pares_top(top,temporalidades,moneda_contra,db:Acceso_DB,g:Global_State):

    loglocal=Logger('reconfigurar_pares_top.log')
    loglocal.set_log_level(g.log_level)

    #empezamos 
    loglocal.log ("----INICIO----")
    inicio=time.time()

    pares = db.get_pares_top(top,moneda_contra)

    print(pares)
    print(len(pares))

    db.temporalidades_a_1d(moneda_contra) 

    for p  in pares:
        try:
            moneda=p['moneda']
            moneda_contra=p['moneda_contra'] 
            print(moneda,moneda_contra)
            db.temporalidades(temporalidades,moneda,moneda_contra)

        except Exception as e:
            loglocal.log('Error',str(e))    

    loglocal.log ("----FIN----")
    return time.time() - inicio        # retorna el tiempo que se demoró
    
#TEST

if __name__ == "__main__":
    #base de datos
    log = Logger('test_reconfigurar_pares_top')
    conn=Conexion_DB(log)
    db=Acceso_DB(log,conn.pool)

    g = Global_State()

    #pool de indicadores para pares lindos.
    logpool=Logger('pool_indicadores.log') 


    reconfigurar_pares_top(10,'1d','USDT',db,g)


