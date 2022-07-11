# # -*- coding: UTF-8 -*-
from indicadores2 import Indicadores
from par_propiedades import *
import argparse
from logger import *
import time
from pws import Pws
from analizador import *
from binance.client import Client 



    
        

       
def analizar(par,escala):
    

    ind=Indicadores(par,log)
            
    px=ind.precio(escala)
    
    
    
    parprop=Par_Propiedades(par,client,log)

    tend=''
    adx=ind.adx(escala)
    if ind.ema_rapida_mayor_lenta(escala,5,14):
        tend='Subiendo '
    else:    
        tend='Bajando  '
    tend+=str(adx[0])+' '+str(adx[2])            

    adosc=ind.adosc(escala)

    macd=ind.macd(escala)
    macd_analisis=ind.macd_analisis(escala,30)

    atr=ind.atr(escala)
    
    sl=(atr+parprop.tickSize)/px*100


    filtro_emat = (ind.precio_mayor_ultimas_emas(escala,10,2)  and ind.ema_rapida_mayor_lenta(escala,10,55)) \
                    or ind.precio_mayor_ultimas_emas(escala,100,2)

    adx=ind.adx(escala)



     



    analizador=Analizador(ind)

    log.log( 'Análisis de ' + par +' '+escala      )
    log.log( 'precio....=',px                      )
    log.log( '..........=', tend                   )
    log.log( 'macd......=',macd[0],macd[1],macd[2] )
    log.log( 'macd_anal.=',macd_analisis           )
    log.log( 'rsi.......=',ind.rsi(escala)         )
    
    log.log( 'adosc.....=',adosc[0],adosc[1]       ) 
    log.log( 'tick      =',parprop.tickSize )
    log.log( 'cant presc=',parprop.cant_moneda_precision )
    log.log( 'tick/px.%.=',round(parprop.tickSize/px*100,8)  )
    log.log( 'Min Notio.=',round(parprop.min_notional,8)     )
    log.log( 'tick......=',parprop.tickSize  )
    log.log( 'stepSize..=',parprop.cant_moneda_precision  )
    log.log( 'atr.......=',round(atr,8)            )
    log.log( 'sl .....%.=',round(sl,2 )            )
    log.log( 'Fuerzas...=',analizador.fuezas_x_escalas('1m 5m 15m 4h 1d'  ) )
    log.log( 'F. 4h 1d..=',analizador.tiene_fuerza_en('4h 1d'  )  )
    log.log( 'F. 5m 15m.=',analizador.tiene_fuerza_en('5m 15m'  )  )
    log.log( 'EMAs Tend.=',filtro_emat   )
    log.log( 'EMAs Tend.=',filtro_emat   )
    log.log( 'ADX       =',adx   )
    

    log.log('--------------------------------------------')
    log.log( 'Precio',px)   
    horas=[1,2,4,8,16,32,64,128]
    for h in horas:
        log.log( h, ind.mp_slice(h,parprop.tickSize) )
    log.log('--------------------------------------------')

    



if __name__== "__main__":
    

   
    print ("Inicio...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-m",   "--moneda"            , help="Moneda")
    parser.add_argument("-c",   "--moneda_contra"     , help="Moenda contra")
    parser.add_argument("-s",   "--escala"            , help="Escala del anális")
    
    parser.add_argument("-v",   "--volumen"           , help="Análisis de Volumen",action='store_true')
    parser.add_argument("-e",   "--emas"              , help="Análisis de Emas",action='store_true')


    args = parser.parse_args()
 
    #valor por defecto moneda contra
    
    moneda=args.moneda.upper()
    moneda_contra=args.moneda_contra.upper()
    if moneda_contra==None:
        moneda_contra='BTC'
    par=moneda+moneda_contra

    escala=args.escala
    
    pws=Pws()
    client = Client(pws.api_key, pws.api_secret)
    log=Logger('analizar.log') 
    ind=Indicadores(par,log)

    if args.volumen:
        vol=ind.volumen_porcentajes(escala)
        log.log( 'Vol.......=',vol[4],vol[5]           )
        log.log( 'vol.contra=',ind.volumen_moneda_contra(escala))

    if args.emas:
        filtro_ultimas    = ind.precio_mayor_ultimas_emas(escala,10,2)
        filtro_emas      = ind.ema_rapida_mayor_lenta(escala,10,55)
        filtro_ema100    = ind.precio_mayor_ultimas_emas(escala,100,2)
        filtro_resultado = (filtro_ultimas  and filtro_emas) \
                    or filtro_ema100
        log.log(' ind.precio_mayor_ultimas_emas(escala,10,2)' , filtro_ultimas) 
        log.log('   ind.ema_rapida_mayor_lenta(escala,10,55)' , filtro_emas)   
        log.log('ind.precio_mayor_ultimas_emas(escala,100,2)' , filtro_ema100)   
        log.log('                                  resultado' , filtro_resultado)              




    #analizar(par,escala)



  
        


    




    print('Fin')


    
    



    #print('Par',par,'Precio',precio,'Función',funcion)


    #print (args)

    #auth = OAuthHandler(twitter_credentials.CONSUMER_KEY,twitter_credentials.CONSUMER_SECRET)
    #auth.set_access_token(twitter_credentials.ACCESS_TOKEN,twitter_credentials.ACCESS_TOKEN_SECRET)
    #stream = Stream(auth,listener)

    #stream.filter(track=db.get_palabras_claves())