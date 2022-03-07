from coinpaprika import client as Coinpaprika
from no_se_usa.acceso_db import *
from acceso_db_conexion import *
from logger import *

from pws import Pws
from binance.client import Client #para el cliente

pws=Pws()
log=Logger('paprika.log') 
client = Client(pws.api_key, pws.api_secret)
#apertura del pull de conexiones
conn=Conexion_DB(log)
db=Acceso_DB(log,conn.pool)


client = Coinpaprika.Client()

coins=client.coins()





criptos=db.ejecutar_sql_ret_cursor('select * from criptomonedas')

sqlu='update criptomonedas set idpaprika=%s, nombre_cripto=%s, rank=%s where idcripto=%s'

for cr in criptos:
    moneda=cr[0]
    p= None
    for c in coins:
        if c['symbol']==moneda:
            p=c
            break
    
    
    print (moneda, p)
    if p != None:
        db.ejecutar_sql(sqlu,(p['id'],p['name'],p['rank'],moneda))
    
    




#ebtc = client.events("btc-bitcoin")
#for e in ebtc:
#    print(e)


#print (client.candle("btc-bitcoin"))    