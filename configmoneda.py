# # -*- coding: UTF-8 -*-
from logger import * #clase para loggear
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from indicadores2 import *
from funciones_utiles import *
from par_propiedades import Par_Propiedades
from formateadores import *
from variables_globales import VariablesEstado
from pws import Pws
import sys
import time
import traceback
import argparse


#todo: necesito: un comando para consultar los parámetros actuales de un par



if __name__== "__main__":
    print ("Inicio...")
    pws=Pws()
    client = Client(pws.api_key, pws.api_secret)

    log=Logger('config_moneda.log') 
    e = VariablesEstado()


    
#j=Indicadores('GTOBTC',client,log)

    funciones=['comprar','vender','comprar+precio','vender+ya','comprar+ya','cazaliq']

    parser = argparse.ArgumentParser()
    parser.add_argument("-d",   "--deshabilitar"      , help="Deshabilita el par, n minutos")
    parser.add_argument("-t",   "--tiempo"            , help="Tiempo de espera en segundos")
    parser.add_argument("-m",   "--moneda"            , help="Moneda")
    parser.add_argument("-c",   "--moneda_contra"     , help="Moenda contra")
    parser.add_argument("-f",   "--funcion"           , help="Función que realizará el par")
    parser.add_argument("-x",   "--precio"            , help="Precio de compra o venta según el caso")
    parser.add_argument("-xs",  "--pxsuperior"        , help="Precio superior, sirve solo para comprar+precio",action='store_false')
    parser.add_argument("-xi",  "--pxinferior"        , help="Precio inferior, sirve solo para comprar+precio",action='store_false')
    #parser.add_argument("-xa",  "--px_px_sup_auto"    , help="Crea automaticamente un -x -xs",action='store_true')
    parser.add_argument("-gs",  "--ganancia_segura"   , help="Actualiza ganancia_segura")
    parser.add_argument("-gi",  "--ganancia_infima"   , help="Actualiza ganancia_infima")
    parser.add_argument("-gr",  "--ganancia_recompra" , help="Actualiza ganancia negativa de recompra")
    parser.add_argument("-sl",  "--stop_loss"         , help="Actualiza el Stop Loss")
    parser.add_argument("-sls", "--stop_loss_subir"   , help="Inicia el stop loss, o lo sube n ticks")
    parser.add_argument("-sli", "--stop_loss_iniciar" , help="Inicia el stop loss aunque tenga que ser un sl negativo")
    parser.add_argument("-tem", "--temporalidades"    , help="Temporalidades lista entre comilla separadas por espacioes ej. '5m 15m'")
    parser.add_argument("-obs", "--observaciones"     , help="Obsercaciones que se tengan de este par y puedan ser útiles para el futuro ej. 'moneda peligrosa' ")
    parser.add_argument("-can", "--cantidad"          , help="Cantidad a comprar expresada en dolares")
    parser.add_argument("-cfg", "--config"            , help="Muestra la configuración actual del par -m -c ingresado",action='store_true')
    parser.add_argument("-vol", "--volumen"           , help="cambia el filtro de incremento_volumen_bueno")
    parser.add_argument("-gan", "--tomar_ganancias"   , help="Porcentaje de ganancias a tomar")
    parser.add_argument("-sig", "--estado_siguiente"  , help="Pasar a estado siguiente",action='store_true')
    parser.add_argument("-rei", "--reiniciar_estado"  , help="Reiniciar el estado actual",action='store_true') 
    parser.add_argument("-ven", "--vender"            , help="Vender, (pasar al estado 4)",action='store_true')  
    parser.add_argument("-esc", "--escala_entrada"    , help="Escala de análisis de entrada")
    parser.add_argument("-rsi", "--rsi_entrada"       , help="RSI análisis entrada")
    parser.add_argument("-sve", "--solo_vender"       , help="Solo vender  0 ó 1")
    parser.add_argument("-sse", "--solo_seniales"     , help="Solo señales   0 ó 1")


    args = parser.parse_args()
 

    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn.pool) 
    
    
    
    #valor por defecto moneda contra
    
    moneda=args.moneda.upper()
    moneda_contra=args.moneda_contra.upper()
    if moneda_contra==None:
        moneda_contra='BTC'


   

   

    #valida funcion
    funcion=args.funcion
    if funcion!=None:
        funcion_ok=True
        if not funcion in funciones:
            print (args.funcion, 'no es', funciones)
            funcion_ok=False
    else:
        funcion_ok=False        


    #valido par
    par_ok=False
    precio_actual=0
    try:
        p = db.get_valores(moneda,moneda_contra)
        par=moneda+moneda_contra
        print ('Par:',par,p['idpar'])
        
        if p['idpar'] != -1:
            par_ok=True
            ind=Indicadores(par,log,e,client)
            prop = Par_Propiedades(par,client,log)
            print ('Par OK')

    except Exception as e:
        print ('No se puede validar Par')


    deshabilitar=args.deshabilitar

    if deshabilitar != None and par_ok:
        
        print ('Deshabilitando', moneda,moneda_contra )
        p=db.get_valores(moneda,moneda_contra)
        idpar=p['idpar']
        db.comando_nuevo(idpar,'deshabilitar',deshabilitar)   
        
        sys.exit()





    #valido stop_loss
    stop_loss=args.stop_loss
    if stop_loss != None:
        stop_loss=float(stop_loss)
        if stop_loss>=0 and stop_loss<100 and par_ok:
            print ('Actualizando Stop Loss',stop_loss )
           
            db.stop_loss(stop_loss,moneda,moneda_contra)
                
  
    #valido temporalidades
    temporalidades=args.temporalidades
    if temporalidades != None:
        print ('Actualizando temporalidades',temporalidades )
       
        db.temporalidades(temporalidades,moneda,moneda_contra)
            
    
    #valido observaciones
    observaciones=args.observaciones
    if observaciones != None:
        print ('Actualizando observaciones',observaciones )
       
        db.observaciones(observaciones,moneda,moneda_contra)
            


    
    #valido ganancia ganancia_segura
    ganancia_segura=args.ganancia_segura
    if ganancia_segura != None:
        ganancia_segura=float(ganancia_segura)
        if ganancia_segura>1 and ganancia_segura<100 and par_ok:
            print ('Actualizando ganancia_segura',ganancia_segura )
           
            db.ganancia_segura(ganancia_segura,moneda,moneda_contra)
                 

    #valido ganancia_infima
    ganancia_infima=args.ganancia_infima
    if ganancia_infima != None:
        ganancia_infima=float(ganancia_infima)
        if ganancia_infima>0 and ganancia_infima<100 and par_ok:
            print ('Actualizando ganancia_infima',ganancia_infima )
           
            db.ganancia_infima(ganancia_infima,moneda,moneda_contra)
                 

    #valido ganancia_recompra (e3_ganancia_recompra) y la transformo en negativa siempre
    ganancia_recompra=args.ganancia_recompra
    if ganancia_recompra != None:
        ganancia_recompra= -1 * abs(float(ganancia_recompra))
        if ganancia_recompra<-4 and ganancia_recompra>-100 and par_ok:
            print ('Actualizando e3_ganancia_recompra',ganancia_recompra )
           
            db.e3_ganancia_recompra(ganancia_recompra,moneda,moneda_contra)
                 

    #valido incremento vol bueno
    volumen=args.volumen
    if volumen != None:
        volumen=abs(float(volumen))
        if volumen>0  and par_ok:
            print ('Actualizando incremento volumen bueno',ganancia_recompra )
           
            db.incremento_volumen_bueno(volumen,moneda,moneda_contra)
                 


    #valido cantidad
    cantidad=args.cantidad
    if cantidad != None:
        cantidad=float(cantidad)
        if cantidad>=0 and par_ok:
            print ('Actualizando cantidad',cantidad)
           
            db.set_cantidad(cantidad,moneda,moneda_contra)


    #valido solo vender
    solo_vender=args.solo_vender    
    if solo_vender != None:
        solo_vender=int(solo_vender)
        if 0<=solo_vender<=1 and par_ok:
            print ('Actualizando solo_vender',solo_vender)
           
            db.set_solo_vender(solo_vender,moneda,moneda_contra)

    #valido solo vender
    solo_seniales=args.solo_seniales  
    if solo_seniales != None:
        solo_seniales=int(solo_seniales)
        if 0<=solo_seniales<=1 and par_ok:
            print ('Actualizando solo_seniales',solo_seniales)
            db.set_solo_seniales(solo_seniales,moneda,moneda_contra)        


        
    #valido escala_entrada y rsi_entrada
    escala=args.escala_entrada
    if escala != None:
        if escala in  e.escala_anterior.keys() and par_ok:
            rsi = args.rsi_entrada
            if rsi != None:
                rsi = float(rsi)
                if  10 <= rsi <=90:
                    print ('Actualizando escala y rsi entrada',escala,rsi)
                    db.set_escala_rsi_entrada_par(escala,rsi,moneda,moneda_contra)






            print ('Actualizando cantidad',cantidad)
           


    precio=args.precio
    if precio!= None:
        precio_actual=ind.precio('1h')
        precio=float(args.precio)
        diferencia=abs(1-precio_actual/precio)
    else:
        precio=0 
        diferencia=0    

    #valido precio
    precio_ok=True
    if precio_actual<0 or diferencia>0.8:
        print ('Precio erroneo o mucha diferencia') 
        precio_ok=False

    #valido tiempo
    ptiempo=args.tiempo
    if ptiempo!=None:
        ptiempo=int(args.tiempo)
        if ptiempo<=0:
            ptiempo=296
    else:
        ptiempo=-1        

    


    # #auto precio y precio superior
    # px_px_sup_auto=args.px_px_sup_auto
    # if px_px_sup_auto!=None and precio==None  :
    #     mm=ind.minmax('4h',17)
    #     precio=float(mm[0]*1.005)
    #     pxsuperior=float(mm[1]*1.005)
        

    #tomar gananciaid
    if par_ok:
        gan=args.tomar_ganancias
        if gan != None:
            gan= float(gan)
            if gan >0:
                p=db.get_valores(moneda,moneda_contra)
                idpar=p['idpar']
                if idpar != -1:
                    print ('tomar ganancias',gan,'%')
                    db.comando_nuevo(idpar,'tomar_ganancias',gan)   
                    
                else:
                    print ('par',moneda,moneda_contra,' no esta en la db')
            else:
                print('porcentaje ganacias debe ser positivo')            


    #iniciar o aumentar stoplos
    
    if par_ok:
        stop_loss_subir = args.stop_loss_subir
        if stop_loss_subir != None:
            p=db.get_valores(moneda,moneda_contra)
            idpar=p['idpar']
            print ('Subir sttoploss',stop_loss_subir,'tick')
            db.comando_nuevo(idpar,'stop_loss_subir',stop_loss_subir)

    if par_ok:
        stop_loss_iniciar = args.stop_loss_iniciar
        if stop_loss_iniciar != None:
            p=db.get_valores(moneda,moneda_contra)
            idpar=p['idpar']
            print ('Iniciar  stoploss aunque sea negativo')
            db.comando_nuevo(idpar,'stop_loss_iniciar','')
            

    #estado_siguiente
    if par_ok and args.estado_siguiente:
        print ('Cambiar al estado siguiente...')
        p=db.get_valores(moneda,moneda_contra)
        idpar=p['idpar']
        db.comando_nuevo(idpar,'estado_siguiente','')  

    #reiniciar_estado
    if par_ok and args.reiniciar_estado:
        print ('Reiniciar el estado actual...')
        p=db.get_valores(moneda,moneda_contra)
        idpar=p['idpar']
        db.comando_nuevo(idpar,'reiniciar_estado','')  

    #vender
    if par_ok and args.vender:
        print ('Veder: Pasa al estado 4.')
        p=db.get_valores(moneda,moneda_contra)
        idpar=p['idpar']
        db.comando_nuevo(idpar,'vender','')  

    print(precio_actual,args.precio,diferencia)




    #deshabilitar
    if ptiempo>0 and par_ok:
        db.habilitar(0,moneda,moneda_contra)
        print('Deshabilitando, esperando',ptiempo,'...')
        time.sleep(ptiempo)

    
    #comprar+precio
    if funcion_ok and par_ok and args.funcion=='comprar+precio':

        #precio superior
        pxsuperior=args.pxsuperior
        
        if  pxsuperior:
            pxsuperior=float(pxsuperior)
        else:    
            pxsuperior=ind.promedio_de_altos('1d',2,5)
        print ('pxsuperior =' ,pxsuperior)

        #precio inferior
        pxinferior=args.pxinferior
        if pxinferior:
            pxinferior=float(pxinferior)
        else:    
            pxinferior=ind.promedio_de_bajos('1d',5,20) * 1.005 

        print ('pxinferior =' ,pxinferior)    

        if pxinferior>0 and pxsuperior>0:
            db.persistir_parametros_e8(moneda,moneda_contra,pxinferior,pxsuperior)
            db.persistir_estado(moneda,moneda_contra,precio,-1,funcion)
            print('Cambio de funciona a comprar+precio',pxinferior,pxsuperior)

    #otras funciones
    elif precio_ok and funcion_ok and par_ok:
        #print(precio_actual,args.precio,diferencia)
        print('Actualizando...')
       
        if funcion=='vender':
            estado = 3
        else: 
            estado= -1   

        if precio != 0:
            print('cambio de función y precio')
            db.persistir_estado(moneda,moneda_contra,precio,estado,funcion)
        else:
            print('cambio de función solamente (no se toca precio)')
            db.persistir_cambio_funcion(moneda,moneda_contra,estado,funcion)
    else:
        print('Funcion y precio no actualizados')


    #habilitar
    if ptiempo>0 and par_ok:
        print('Habilitando...')
        db.habilitar(1,moneda,moneda_contra)
        


             

    
    if args.config and par_ok:
       
        valores=db.get_valores(moneda,moneda_contra)
        print('*** Valores del par',moneda,moneda_contra)
        for v in valores:
            print( v,valores[v]) 

        print('---propiedades del par ---', par)
        print('prop.min_notional',prop.min_notional)
        print('prop.tickSize',format_valor_truncando(prop.tickSize,8) )
        print('variacion tick',round( prop.tickSize / ind.precio('1h') *100,8) )
        print('prop.cant_moneda_precision',prop.cant_moneda_precision)

        ind = Indicadores(moneda+moneda_contra,log,e,client)

        print('atr 4h',ind.atr('4h'))
        print('atr 1d',ind.atr('1d'))

   


    conn.desconectar()
    print('Fin')


    
    



    #print('Par',par,'Precio',precio,'Función',funcion)


    #print (args)

    #auth = OAuthHandler(twitter_credentials.CONSUMER_KEY,twitter_credentials.CONSUMER_SECRET)
    #auth.set_access_token(twitter_credentials.ACCESS_TOKEN,twitter_credentials.ACCESS_TOKEN_SECRET)
    #stream = Stream(auth,listener)

    #stream.filter(track=db.get_palabras_claves())