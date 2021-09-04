from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from logger import *
from datetime import *
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente

log=Logger('test_acceso_db.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)


#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
if conn.pool:

    db=Acceso_DB(log,conn.pool)

    id_par_escala = db.get_id_par_escala('btcusdt','1m') 
    ret = db.crear_actualizar_vela(id_par_escala,1,1,1,1,1,1,1)
    print(ret)
    ret = db.crear_actualizar_vela(id_par_escala,1,1,1,1,1,1,2)
    print(ret)



#fecha=datetime.now().replace(microsecond=0)  - timedelta( minutes= 40  )

#print (fecha)
#alcistas, bajistas=db.ind_historico_alcista_bajista(fecha,0.25)
#print (alcistas, bajistas)



#p=db.get_valores('COCOS','BTC')
#print (p)

#ultimo_hist=db.ind_historico_ultimo_registro(p['idpar'])
#print(ultimo_hist)
#db.ind_historico_insert(p['idpar'],1,0)


#print ('get_trade_menor_precio',db.get_trade_menor_precio('dock','btc')  )

# print ('get_ultimo_trade_cerrado',db.get_ultimo_trade_cerrado('KNC','BTC')   )
# ta=db.get_ultimo_trade_cerrado('KNC','BTC')
# ahora=datetime.now().replace(microsecond=0) 
# print ('ahora',ahora,'antes', ta['ejec_fecha'])
# print ('tiempo_transcurrido',ahora - ta['ejec_fecha'])


# print ('get_ultimo_trade_cerrado XX',db.get_ultimo_trade_cerrado('KDFNC','BTC')   )


# moneda='INS'
# moneda_contra='BTC'
# ind=Indicadores(moneda+moneda_contra,client,log)


# precio_ultimo_trade = db.get_trade_menor_precio(moneda,moneda_contra)['precio']
# precio=ind.precio('1h')



# print ('variacion ultimotrad,precio',variacion  (precio_ultimo_trade,precio)    ) 

