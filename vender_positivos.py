# # -*- coding: UTF-8 -*-
from binance.client import Client
import time
import os
import sys

import pws
import traceback
from acceso_db import *
from logger import *

log=Logger('vender_positivos_mercados.log') 


client = Client(pws.api_key, pws.api_secret)

db=Acceso_DB(log)
cursor=db.conexion.cursor()

#monedas_contra=['BTC','USDT']
monedas_contra=['BTC']

def tomar_cantidad(parametro_asset):
    
    ret=0
    while True:
        try:
            balance = client.get_asset_balance(asset=parametro_asset)
            ret=float(balance['free'])+float(balance['locked'])
            break
        except Exception as e:
            print ('Error, esperando 60 segundos.')
            time.sleep(60)
    
   # print parametro_asset,balance,ret
    return ret
        



def cargarlista(tickers):
    pares={}
    for t in (tickers):
        if t['symbol'].endswith("BTC"): #or t['symbol'].endswith("USDT"):
            pares[ t['symbol']]= float( t['quoteVolume'] )
    return pares


def actualizar_datos():
    tickers = client.get_ticker()
    
    usql="UPDATE pares set precio= %s , porcentaje_cambio_precio = %s ,balance = %s,quoteVolume= %s "
    usql+="WHERE moneda= %s and moneda_contra= %s "

    for t in tickers:
        moneda_contra=''
        moneda=''
        precio= float(t['lastPrice'])
        quoteVolume= float(t['quoteVolume'])
        porcentaje_cambio_precio=  float(t['priceChangePercent'])      
        for m in monedas_contra:
            lm=len(m)
            s=t['symbol']
            if s.endswith(m):
                moneda=str(s[:len(s)-lm])
                moneda_contra=m
                balance=tomar_cantidad(moneda)

                print (moneda, moneda_contra,precio,porcentaje_cambio_precio,balance) 
                cursor.execute(usql,(precio , porcentaje_cambio_precio,balance,quoteVolume,moneda, moneda_contra))
                # while True:
                #     try:
                #         con.commit()
                #         break
                #     except Exception as e:
                #         print 'Error en commit, esperamos'
                #         time.sleep(20)    

                time.sleep(1)
                break
               

 

def intercambiar_monedas_negativas_por_positivas():
                                 # moneda dificiles deshabilitadas   #top 10 siempre habilitado        TUSD Y VEN #NO sirven para trade
    monedas_excluidas="        and moneda not in('HOT','NPXS','BCN','BTC','ETH','XRP','BCH','EOS','XLM','LTC','ADA','XMR','BNB','TUSD','USDT','VEN') " 

    drop_contra_usdt="DROP TEMPORARY TABLE IF EXISTS contra_usdt, deshabilitar" 

    crea_contra_usdt="CREATE TEMPORARY TABLE contra_usdt ENGINE=MEMORY  as (select moneda from pares where moneda_contra='USDT') "

    deshabilitar ="select moneda,moneda_contra from pares where habilitado =1 and balance =0 "
    deshabilitar+= monedas_excluidas
    deshabilitar+=" order by porcentaje_cambio_precio limit %s "

    crea_deshabilitar="CREATE TEMPORARY TABLE deshabilitar ENGINE=MEMORY  as (" + deshabilitar +")"
    
    

    # #HABILITAR TODOS LOS LOS PARES CON CAMBIOS POSITIVOS.
    # sql1 ="UPDATE pares set habilitado=1"
    # sql1+="  where ( (moneda_contra='BTC' and moneda not in (select moneda from contra_usdt) )  "
    # sql1+="        OR moneda_contra='USDT' ) "
    # sql1+= monedas_excluidas
    # sql1+="        and habilitado=0 "
    # #sql1+="        and porcentaje_cambio_precio>-3 "
    # sql1+="        and precio>0.00000300"

     #HABILITAR TODOS LOS LOS PARES CON CAMBIOS POSITIVOS.
    sql1 ="UPDATE pares set habilitado=1"
    sql1+="  where ( moneda_contra='BTC' ) "
    sql1+= monedas_excluidas
    sql1+="        and habilitado=0 "
    #sql1+="        and porcentaje_cambio_precio>-3 "
    sql1+="        and precio>0.00000300"




    #DESHABILITAR TODOS LOS PARES CON BALANCE EN CERO 
    sql2 ="UPDATE pares set habilitado=0"
    #sql2+="  where moneda_contra='BTC' and  moneda not in (select moneda from contra_usdt)  "
    sql2+="  where moneda_contra='BTC'"
    sql2+= monedas_excluidas
    sql2+="        and balance=0 and habilitado=1 "
    #sql2+="        and porcentaje_cambio_precio<-2"
    
    #cuenta loda habilitados
    sql3="select count(1) as cuenta from pares where habilitado=1"

    #deshabilita los primeros habilitados para mentener la cantidad deseada. 
    sql4="UPDATE pares set habilitado=0 where (moneda,moneda_contra) "
    sql4+=" in (select moneda,moneda_contra from deshabilitar)"

    #lista los habilitados
    sql5="select moneda, moneda_contra, porcentaje_cambio_precio, balance , estado_inicial , tendencia_minima_entrada , veces_tendencia_minima from pares where habilitado=1 order by porcentaje_cambio_precio;"




    print (sql1)
    print (sql2)
    print (sql4)

    #cursor.execute(drop_contra_usdt) 
    #cursor.execute(crea_contra_usdt) 

    cursor.execute(sql1)
    
    #cursor.execute(sql2)

    cursor.execute(sql3)
    chabilitados=int(cursor.fetchone()['cuenta'])
    print ('habilitados:', chabilitados)

    
    #eliminar los excesos
    pares_habilitados=150
    if chabilitados>pares_habilitados:
       nohab=chabilitados-pares_habilitados
       cursor.execute(crea_deshabilitar,(nohab,))
       cursor.execute(sql4) 
       


    # if chabilitados>0:
    #     nohab=chabilitados-37
    #     for i in range(0,nohab):
    #         cursor.execute(sql4) 

    cursor.execute(sql5)
        
    for row in cursor:
        log.log( row)

    log.log( 'habilitados:', chabilitados-nohab)

def actualizar_analisis_e7():
    volumen="40"

    cursor.execute("update pares set analisis_e7='1,2' where moneda_contra='BTC' and quotevolume>="+volumen)
    cursor.execute("update pares set analisis_e7='2'   where moneda_contra='BTC' and quotevolume<"+volumen)


        

        
    
    

actualizar_datos()
actualizar_analisis_e7()
#como he logrado monitorear todo loq ue que quiero, dehabilito de momento
#intercambiar_monedas_negativas_por_positivas()  #

db.conexion.commit()