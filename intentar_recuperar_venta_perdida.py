#from gestor_de_posicion import Gestor_de_Posicion
from ordenes_binance import OrdenesExchange
from acceso_db import Acceso_DB
from funciones_utiles import strtime_a_time,strtime_a_fecha
import datetime
from logger import Logger 

def intentar_recuperar_venta_perdida(moneda,moneda_contra,oe:OrdenesExchange,db:Acceso_DB,log:Logger ):
    #obtener datos de ultima compra registrado
    #idtrade,cantidad,precio,orderid,fecha
    ret = False
    try:
        uc = db.get_ultimo_trade_abierto(moneda,moneda_contra) #una orden de compra
        if uc['idtrade'] != -1: # hay una orden con ejecutado=0
            #consulto el estado de la orden

            orden = encontrar_orden_venta(moneda+moneda_contra,uc['cantidad'],uc['fecha'],oe,db)
            #print('Orden encontrada',orden)
            fo =  strtime_a_time(orden['time'])
            duracion = (fo - uc['fecha']).seconds
            if 0 < duracion < 3600 * 4: #la orden es reciente
                ejecutado=float(orden['executedQty'])
                precio =float(orden['price']) 
                db.trade_sumar_ejecutado(uc['idtrade'],ejecutado,precio,strtime_a_fecha(orden['time']),orden['orderId'])
                ret = True
    except Exception as e:
        log.log('Error al intentar recuperar venta perdida',str(e))

    return ret    



        


def encontrar_orden_venta(par,cantidad,fecha,oe:OrdenesExchange,db:Acceso_DB):
    print( 'encontrar_orden',par,cantidad,fecha)
    ordenes = oe.consultar_ordenes(par)
    ret = None
    for o in reversed(ordenes):
        #print(float(o['executedQty']),  cantidad)
        if float(o['executedQty']) == cantidad:
            #print(float(o['executedQty']),  cantidad)
            if o['side']=='SELL' and o['status']=='FILLED':
                orden_en_db = db.get_trade_venta_orderid(o['orderId'])
                #print(orden_en_db)
                if orden_en_db['idtrade'] == -1: 
                    #he encontrado una orden de compra con el id buscado por la misma cantidad que no está en la base
                    #esto es lo que buscamo!
                    ret = o
                    break
    return ret    



if __name__=='__main__':
    from datetime import datetime
    from binance.client import Client #para el cliente
    from logger import *
    from ordenes_binance import OrdenesExchange
    from pws import Pws
    from variables_globales import VariablesEstado
    from acceso_db import Acceso_DB
    from acceso_db_conexion import Conexion_DB
    
    pws=Pws()
    log=Logger('test_ordenes_binance.log') 
    conn=Conexion_DB(log)

    client = Client(pws.api_key, pws.api_secret,{ "timeout": 20})
    p = Gestor_de_Posicion(log,client,conn)
    e = VariablesEstado(p)

    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn.pool)
    
    moneda='EOS'
    moneda_contra='USDT'
    cantidad=2.18

    par=moneda+moneda_contra

    oe=OrdenesExchange(client,par,log,e)

    intentar_recuperar_venta_perdida(moneda,moneda_contra,oe,db,log)

    # for o in ordenes:
    #     print (o)
