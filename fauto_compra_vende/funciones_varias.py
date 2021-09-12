

### funciones que probablemente no se usan ###

#retorna la variacion entre compra y ventan %
def var_compra_venta(px_compra,px_venta):
    return ( px_venta/px_compra -1   ) * 100   

def actualizar_info_pares_deshabilitados_periodicamente(e:VariablesEstado,IndPool:Pool_Indicadores,conn,client):
    time.sleep(300)# espero 5 minutitos antes de empezar a hacer algo 
    db = Acceso_DB(log,conn.pool)
    while e.trabajando:
        if e.se_puede_operar: 
            tiempo = actualizar_info_pares_deshabilitados(e,IndPool,conn,client)

            actualizar_ranking_por_volumen_global(e,IndPool,conn,client)
            
            if IndPool.btc_apto_para_altcoins:
                temporalidades='1h 4h 1d'
            else:
                temporalidades='4h 1d'      

            reconfigurar_pares_top(30,temporalidades ,'USDT',db,e)
            reconfigurar_pares_top(15,temporalidades,'BTC',db,e)


        time.sleep(1800 + tiempo) 

def control_BTC_invertido(): #Recáculo de los btc que tiene nque estan en reserva según lo que tengo comprado contra BTC
    btc=BTC_invertido()
    
    log.log('BTC expuesto',btc) 
    
    btcexponer=0.01
    if btc!=0:
        if abs(e.BTC_invertido_actual-btc)/btc > 0.1: #si hay una diferencia mayor al 10%
           e.BTC_invertido_actual=btc
           btcexponer=0.01 - btc
           e.pares['BTCUSDT'][0].cantidad_de_reserva=btcexponer - btc   
           log.log('Cambio de BTC disponibe',btcexponer)
           e.pares['BTCUSDT'][0].forzar_sicronizar=True
    elif btc==0 and  e.BTC_invertido_actual!=0:
        e.BTC_invertido_actual=0
        e.pares['BTCUSDT'][0].cantidad_de_reserva=btcexponer 
        log.log('Cambio de BTC disponibe',btcexponer)
        e.pares['BTCUSDT'][0].forzar_sicronizar=True     

def BTC_invertido(): #Recáculo de los btc que tiene nque estan en reserva según lo que tengo comprado contra BTC
    btc=0
    for k in e.pares_control.keys():
        if k.endswith('BTC') and (e.pares[k][0].estado==3 or e.pares[k][0].estado==4):
            btc+=e.pares[k][0].cant_moneda_compra * e.pares[k][0].precio
            log.log('BTC_invertido()',k,e.pares[k][0].cant_moneda_compra,e.pares[k][0].precio,e.pares[k][0].cant_moneda_compra * e.pares[k][0].precio,btc)
    return btc 

def reporte_peores(horas_hacia_atras):
    peores = hpdb.ind_historico_peores(horas_hacia_atras)
    lin=''
    if peores != None:
        for p in peores:
            lin += p[0]+p[1]+ ' ' +str(p[2]) + ' ' + str(p[3])+'\n'

    return 'Peores Monedas: ' +str(horas_hacia_atras)+' horas\n' + lin    

def deshabiliar_pares_en_compra_temporalmente_periodicamente(e:VariablesEstado):
    periodo = 600
    time.sleep( periodo )  # unos segundos para que levante todo
    loglocal=Logger('deshabiliar_pares_en_compra_temporalmente_periodicamente.log')

    while e.trabajando:
        if e.se_puede_operar: 
            #loglocal.log('inicio: deshabiliar_pares_en_compra_temporalmente_periodicamente')         
            try:
                deshabiliar_pares_en_compra_temporalmente(e,loglocal) 
            except Exception as ex:
                loglocal.log(str(ex))

            #loglocal.log('fin: deshabiliar_pares_en_compra_temporalmente_periodicamente')             

        time.sleep( periodo )  # unos segundos para que levante todo

def deshabiliar_pares_en_compra_temporalmente(e,log):
    pares_en_compra=[]
    monedas_contra=[]
    #  detecto determino los pares en compra
    for k in e.pares.keys():
        p=e.pares[k][0] # lo pongo en p para referenciarlo amigablemente
        if p.estoy_vivo and p.estado==2:
            try:
                coef = float(1-p.precio_compra/p.precio)
                pares_en_compra.append([p,coef])
                if p.moneda_contra not in monedas_contra:
                    monedas_contra.append(p.moneda_contra)
            except Exception as e:
                log.log(str(e))

    pares_en_compra.sort(key=lambda x:x[1],reverse=True)   #ordeno por el segundo elemento de la tupla  
    
    #log para ver como queda esto
    for p in (pares_en_compra):
        log.log (p[0].moneda, p[0].moneda_contra,p[1])
   
    #recorro en forma inversa y detengo 1 par de cada moneda contra
    # lo que llevan mucho tiempo o cuyo precio de compra está muy alejado del precio y por lo tanto será muy dificil comprar
    log.log('monedas_contra',monedas_contra)
    for mc in monedas_contra:
        log.log('moneda_contra',mc)
        if e.falta_de_moneda[mc]:
            e.falta_de_moneda[mc]=False #declaro satisfecha la demanda
            for x in pares_en_compra:
                p=x[0]
                if p.moneda_contra == mc:
                    coef=x[1]
                    ahora = time.time()
                    tiempo_en_estado = int(ahora - p.tiempo_inicio_estado)
                    #log.log(p.moneda,p.moneda_contra,'t.estado=',tiempo_en_estado,'coef=',coef)
                    if tiempo_en_estado > 3600 or coef>0.15:
                        p.detener_estado_2(horas=e.horas_deshabilitar_par)
                        log.log('deteniendo...',p.moneda,p.moneda_contra,x[1])
                        break



#esta funcion fue reemplazada por otra teoría de trading
# en par.py self.db.trades_cantidad_de_pares_con_trades() 

def cuenta_pares_estado2():
    '''cuenta los pares en estado 2 para cada moneda contra
       en la que se opera.
       estos valores son luego utilizado en par 
       para no supera la cantidad de pares simultaneos
       comprando
    '''
    cp = {'BUSD':0,'USDT':0,'BTC':0}

    for k in e.pares_control.keys():
        p = e.pares[k][0]
        if p.estado == 2:
            if p.moneda_contra == "USDT":
                cp["USDT"] += 1
            elif p.moneda_contra == "BTC":
                cp["BTC"] += 1

    e.pares_en_compras = cp    

def actualizar_posicion_periodicamente(e,gestor_de_posicion):
    e.actualizar_posicion()
    periodo = 300
    time.sleep( periodo )  # unos segundos para que levante todo
    
    while e.trabajando:
        if e.se_puede_operar: 
            try:
                e.actualizar_posicion()
            except Exception as ex:
                print(str(ex))

        time.sleep( periodo )  # unos segundos para que levante todo    

def matar(par):
    #e.parer[par][0].detener()
    #e.pares[par][1].join()
    e.pares[par][0].detener()
    e.pares[par][0] = None
    #del e.pares[par]
    #del e.pares_control[par]
    gc.collect()        