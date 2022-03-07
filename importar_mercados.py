
from no_se_usa.acceso_db import *
from acceso_db_conexion import *
from pws import Pws
from logger import *
from binance.client import Client
from datetime import datetime



def main():
    
    pws= Pws()
    log=Logger('mercados.log') 
    conn=Conexion_DB(log)
    db=Acceso_DB(log,conn.pool)
    client = Client(pws.api_key, pws.api_secret)


    prices = client.get_orderbook_tickers()

    #print (prices)
    
    monedas_contra=['BTC','USDT']
    for m in monedas_contra:
        lm=len(m)
        for p in (prices):
            s=p['symbol']
            if s.endswith(m):
                moneda=str(s[:len(s)-lm])
                d=db.get_valores(moneda,m)
                if d['idpar']==-1:
                    ahora='ingresado ' + datetime.now().strftime("%d-%b-%Y (%H:%M)")
                    print (moneda,m,ahora)
                    db.insertar_par(moneda,m,ahora)



main()