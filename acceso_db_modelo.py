# # -*- coding: UTF-8 -*-
import time
from datetime import datetime

class Acceso_DB:
    '''
    Este es el modelo, que se apoya en las funciones para acceso a datos
    
    '''
    
    actualiza_estado='UPDATE pares set precio_compra= %s,estado= %s, funcion= %s WHERE moneda= %s AND moneda_contra= %s'
    actualiza_func__='UPDATE pares set estado= %s, funcion= %s WHERE moneda= %s AND moneda_contra= %s'
    actualiza_parms8='UPDATE pares set e8_precio_inferior= %s, e8_precio_superior= %s WHERE moneda= %s AND moneda_contra= %s'
    actualiza_shitco='UPDATE pares set shitcoin= %s WHERE moneda= %s AND moneda_contra= %s'
    actualiza_bavopr='UPDATE pares set balance= %s, volumen= %s, precio=%s, coeficiente_ema_rapida_lenta=%s, fecha_estadisticas = NOW() WHERE moneda= %s AND moneda_contra= %s'
    actualiza_tem_1d="UPDATE pares set temporalidades='1d' WHERE habilitable=1 AND moneda_contra= %s"
    actualiza_temp__='UPDATE pares set temporalidades=%s WHERE moneda= %s AND moneda_contra= %s'

    actualiza_volpx_='UPDATE pares set volumen= %s, precio=%s,  fecha_estadisticas = NOW() WHERE moneda= %s AND moneda_contra= %s'

    obt_datos_moneda='SELECT idpar,habilitado,pstoploss,metodo_compra_venta,cantidad,precio_compra,estado,funcion,ganancia_segura,ganancia_infima,escala_analisis_entrada,rsi_analisis_entrada,tendencia_minima_entrada,solo_vender,solo_seniales,veces_tendencia_minima,xvela_corpulenta,cantidad_de_reserva,analisis_e7,e8_precio_inferior,e8_precio_superior,e3_ganancia_recompra,incremento_volumen_bueno,xobjetivo,shitcoin,min_notional,stoploss_habilitado,stoploss_cazaliq,uso_de_reserva,temporalidades,observaciones,objetivo_compra,objetivo_venta,max_entradas from pares where moneda= %s and moneda_contra= %s'
    mon_habilita_lin='SELECT moneda,moneda_contra from pares where habilitable=1 and habilitado=0 and no_habilitar_hasta < NOW() and coeficiente_ema_rapida_lenta  > 0 order by volumen desc'
    mon_habilita_feo='SELECT moneda,moneda_contra from pares where habilitable=1 and habilitado=0 and no_habilitar_hasta < NOW() and coeficiente_ema_rapida_lenta <= 0 order by volumen desc'
    mon_habilitables='SELECT moneda,moneda_contra from pares where habilitable=1 and habilitado=0 and no_habilitar_hasta < NOW() order by volumen desc'
    mon_habilitables_todos='SELECT moneda,moneda_contra from pares where habilitable=1 and habilitado=0'
    mon_count_habilitados='SELECT count(1) as cant from pares where habilitado=1'
    mon_pares_top___='select moneda,moneda_contra,volumen  from pares  where habilitable=1  and moneda_contra=%s order by volumen desc limit %s'
    par_puede_habili='SELECT moneda,moneda_contra from pares where habilitable=1 and habilitado=0 and no_habilitar_hasta < NOW() and concat(moneda,moneda_contra)=%s'
    habilitar_______='UPDATE pares set habilitado= %s WHERE habilitable=1 AND moneda= %s AND moneda_contra= %s'
    __habilitar_habilitables = 'UPDATE pares set habilitado= 1 WHERE habilitable=1 and habilitado=0'
    __deshabilitar_pares_sin_trades = ''' update pares set habilitado=0 where habilitado=1 and (moneda,moneda_contra) not in 
                                         (select moneda,moneda_contra as cantidad from trades where ejecutado=0 group by moneda,moneda_contra)
                                      '''
    trade_persistir_='INSERT INTO trades (fecha,orderid,moneda,moneda_contra,escala,senial_entrada,cantidad,precio,ganancia_infima,ganancia_segura,tomar_perdidas,ejecutado,analisis,objetivo_venta) VALUES (%s,%s,%s, %s, %s,%s,%s,%s,%s,%s,%s,0,%s,%s)'
    trade_borrar____='DELETE from trades where moneda=%s'
    trade_avg_______='SELECT sum( (cantidad-ejecutado)*precio )/sum(cantidad-ejecutado) as pcompra from trades where cantidad-ejecutado>0 moneda=%s and moneda_contra=%s'
    trade_total_mon_='SELECT sum(cantidad-ejecutado) as total from trades where moneda=%s'
    trade_total_moneda_contra = 'select sum(precio * cantidad) as total from trades where ejecutado = 0 and moneda_contra=%s'
    trade_menor_prec='SELECT idtrade,cantidad,precio,fecha,ganancia_infima,ganancia_segura,tomar_perdidas,escala,senial_entrada,ejecutado,objetivo_venta from trades where moneda=%s and moneda_contra=%s and ejecutado=0 order by precio limit 1'
    trade_venta_orid='SELECT idtrade,cantidad,precio,fecha,ganancia_infima,ganancia_segura,tomar_perdidas,escala,senial_entrada,ejecutado from trades where ejec_orderid=%s limit 1'
    trade_compr_orid='SELECT idtrade,cantidad,precio,fecha,ganancia_infima,ganancia_segura,tomar_perdidas,escala,senial_entrada,ejecutado from trades where orderid=%s limit 1'
    trade_ultimo____='SELECT idtrade,ejec_precio,ejec_fecha,tomar_perdidas from trades where moneda=%s and moneda_contra=%s and ejecutado>0 order by ejec_fecha desc limit 1'
    trades_pares_act=''' select count(1) as cant_pares_activos from (
                        select moneda,moneda_contra as cantidad from trades where ejecutado=0 group by moneda,moneda_contra) as pares_en_trades 
                     '''
    
    trade_id________='SELECT * from trades where idtrade=%s'
    trades_cantidad_='select count(1) as cantidad  from trades where moneda=%s and moneda_contra=%s and ejecutado = 0'
    trade_borrar_id_='DELETE from trades where idtrade=%s'
    trade_btc_reserv="select cantidad-ejecutado as cantidad from trades where moneda='BTC' and ejecutado=0 order by precio limit 1"
    trades_pend_no_h='''select trades.moneda, trades.moneda_contra, trades.precio from trades,pares 
                        where 
                        trades.moneda=pares.moneda and trades.moneda_contra=pares.moneda_contra
                        and ejecutado=0 and habilitado=0 and habilitable=1 order by moneda,moneda_contra,trades.precio
                     '''

    velas_actualizar=''' UPDATE velas set open=%s,high=%s,low=%s,close=%s,volume=%s,close_time=%s 
                         WHERE id_par_escala=%s and open_time=%s '''
    
    velas_act_rsi__ =''' UPDATE velas set rsi=%s WHERE id_par_escala=%s and open_time=%s '''                      

    velas_get_vela__='SELECT * from velas where id_par_escala=%s and open_time=%s'                 

    velas_get_sig___='SELECT * from velas where id_par_escala=%s and open_time > %s order by open_time limit 1'

    velas_get_velas_='SELECT * from velas where id_par_escala=%s and open_time between %s and  %s'
    
    pares_lista_habi='select moneda,moneda_contra,balance from pares where habilitado=1 order by balance desc ,volumen desc'
    cta_pares__activ='select count(1) as cuenta from pares where habilitado=1'

    
    ind_inserta_hist='INSERT into ind_historico (idpar,idind,valor) VALUES (%s,%s,%s)'
    ind_ultimo_regis='select idpar,idind,fecha,valor from ind_historico where idpar=%s order by fecha desc limit 1'
    ind_alcis_bajist=''' select * from (
                            select 1 as alcista, count(1) as cant from (
                                select moneda,moneda_contra,avg(valor) as v from pares,ind_historico where
                                pares.idpar=ind_historico.idpar
                                and fecha > %s
                                and valor >= %s
                                group by moneda,moneda_contra
                            ) x
                            UNION ALL
                            select 0 as alcista, count(1) as cant from (
                                select moneda,moneda_contra,avg(valor) as v from pares,ind_historico where
                                pares.idpar=ind_historico.idpar
                                and fecha > %s
                                and valor < %s
                                group by moneda,moneda_contra
                            ) y
                        ) totales order by alcista desc'''

    cmd____get_lista= 'select * from comandos where idpar=%s and ejecutado=0 order by fecha'
    
    ind_peores_casos='''select pares.moneda,pares.moneda_contra, ind_historico.fecha,ind_historico.valor from ind_historico,pares 
                        where ind_historico.idpar=pares.idpar 
                        and fecha BETWEEN DATE_SUB(NOW() , INTERVAL %s HOUR) AND NOW() 
                        order by valor 
                        limit 30'''

    ind_borrar_viejo='select * from ind_historico where fecha < DATE_SUB(NOW(), INTERVAL 60 DAY) ' # solo consevamos los ultimos 60 dias           
    

    ranking_por_volumen='''select moneda,moneda_contra from (
                            select idpar,moneda,moneda_contra,volumen from pares 
                            where habilitable=1 and moneda_contra='usdt'
                            union all
                            select idpar,moneda,moneda_contra,volumen * %s from pares 
                            where habilitable=1 and moneda_contra='btc'
                            ) a
                            order by volumen desc  
    '''
    precio_par = 'select precio from pares where moneda=%s and moneda_contra=%s'


    def __init__(self,log,fxdb):
        self.log=log
        self.fxdb = fxdb
        
    def trades_pendientes_no_habilitados(self):
        return self.fxdb.ejecutar_sql_ret_dict(self.trades_pend_no_h)

    def trade_persistir(self,moneda,moneda_contra,escala,senial_entrada,cantidad,precio_compra,objetivo_venta,ganancia_infima,ganancia_segura,tomar_perdidas,analisis,fecha,orderid):
        if fecha==None:
            now = datetime.now()
            fecha = now.strftime('%Y-%m-%d %H:%M:%S')

        self.fxdb.ejecutar_sql(self.trade_persistir_,(fecha,orderid,moneda,moneda_contra,escala,senial_entrada,cantidad,precio_compra,ganancia_infima,ganancia_segura,tomar_perdidas,analisis,objetivo_venta))
        
    def trade_sumar_ejecutado(self,idtrade,cantidad,precio,fecha,orderid):
        
        if fecha==None:
            now = datetime.now()
            fecha = now.strftime('%Y-%m-%d %H:%M:%S')
        
        sql='UPDATE trades set ejecutado = ejecutado + %s, ejec_precio=%s, ejec_fecha=%s, ejec_orderid=%s where idtrade=%s'
        self.fxdb.ejecutar_sql(sql,(cantidad,precio,fecha,orderid,idtrade))
        
    
    def trades_completar_ejecutados(self,moneda,moneda_contra):
        sql='update trades set ejecutado=cantidad where moneda=%s and moneda_contra=%s and ejecutado<cantidad'
        self.fxdb.ejecutar_sql(sql,(moneda,moneda_contra))


    def trade_duracion_en_segundos(self,idtrade):
        sql='select time_to_sec(timediff(ejec_fecha,fecha)) from trades where idtrade=%s'   
        return self.fxdb.ejecutar_sql_ret_1_valor(sql,(idtrade,))

    def trades_cantidad_de_pares_con_trades(self):
        ''' entrega la cantidad de pares que tienen trades (suma 1 por cada para que exista en trades abiertos) sin importar 
        la cantidad de trades abiertos existentes por cada par'''
        return self.fxdb.ejecutar_sql_ret_1_valor(self.trades_pares_act)

    def trades_cantidad(self,moneda,moneda_contra):
        ''' retorna la cantidad de trades que hay en un par'''
        return self.fxdb.ejecutar_sql_ret_1_valor(self.trades_cantidad_,(moneda,moneda_contra))    

    def total_moneda_en_trades(self,moneda):
         
        total = self.fxdb.ejecutar_sql_ret_1_valor(self.trade_total_mon_,(moneda,))
        if total==None:
            total=0
        return total   

    def total_moneda_contra_en_trades(self,moneda_contra):
        total = self.fxdb.ejecutar_sql_ret_1_valor(self.trade_total_moneda_contra,(moneda_contra,))
        if total==None:
            total=0
        return total     

    def trade_borrar_id(self,idtrade):
        self.fxdb.ejecutar_sql(self.trade_borrar_id_,(idtrade,))
        

    def _DEPRECATED_trade_avg(self,moneda,moneda_contra):
        p=self.fxdb.ejecutar_sql_ret_dict(self.trade_avg_______,(moneda,moneda_contra))
        
        ret=p['pcompra']
        if ret==None:
            ret=0  
        return ret

    def get_trade_menor_precio(self,moneda,moneda_contra):
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_menor_prec,(moneda,moneda_contra))
  
        if len(r)==0:
            p={'idtrade': -1, 'cantidad': -1, 'precio': -1, 'fecha': None,'tomar_perdidas':0,'ejecutado':0}
        else:
            p=r[0]

        return p  
     
    def get_trade_venta_orderid(self,orderid):
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_venta_orid,(orderid,))
  
        if len(r)==0:
            p={'idtrade': -1, 'cantidad': -1, 'precio': -1, 'fecha': None,'tomar_perdidas':0,'ejecutado':0}
        else:
            p=r[0]

        return p  

    def get_trade_compra_orderid(self,orderid):
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_compr_orid,(orderid,))
  
        if len(r)==0:
            p={'idtrade': -1, 'cantidad': -1, 'precio': -1, 'fecha': None,'tomar_perdidas':0,'ejecutado':0}
        else:
            p=r[0]

        return p  

    def get_ultimo_trade_cerrado(self,moneda,moneda_contra):
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_ultimo____,(moneda,moneda_contra))
  
        if len(r)==0:
            p={'idtrade': -1, 'ejec_precio': -1, 'ejec_fecha': None}
        else:
            p=r[0]

        return p    

    def get_trade_id(self,id):
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_id________,(id,))
  
        if len(r)==0:
            p={'idtrade': -1,'moneda': '', 'moneda_contra': ''}
        else:
            p=r[0]

        return p  

    #devuelve la cantidad de btc conta pax o usdt etc que está en juego para poder reservarlos 
    def trade_btc_tradeando(self): 
        r=self.fxdb.ejecutar_sql_ret_dict(self.trade_btc_reserv)
        if len(r)==0:
            p={'cantidad': 0}
        else:
            p=r[0]    
        return p['cantidad']    

    def persistir_shitcoin(self,shitcoin,moneda,moneda_contra):
        self.fxdb.ejecutar_sql(self.actualiza_shitco,(shitcoin,moneda,moneda_contra))

    def par_persistir_datos_estadisticos(self,moneda,moneda_contra,balance,volumen,precio,coef_emar_emal):
        self.fxdb.ejecutar_sql(self.actualiza_bavopr, (float(balance),float(volumen),float(precio),float(coef_emar_emal),moneda,moneda_contra) ) 

    def par_persistir_volumen_precio(self,moneda,moneda_contra,volumen,precio):
        self.fxdb.ejecutar_sql(self.actualiza_volpx_, (float(volumen),float(precio),moneda,moneda_contra) )     

    def persistir_estado(self,moneda,moneda_contra,precio_compra,estado,funcion):
        self.fxdb.ejecutar_sql(self.actualiza_estado,(precio_compra,estado,funcion,moneda,moneda_contra))
        
    def temporalidades(self,temporalidades,moneda,moneda_contra):
        self.fxdb.ejecutar_sql( self.actualiza_temp__, (temporalidades,moneda,moneda_contra)  )

    def temporalidades_a_1d(self,moneda_contra):
        self.fxdb.ejecutar_sql( self.actualiza_tem_1d, (moneda_contra,)  )
    
    def observaciones(self,observaciones,moneda,moneda_contra):
        sql='UPDATE pares set observaciones=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (observaciones,moneda,moneda_contra)  )
        
    def ganancia_infima(self,ganancia_infima,moneda,moneda_contra):
        sql='UPDATE pares set ganancia_infima=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (ganancia_infima,moneda,moneda_contra)  )

    def ganancia_segura(self,ganancia_segura,moneda,moneda_contra):
        sql='UPDATE pares set ganancia_segura=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (ganancia_segura,moneda,moneda_contra)  )

    def stop_loss(self,stop_loss,moneda,moneda_contra):
        sql='UPDATE pares set pstoploss=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (stop_loss,moneda,moneda_contra)  )
        
    def e3_ganancia_recompra(self,e3_ganancia_recompra,moneda,moneda_contra):
        sql='UPDATE pares set e3_ganancia_recompra=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (e3_ganancia_recompra,moneda,moneda_contra)  )

    def incremento_volumen_bueno(self,p_inc_vol_bue,moneda,moneda_contra):
        sql='UPDATE pares set incremento_volumen_bueno=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (p_inc_vol_bue,moneda,moneda_contra)  )
        
    def set_cantidad(self,cantidad,moneda,moneda_contra):
        sql='UPDATE pares set cantidad=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (cantidad,moneda,moneda_contra )  )

    def set_solo_vender(self,solo_vender,moneda,moneda_contra):
        sql='UPDATE pares set solo_vender=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (solo_vender,moneda,moneda_contra )  )

    def set_solo_seniales(self,solo_seniales,moneda,moneda_contra):
        sql='UPDATE pares set solo_vender=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (solo_seniales,moneda,moneda_contra )  )

    def set_escala_rsi_entrada_par(self,escala_analisis_entrada,rsi_analisis_entrada,moneda,moneda_contra):
        sql='UPDATE pares set escala_analisis_entrada=%s, rsi_analisis_entrada=%s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (escala_analisis_entrada,rsi_analisis_entrada,moneda,moneda_contra )  )

            
    def persistir_cambio_funcion(self,moneda,moneda_contra,estado,funcion):
        self.fxdb.ejecutar_sql(self.actualiza_func__,(estado,funcion,moneda,moneda_contra))
        
    def persistir_parametros_e8(self,moneda,moneda_contra,e8_precio_inferior,e8_precio_superior):
        self.fxdb.ejecutar_sql(self.actualiza_parms8,(e8_precio_inferior,e8_precio_superior,moneda,moneda_contra))

    def deshabilitar_todos_los_pares(self):
        sql="UPDATE pares set habilitado=0 WHERE habilitado=1 and funcion !='stoploss'"
        self.fxdb.ejecutar_sql(sql)

    def insertar_par(self,moneda,moneda_contra,observaciones):
        sql="INSERT into pares (moneda,moneda_contra,habilitado,habilitable,solo_seniales,temporalidades,observaciones) values (%s,%s,0,0,1,'1d',%s)"
        self.fxdb.ejecutar_sql(sql,(moneda,moneda_contra,observaciones))

    #esta funciona debe remplazar a persistir_estado
    def actualizar_estado(self,moneda,moneda_contra,precio_compra,estado_inicial):
       self.fxdb.ejecutar_sql(self.actualiza_estado,(precio_compra,estado_inicial,moneda,moneda_contra))

    def set_no_habilitar_hasta(self,fecha_hasta,moneda,moneda_contra):
        sql='UPDATE pares set no_habilitar_hasta=%s,habilitado=0 WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql( sql, (fecha_hasta,moneda,moneda_contra )  )
  
    def persistir_ganancias(self,ganancias,moneda,moneda_contra):
        #9/5/2019 no se para que sirve la variable balance, sa saco
        #actua__ganancias='UPDATE pares set ganancias=ganancias + %s , balance= %s WHERE moneda= %s AND moneda_contra= %s'
        sql='UPDATE pares set ganancias=ganancias + %s WHERE moneda= %s AND moneda_contra= %s'
        self.fxdb.ejecutar_sql(sql,(ganancias,moneda,moneda_contra))


    def ind_historico_insert(self,idpar,idind,valor):
        self.fxdb.ejecutar_sql(self.ind_inserta_hist,(idpar,idind,valor))

    def ind_historico_ultimo_registro(self,idpar):
        r=self.fxdb.ejecutar_sql_ret_dict(self.ind_ultimo_regis,(idpar,))
        if len(r)==0:
            p={'idpar': -1,'idind':-1, 'fecha': '', 'valor': None}
        else:
            p=r[0]
        return p  

    def ind_historico_get_ultimos(self,idpar,fecha_desde):
        sql='select fecha,valor from ind_historico where idpar=%s and fecha>%s'
        r=self.fxdb.ejecutar_sql_ret_cursor(sql,(idpar,fecha_desde))
        return r
    
    def ind_historico_alcista_bajista(self,fecha,porcentaje_corte):
        
        cursor=self.fxdb.ejecutar_sql_ret_cursor(self.ind_alcis_bajist,(fecha,porcentaje_corte,fecha,porcentaje_corte))       #(fecha,porcentaje_corte,fecha,porcentaje_corte)
        
        return cursor[0][1],cursor[1][1]


    def ind_historico_peores(self,horas_hacia_atras):
        self.fxdb.ejecutar_sql( self.ind_borrar_viejo ) #hacemos limpieza primero

        try:  
            cursor=self.fxdb.ejecutar_sql_ret_cursor(self.ind_peores_casos,(horas_hacia_atras,)) 
        except:
            
            cursor = None    

        return cursor

    def habilitar_en_el_futuro(self,moneda,moneda_contra,fecha_futura):
        sql="UPDATE pares set habilitado=0 ,habilitable=1, no_habilitar_hasta=%s  WHERE moneda= %s AND moneda_contra= %s"
        self.fxdb.ejecutar_sql(sql,(fecha_futura,moneda,moneda_contra) )

    def habilitar(self,habilitar_on_off,moneda,moneda_contra):
        self.fxdb.ejecutar_sql(self.habilitar_______,(habilitar_on_off,moneda,moneda_contra) )
    
    def habilitar_habilitables(self): 
        self.fxdb.ejecutar_sql(self.__habilitar_habilitables )
    
    def deshabilitar_pares_sin_trades(self):
        self.fxdb.ejecutar_sql(self.__deshabilitar_pares_sin_trades )

    def get_habilitables_lindos(self):
        r=self.fxdb.ejecutar_sql_ret_dict(self.mon_habilita_lin)
        
        return r

    def get_count_habilitados(self):
        total = self.fxdb.ejecutar_sql_ret_1_valor(self.mon_count_habilitados)
        if total==None:
            total=0
        return total       

    def get_pares_top(self,top,moneda_contra):
        r=self.fxdb.ejecutar_sql_ret_dict(self.mon_pares_top___,(moneda_contra,top))
        return r    

    def get_habilitables_feos(self):
        r=self.fxdb.ejecutar_sql_ret_dict(self.mon_habilita_feo)
        
        return r
    
    def get_habilitables(self):
        r=self.fxdb.ejecutar_sql_ret_dict(self.mon_habilitables)
        
        return r   

    def get_habilitables_todos(self):
        r=self.fxdb.ejecutar_sql_ret_dict(self.mon_habilitables_todos)
        
        return r   


    def se_puede_habilitar(self,par):  
        r=self.fxdb.ejecutar_sql_ret_dict(self.par_puede_habili,(par,))
        return len(r) > 0 #si hay registros, se puede habilitar

    def get_valores(self,moneda,moneda_contra):
        r=self.fxdb.ejecutar_sql_ret_dict(self.obt_datos_moneda,(moneda,moneda_contra))
        if len(r)==0:
            p={'idpar': -1,'moneda': '', 'moneda_contra': ''}
        else:
            p=r[0]
        return p
    
    # par_escala
    def get_id_par_escala(self,par,escala):
        idpar = self.get_idpar(par)
        id_par_escala = None
        if idpar is None:
            id_par_escala = None
        else:
            id_par_escala = self.get_id_par_escala_de_idpar(idpar,escala)
            if id_par_escala is None:
                self.crear_nuevo_par_escala(idpar,escala)
                id_par_escala = self.get_id_par_escala_de_idpar(idpar,escala)

        return id_par_escala        

    def crear_nuevo_par_escala(self,idpar,escala):
        sql = f'INSERT into par_escala (idpar,escala) values ({idpar},"{escala}")'
        self.fxdb.ejecutar_sql(sql)        

    def get_id_par_escala_de_idpar(self,idpar,escala):
        '''
        retorna id_par_escala sabiendo que existe idpar
        '''
        sql = f'select id_par_escala from par_escala where idpar={idpar} and escala="{escala}"'
        return self.fxdb.ejecutar_sql_ret_1_valor(sql)
    
    def get_idpar(self,par):
        sql = f'select idpar from pares where concat(moneda,moneda_contra) = "{par.upper()}"'
        return self.fxdb.ejecutar_sql_ret_1_valor(sql)

    # par_escala fin

    ###### velas

    def crear_actualizar_vela(self,id_par_escala,open_time,open,high,low,close,volume,close_time):
        velas_crea_actualiza=f''' INSERT into velas (id_par_escala,open_time,open,high,low,close,volume,close_time)
                              VALUES ({id_par_escala},{open_time},{open},{high},{low},{close},{volume},{close_time}) 
                              ON DUPLICATE KEY UPDATE 
                              open={open},high={high},low={low},close={close},volume={volume},close_time={close_time} 
                         
                          '''
        ret = self.fxdb.ejecutar_sql(velas_crea_actualiza)
        #if ret == -1: #error de entrada dupliadas, actualizamos
        #    ret = self.fxdb.ejecutar_sql_sin_cursor(self.velas_actualizar,(open,high,low,close,volume,close_time,id_par_escala,open_time,))
        return ret    

    def actualizar_velas_rsi(self,id_par_escala,open_time,rsi):
        ret = self.fxdb.ejecutar_sql(self.velas_act_rsi__,(rsi,id_par_escala,open_time))    
        
    
    def get_vela_siguiente(self,id_par_escala,open_time):
        r=self.fxdb.ejecutar_sql_ret_1_valor(self.velas_get_sig___,(id_par_escala,open_time))

    def get_vela(self,id_par_escala,open_time):
        r=self.fxdb.ejecutar_sql_ret_dict(self.velas_get_vela__,(id_par_escala,open_time)  )
        return r

    def get_velas_rango(self,par, escala, open_time_ini, open_time_fin):
        id_par_escala = self.get_id_par_escala(par,escala)
        r=self.fxdb.ejecutar_sql_ret_cursor (self.velas_get_velas_,(id_par_escala, open_time_ini, open_time_fin))
        return r    


    ##### velas fin



    def get_monedas_con_trades_activos(self,moneda_contra):
        return self.fxdb.ejecutar_sql_ret_dict('select count(1) as cant_trades,moneda,moneda_contra from trades where ejecutado< cantidad group by moneda_contra,moneda having moneda_contra= %s order by cant_trades',(moneda_contra,))
        
    
    def get_cuenta_pares_activos(self):
        return self.fxdb.ejecutar_sql_ret_1_valor(self.cta_pares__activ)

    def lista_de_pares_activos(self):
        return self.fxdb.ejecutar_sql_ret_dict(self.pares_lista_habi)

    def lista_de_pares_activos_con_trades(self):
        sql  = 'select pares.moneda,pares.moneda_contra,0 as balance from trades,pares '
        sql += 'where pares.moneda=trades.moneda and pares.moneda_contra=trades.moneda_contra and '
        sql += 'trades.ejecutado=0 and pares.habilitado=1 '
        sql += 'group by moneda, moneda_contra'
        return self.fxdb.ejecutar_sql_ret_dict(sql)

    def precio(self,moneda,moneda_contra):
        return  self.fxdb.ejecutar_sql_ret_1_valor(self.precio_par,(moneda,moneda_contra))

    def ranking_de_monedas_por_volumen(self,pxbtcusdt=None):
        if pxbtcusdt is None:
            pxbtc=self.precio('BTC','USDT')
        else:
            pxbtc = pxbtcusdt

        return self.fxdb.ejecutar_sql_ret_cursor(self.ranking_por_volumen,(pxbtc,))


###---------------------COMANDOS-------------------------------###
    def comando_nuevo(self,idpar,comando,parametros):
        sql='INSERT into comandos (idpar,comando,parametros) VALUES (%s,%s,%s)'
        return self.fxdb.ejecutar_sql(sql, (idpar,comando,parametros) )

    def comando_get_lista(self,idpar):
        return self.fxdb.ejecutar_sql_ret_dict(self.cmd____get_lista,(idpar,))

    def comando_respuesta(self,idcomando,respuesta ):
        sql='UPDATE comandos set respuesta=%s,ejecutado=1 where idcomando=%s'
        return self.fxdb.ejecutar_sql(sql,(respuesta,idcomando)  )

###---------------------FIN-COMANDO----------------------------###
###---------------------REPORTES-------------------------------###

    def trades_ejecutados_y_ganancia(self,mes,anio):
        sql="""select moneda_contra, 
               count(1) as cantidad, 
               sum( round(ejec_precio*ejecutado - precio*cantidad - ejec_precio*ejecutado*0.001 - precio*cantidad*0.001 ,8) )  as resultado
            from trades 
            where 
                ejecutado = cantidad and
                month(fecha) = %s and 
                year(fecha) = %s 
            group by moneda_contra """

        return self.fxdb.ejecutar_sql_ret_dict( sql, (mes,anio) )  


    def trades_abiertos(self,mes,anio):
        sql="""select idtrade,fecha, moneda, moneda_contra, senial_entrada,analisis,cantidad,precio,ganancia_infima,ganancia_segura,tomar_perdidas 
            from trades 
            where 
                ejecutado < cantidad and
                month(fecha) = %s and 
                year(fecha) = %s 
            order by fecha    
            """

        return self.fxdb.ejecutar_sql_ret_dict( sql, (mes,anio) )        


###---------------------FIN-REPORTES-------------------------------###


##############################################################################################################
#########################################  API ###############################################################
##############################################################################################################     
    def api_trades_ejecutados_y_ganancia(self,mes,anio):
        sql="""select moneda_contra, 
               count(1) as cantidad, 
               sum( round(ejec_precio*ejecutado - precio*cantidad - ejec_precio*ejecutado*0.001 - precio*cantidad*0.001 ,8) )  as resultado
            from trades 
            where 
                ejecutado = cantidad and
                month(fecha) = %s and 
                year(fecha) = %s 
            group by moneda_contra """

        return self.fxdb.ejecutar_sql_ret_cursor( sql, (mes,anio) )  

##############################################################################################################
##############################################################################################################
##############################################################################################################
#para ver en el futuro con el tema de twitter.

    def get_palabras_claves(self):
        cursor=self.conexion.cursor()
        cursor.execute('select palabras_clave from criptomonedas where habilitado=1')
        palabras_claves=[]
        for row in cursor:
            palabras_claves.extend(row['palabras_clave'].split(' ')) #agrego a palabras claves la lista de creada desde row 
        return palabras_claves    

    def get_lista_de_criptos(self,tweet):
        cursor=self.conexion.cursor()
        cursor.execute('SELECT idcripto, palabras_clave from criptomonedas ')
        lista_monedas=[]
        simbolos=['#','@','$']
        tweet=tweet.lower()
        for row in cursor:
            palabras_clave=row['palabras_clave'].split(' ')
            for p in palabras_clave: 
                if tweet.find(p) != -1:
                    lista_monedas.append(row['idcripto'])
                    break
                else:
                    for s in simbolos:
                        
                        if tweet.find(s+p) != -1:
                            lista_monedas.append(row['idcripto'])
                            break

        return lista_monedas        

    def valorar_tweet(self,lista_palabras_tweet):
        valor=0
        cursor=self.conexion.cursor()
        busca='select valor from palabras where palabra = %s'
        for ptweet in lista_palabras_tweet:
            try:
                cursor.execute(busca, (ptweet,))
                for row in cursor:
                    valor=valor+row['valor']
            except Exception as e:
                print (str(e))
        return valor 

