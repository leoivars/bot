from logger import Logger
from time import time
from variables_globales import VariablesEstado
from acceso_db import Acceso_DB
import time

def habilitar_deshabilitar_pares(g:VariablesEstado,db:Acceso_DB):
    ''' si se pueden realizar mas entradas, se activan todos los pares
        retorna cantidad de pares habilitados
    '''
    if db.trades_cantidad_de_pares_con_trades() < g.maxima_cantidad_de_pares_con_trades:
        if len ( db.get_habilitables() ) > 0:
            db.habilitar_habilitables()
    else:
        db.deshabilitar_pares_sin_trades()


def habilitar_deshabilitar_pares_periodicamente(g:VariablesEstado,conn):
    log = Logger('habilitar_deshabilitar.log')
    db:Acceso_DB = Acceso_DB(log,conn.pool)
    while g.trabajando:
        habilitar_deshabilitar_pares(g,db)
        time.sleep(300)     






