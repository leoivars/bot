from logger import Logger
from time import time
from variables_globales import VariablesEstado
from acceso_db import Acceso_DB
import time

def habilitar_deshabilitar_pares(g:VariablesEstado,db:Acceso_DB):
    ''' Controla la cantidad de pares que tienen trades en este momento y lo compara con 
        g.maxima_cantidad_de_pares_con_trades que establece la cantidad máxima de pares con trades. 
        Si la cantidad es menor, habilita todos pares que sean habilitable (habilitable=1 en la tabla pares).
        El objetivo es mantener todos los paras habilitados hasta lograr un máximo de pares con trades. Una vez que se logra,
        solo quedarán habilitados los pares con trades.
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






