from mercado_actualizador_socket import Mercado_Actualizador_Socket
import websocket
from velaset import VelaSet
from logger import Logger
import time
from pws import Pws
from binance.client import Client #para el cliente
from variables_globales import VariablesEstado
from mercado import Mercado

pws=Pws()
client = Client(pws.api_key, pws.api_secret)
log=Logger('Test_mercado.log')


globales = VariablesEstado()

par = 'BTCUSDT'
escala = '1m'

#escala  ={'1m':60 ,'5m': 300 ,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,'1w':604800,'1M':2419200}
#escala  ={'1m':60 ,'5m': 300 ,'15m':900}
escala  ={'1m':60,'5m': 300,'15m':900}
#escala  ={'1m':60,'5m': 300,'4h':None}
#escala  ={'4h':60}
#pares=['APPCBTC','NAVBTC','POWRBTC','BATBTC','BQXBTC','GVTBTC','RCNBTC','BTCUSDT']
pares=['BNBUSDT','BTCUSDT']

def control_inconsistencias(m):
    for p in m.par_escala_ws_v:
        for e in m.par_escala_ws_v[p]:
            i = m.par_escala_ws_v[p][e][1].inconsistencias()
            if i != -1:
                print (p,e,i)

print('inicio....')
m = Mercado(log,globales,client)

for e in escala:
    for p in pares:
        print(p,e)
        m.get_velaset(p,e)

i = 90



print('##############',m.par_escala_ws_v)

while  i >=0:
    control_inconsistencias(m)
    time.sleep(1)
    print( 'tiempo:',i * 1)
    i -=1
    for p in m.par_escala_ws_v:
        for e in m.par_escala_ws_v[p]:
            #vs:VelaSet = m.par_escala_ws_v[p][e][1]
            #ws:Mercado_Actualizador_Socket = m.par_escala_ws_v[p][e][0]
            #print(f' ultima_recepcion {time.time() - ws.time_ultima_recepcion}')
            #print(f' time_conexion    {time.time() - ws.time_conexion}')
            #print(f' suscripciones    { ws.subscripciones}')
            print(  p,e )
    if i == 70:
        m.desuscribir_todas_las_escalas('BNBUSDT')        

    for ws in m.sockets:    
        print(ws,m.get_suscripciones(ws))        
    
    #print( m.par_escala_ws_v)


for p in m.par_escala_ws_v:
    for e in m.par_escala_ws_v[p]:
        print(p,e)
        print(m.par_escala_ws_v[p][e][1].df)


m.detener_sockets()











