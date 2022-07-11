
from acceso_db import *
from acceso_db_conexion import *
from pws import Pws
from logger import *
from binance.client import Client
from datetime import datetime
#from Monitor_precios_ws import MonitorPreciosWs
from pool_indicadores import Pool_Indicadores
from variables_globales import  Global_State
from actualizador_info_par import ActualizadorInfoPar
from ordenes_binance import OrdenesExchange


log=Logger('actualizar_estadisticas.log') 
e=Global_State()

#web soket de monitor de precios
mo_pre=MonitorPreciosWs(log)
mo_pre.empezar()

#pool de indicadores para pares lindos.
logpool=Logger('pool_indicadores.log') 
IndPool=Pool_Indicadores(logpool,mo_pre,e)

pws= Pws()

conn=Conexion_DB(log)
db=Acceso_DB(log,conn.pool)

client = Client(pws.api_key, pws.api_secret)



def actualizar_estadisticas(moneda,moneda_contra):
    log.log('actualizar_estadisticas',moneda,moneda_contra)
    par= moneda+moneda_contra
    ind= IndPool.indicador(par)
    escala='1d'
    oe = OrdenesExchange(client,par,log,e)
    actualizador = ActualizadorInfoPar(db, oe ,log)
    actualizador.actualizar_info(ind,escala,moneda,moneda_contra)

def main():
    prices = client.get_orderbook_tickers()
    monedas_contra=['BTC','USDT']
    for m in monedas_contra:
        lm=len(m)
        for p in (prices):
            s=p['symbol']
            if s.endswith(m):
                moneda=str(s[:len(s)-lm])
                d=db.get_valores(moneda,m)
                if d['idpar']!=-1:
                    actualizar_estadisticas(moneda,m)


main()