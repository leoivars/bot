#from abc import ABC,abstractmethod
from datetime import timedelta
import time


from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing


from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from binance.client import Client #para el cliente
from fpar.filtros import filtro_parte_baja_rango, filtro_xvolumen_de_impulso,filtro_dos_emas_positivas,filtro_parte_alta_rango,filtro_de_rsi_minimo_cercano,filtro_tres_emas_positivas
from fpar.filtros import filtro_ema_rapida_lenta,filtro_rsi
from fpar.ganancias import calculo_ganancias,precio_de_venta_minimo


from pws import Pws

class Estrategia():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    def __init__(self,par,log,estado_general, mercado):
        self.log: Logger = log
        self.g: Global_State = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        self.escala_de_analisis ='?'
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        #print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def decision_de_compra(self,escala,coef_bajo,pmin_impulso,em12):
        '''
        agrupo acá todos los grandes filtros que toman la dicisión nucleo
        y que luego de ejecutan constantemente  en estado 2
        para mantener el estado de compra
        '''
        ind = self.ind
        comprar= False
        
        if not comprar:
            ret = self.filtros_desicion(escala,50,coef_bajo,pmin_impulso,rsi,(2,3))
            if ret[0]:
                #if ind.control_de_inconsistemcias(esc) == -1: #no hay inconsitencias
                self.escala_de_analisis = ret[1]
                self.sub_escala_de_analisis = ret[1]
                self.analisis_provocador_entrada=ret[2]
                comprar = True
                                        

        return comprar 

    def decision_venta(self,pxcompra,gan_min,escala=None):
        ind: Indicadores =self.ind

        if escala:
            escala_de_salida = escala
        else:
            escala_de_salida = '15m'    
        
        self.log.log(f'escala_de_salida {escala_de_salida}' )    

        if not filtro_parte_alta_rango(ind,self.log,escala_de_salida,90):
            return False   

        gan =   calculo_ganancias(self.g,pxcompra,ind.precio(escala))

        gan_min = self.g.ganancia_minima[escala_de_salida]
        precio_bajista = ind.el_precio_es_bajista(escala_de_salida)
        precio_no_sube = ind.no_sube(escala_de_salida)
        self.log.log(f'gan_min {gan_min} gan {gan} px_bajista {precio_bajista} px_no_sube {precio_no_sube}' )
                 
        if gan < 0.3:# or self.no_se_cumple_objetivo_venta():
            return False
        elif gan < gan_min and not precio_bajista:
            return False

        marca_salida='S>>>'    


        rsi_max,rsi_max_pos,rsi = ind.rsi_maximo_y_pos(escala_de_salida,5)
        self.log.log(f'rsi {rsi} rsi_max {rsi_max} rsi_max_pos {rsi_max_pos}')
        
        lista_max = ind.lista_picos_maximos_ema(escala_de_salida,periodos=9,cvelas=10,origen='close',izquierda=5,derecha=2)

        if lista_max:
            pos_max = lista_max[0][0] 
            if pos_max <= 3 and rsi > 70:
                self.log.log(f'{marca_salida} rsi > 70 y picoema {lista_max}')
                return True

        if rsi_max > 90 and rsi_max > rsi and  1<= rsi_max_pos <= 3 and gan>gan_min: ## and self.filtro_volumen_calmado(self.escala_de_analisis):
            self.log.log(f'{marca_salida} rsi_max  > 90 {rsi_max}')
            return True

        if rsi_max > 70 and rsi_max > rsi and 1<= rsi_max_pos <= 4 and precio_no_sube: 
            self.log.log(f'{marca_salida} rsi_max > 70 {rsi_max}')
            return True
        
        if rsi_max > 53 and rsi_max > rsi and 1<= rsi_max_pos <= 3 and precio_bajista:
            self.log.log(f'{marca_salida} rsi_max > 53 {rsi_max} ,precio_bajista')
            return True

        if rsi_max > 50 and rsi_max > rsi and 1<= rsi_max_pos <= 3 and ind.precio_bajo_ema_importante(escala_de_salida):
            self.log.log(f'precio_bajo_ema_importante')
            return True

        
        return False
      

    def precio_de_compra(self):
        px,_=self.calculador_px_compra.calcular_precio_de_compra('mercado',self.escala_de_analisis)
        return px

    def precio(self,escala=None):
        if escala is None:
            escala = self.escala_de_analisis
        return self.ind.precio(escala)

    def stoploss(self,escala):
        sl = self.ind.minimo(escala,cvelas=3)  
        #recorrido = self.ind.recorrido_maximo(escala,290)
        precio = self.precio()
        if sl > self.precio():
            sl = precio - self.ind.recorrido_promedio(escala,50)
        return sl

    def stoploss_subir(self,sl_actual,pxcompra):
        #minimo = self.ind.minimo(self.escala_de_analisis,cvelas=3)  
        px_salir_derecho = precio_de_venta_minimo(self.g,0.1,pxcompra)
        precio = self.precio()
        sl = 0
        if precio > px_salir_derecho :
            sl = px_salir_derecho + (  (precio - px_salir_derecho) /2 )

        if sl > sl_actual:
            self.log.log(f'sl de {sl_actual} --> {sl}')
        else:    
            sl = sl_actual    

        return sl    

    def scalping_parte_muy_baja(self,escala,cvelas_rango=90,porcentaje_bajo=.2,p_xmin_impulso=50,em123=(4,7,21)):
        self.log.log('====== scalping_parte_muy_baja ======')
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):                              #estoy en la parte baja del rango
            if filtro_xvolumen_de_impulso(ind,self.log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):                   #hay volumen 27x mayor en total durante la bajada
                if filtro_dos_emas_positivas(ind,self.log,escala,ema1_per=em123[0],ema2_per=em123[1]):                                #giro en el precio
                    ret = [True,escala,f'scalping_parte_muy_baja{cvelas_rango}_{porcentaje_bajo}']
        return ret            

    def filtros_desicion(self,escala,cvelas_rango=90,porcentaje_bajo=.2,p_xmin_impulso=50,rsi_inf=30,pos_rsi_inf=(2,3)):
        self.log.log('====== ema_rapida_lenta_xvolumen ======')
        ret=[False,'xx']
        ind: Indicadores = self.ind
        if filtro_parte_baja_rango(self.ind,self.log,escala,cvelas_rango,porcentaje_bajo):
            if filtro_xvolumen_de_impulso(self.ind,self.log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):
                if filtro_de_rsi_minimo_cercano(self.ind,self.log,escala,rsi_inf,pos_rsi_inf):
                   ret = [True,escala,f'ema_rapida_lenta_xvolumen'] 

        # if filtro_ema_rapida_lenta(ind,self.log,escala,rapida=em123[0],lenta=em123[1],diferencia=0.1):  
        #     if filtro_xvolumen_de_impulso(ind,self.log,escala,periodos=14,sentido=0,xmin_impulso=p_xmin_impulso):
        #         ret = [True,escala,f'scalping_parte_muy_baja{cvelas_rango}_{porcentaje_bajo}']
        
        return ret    

#if filtro_tres_emas_positivas(ind,self.log,escala,ema1_per=em123[0],ema2_per=em123[1],ema3_per=em123[2]):   


def cerrar_opercion(gan,ganancia,gananciap,ganadas,perdidas,entradas,comprado):
    ganancia += g.calculo_ganancia_total(comp_px,px_vta,cantidad)
    gananciap+=gan
    if gan >0:
        ganadas+=1
    else:
        perdidas+=1    
    entradas+=1
    log.log (f'----->Termina operacion gan {gan} entradas {entradas}') 
    comprado=False


if __name__=='__main__':
    log=Logger(f'estrategia_{time.time()}.log')
    log_resultados=Logger(f'estrategia_resultados.log')
    pws=Pws()
    
    from pymysql.constants.ER import NO
   
    from acceso_db_sin_pool_conexion import Conexion_DB_Directa
    from acceso_db_sin_pool_funciones import Acceso_DB_Funciones
    from acceso_db_modelo import Acceso_DB

    client = Client(pws.api_key, pws.api_secret)

    conn=Conexion_DB_Directa(log)                          
    fxdb=Acceso_DB_Funciones(log,conn)        
    db = Acceso_DB(log,fxdb)   

    g = Global_State()

    #fini='2021-06-16 00:00:00' 
    #ffin='2021-07-01 23:59:59' 
    
    #parametros de al simulacion
    escalas=['1m']
    escalas_mercados=['1m']
    emas12=[(5,10)]
    vrsi=[x for x in range(15,35)]
    #coficientes_bajo=[0.786,0.618,.5,0.382,0.236]
    coficientes_bajo=[0.618,.5,0.382,0.236]
    #emas12=[(4,7)]
    xmin_impulsos = [x for x in range(15,40)]
    #xmin_impulsos = [19]
    fecha_fin =  strtime_a_obj_fecha('2022-03-30 00:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    fin_test  =  strtime_a_obj_fecha('2022-04-04 23:30:00')
    #fecha_fin =  strtime_a_obj_fecha('2022-03-14 00:00:00')  #Consiste en la ultima vela (la mas actual, que existe en la simulación)
    #fin_test  =  strtime_a_obj_fecha('2022-03-16 00:00:00')
    txt_test = 'baja_emarl_xvolumen'


    #lista_pares=['XMRUSDT','BTCUSDT','CELRUSDT']
    #lista_pares=[ 'ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']
    lista_pares=['BTCUSDT']
    #lista_pares=['CELRUSDT','ADAUSDT','AVAXUSDT','BNBUSDT','DOTUSDT','XRPUSDT']

    db.backtesting_borrar_todos_los_resultados()

    for par in lista_pares:

        pares=[par]
        m=Mercado_Back_Testing(log,g,db)
        estrategia = Estrategia(par,log,g,m)
        un_minuto = timedelta(minutes=1)
        tres_minutos = timedelta(minutes=3)
        cinco_minutos = timedelta(minutes=5)
        diez_minutos = timedelta(minutes=10)
        una_hora = timedelta(hours=1)
        dos_horas = timedelta(hours=2)
        

        tot= len(escalas) * len (xmin_impulsos) * len(vrsi) * len(coficientes_bajo)
        c=0

        for esc in escalas:
            for xmin_imp in xmin_impulsos:
                for rsi in vrsi:
                    for coef_bajo in coficientes_bajo:
                        c+=1
                        
    
                        comprado=False
                        comp_px = 0
                        comp_stop_loss =0
                        ganancia =0
                        gananciap =0
                        entradas=0
                        ganadas=0
                        perdidas=0
                        cantidad=0.0001
                        gan_min=0
                        
                        m.inicar_mercados(fecha_fin,300,pares,escalas_mercados)
                        while m.fecha_fin < fin_test:
                            txtf = m.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')
                            print(f'-------------------------------------------------{txtf}-------{esc}-{xmin_imp}-{rsi}-{coef_bajo}----{c}--->{round(c/tot*100,2)}')
                            if not comprado:
                                if estrategia.decision_de_compra(esc,coef_bajo,xmin_imp,rsi):
                                    comp_px=estrategia.precio_de_compra()
                                    comp_stop_loss = estrategia.stoploss(estrategia.escala_de_analisis)
                                    comprado = True
                                    gan_min = abs(g.calculo_ganancia_porcentual(comp_px,comp_stop_loss))
                                    log.log ('gogogo-->',txtf,estrategia.escala_de_analisis,estrategia.par)
                                    log.log (f'comp_px {comp_px}, comp_sto_loss {comp_stop_loss}')
                            else:
                                px_vta=estrategia.precio()
                                vendido = False
                                if px_vta < comp_stop_loss:
                                    px_vta = comp_stop_loss
                                    vendido = True

                                gan=g.calculo_ganancia_porcentual(comp_px,px_vta)
                                log.log (f'{txtf} -comprado-> {gan}%  sl {comp_stop_loss} ')    

                                if not vendido and  estrategia.decision_venta(comp_px,gan_min,estrategia.escala_de_analisis):
                                    vendido = True

                                if vendido:
                                    gananciap+=gan
                                    if gan >0:
                                        signo='+'
                                        ganadas+=1
                                    else:
                                        perdidas+=1 
                                        signo='-'   
                                    entradas+=1
                                    log.log (f'----->Termina operacion {signo} gan {gan} entradas {entradas}') 
                                    comprado=False
                                else:
                                    comp_stop_loss = estrategia.stoploss_subir(comp_stop_loss,comp_px)    
                            m.avanzar_tiempo(una_hora)
                            m.actualizar_mercados()  

                        if comprado:   #guardo compra abierta    
                            
                            gananciap+=gan
                            if gan >0:
                                ganadas+=1
                            else:
                                perdidas+=1    
                            entradas+=1
                            log.log (f'----->Termina operacion gan {gan} entradas {entradas}') 
                            comprado=False

                        txt_log_paremtros = f'{txt_test}: escala={esc} coef_bajo {coef_bajo} xmin_impulso{xmin_imp} rsi {rsi}  fechas {fecha_fin}-{fin_test}'
                        txt_log_datos     = f'{par} ganancia= {gananciap} entradas {entradas} ganadas {ganadas} perdidas {perdidas}'  
                        txt_log_fin = txt_log_datos,txt_log_paremtros
                        log.log(txt_log_fin)
                        log_resultados.log (txt_log_fin) 
                        db.backtesting_agregar_resultado(par,txt_log_paremtros,ganadas,perdidas,gananciap)
                    
