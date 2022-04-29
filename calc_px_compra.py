from curses import BUTTON_CTRL
from indicadores2 import Indicadores
from libro_ordenes2 import Libro_Ordenes_DF
from logger import Logger
from mercado import Mercado
from variables_globales import Global_State
from funciones_utiles import format_valor_truncando
from numpy import isnan


class Calculador_Precio_Compra:
    def __init__(self,par,g: Global_State,log:Logger,mercado:Mercado,libro:Libro_Ordenes_DF=None):
        self.par = par 
        self.ind_par :Indicadores = Indicadores(par,log,g,mercado)
        self.ind_btc :Indicadores = Indicadores('BTCUSDT',log,g,mercado)
        self.log:Logger = log
        self.g :Global_State = g
        self.escala_de_analisis = '1d'
        self.libro: Libro_Ordenes_DF = libro
        self.calculo_precio_compra='indefinido'

    def calcular_precio_de_compra(self,metodo,escala,compras_recientes=99):
        ind: Indicadores = self.ind_par
        self.precio = ind.precio(escala)
        self.escala_de_analisis = escala
 
        px=0

        self.metodo_compra_venta=metodo
        self.log.log('metodo_compra--->',metodo)


        if metodo=="libro_grupo_mayor":
            self.libro.actualizar()
            if self.ind_par.ema_rapida_mayor_lenta2('4h',9,21,.1):
                metodo == 'market'
            else:    
                px = self.libro.precio_compra1
            
            self.calculo_precio_compra='libro_grupo_mayor'
            self.log.log('calc.libro_grupo_mayor',px)
            #self.log.log(self.libro.dump_libro())

        if metodo=="mercado":
            px= ind.precio(escala)
            self.calculo_precio_compra='mercado'
            self.log.log('calc. mercado',px) 

        if metodo=="market":
            px= ind.precio(escala)
            self.calculo_precio_compra='market'
            self.log.log('calc.market',px)

        if metodo=="minimo_del_rango_rsi_bajo":
            self.calculo_precio_compra='minimo_del_rango_rsi_bajo' 
            precio_actual = ind.precio(escala)
            
            p_bajo = self.porcentaje_bajo(compras_recientes)     

            px=precio_actual
            px_min,pos_minimo,px_max,pos_maximo = ind.minimo_maximo_y_posicion(escala,50)
            self.log.log(f'{px} px_min {px_min} pos_minimo {pos_minimo} px_max {px_max} pos_maximo {pos_maximo} ')
            if not px_min is None and pos_minimo < pos_maximo  :        #el el minimo esta ubicado primero que el maximo
                px = px_min + (px_max - px_min) * p_bajo
                self.calculo_precio_compra=f'calc. px_min + (px_max - px_min) * {p_bajo}'
                self.log.log(f'calc. px_min + (px_max - px_min) * {p_bajo} ')
            
            if px >= precio_actual:
                self.calculo_precio_compra='precio_de_rsi_mas_bajo(escala,29)'
                px =  ind.precio_de_rsi_mas_bajo(escala,29)
                self.log.log('px - ind.recorrido_maximo',px)

            if px >= precio_actual:
                self.calculo_precio_compra='px - recorrido_maximo'
                px =  self.precio - ind.recorrido_maximo(self.escala_de_analisis,75)      #ind.precio_de_rsi_mas_bajo(escala,26)
                self.log.log('px - recorrido_maximo',px)    

        elif metodo=="scalping":
            px,_ =self.ind_par.minimo_maximo_por_rango_velas_imporantes(escala,100)
            self.calculo_precio_compra='scalping_pxminimo'
            if px > self.ind_par.precio(escala):
                self.libro.actualizar()
                px = self.libro.precio_compra2
                self.calculo_precio_compra='scalping_min_libro_grp_mayor'
            
            self.log.log(f'calc.{self.calculo_precio_compra}',px)
           
        elif metodo=="parte_baja_rango_macd":
            px = self.calc_parte_baja_rango_macd()
            self.calculo_precio_compra = 'parte_baja_rango_macd'

        elif metodo=="ret_fibo":
            px,self.calculo_precio_compra = self.calc_retro_fibo()
            if px == 0:
                self.log.log('no puedo calcular por ret_fibo')
                metodo='menor_de_emas_y_cazaliq'

        elif metodo=="pefil_volumen":
            px= self.calc_pefil_volumen()
            if px == 0:
                self.log.log('no puedo calcular por pefil_volumen')
                metodo='mayor_de_emas_y_cazaliq'  
            else:
                self.calculo_precio_compra = 'pefil_volumen'          

        elif metodo=="ema_9":
            px, self.calculo_precio_compra = self.calc_ema(9)
        
        elif metodo=="ema_20":
            px, self.calculo_precio_compra = self.calc_ema(20)

        elif metodo=="ema_55":
            px, self.calculo_precio_compra = self.calc_ema(55)
        
        elif metodo=="mecha_bajo_ema_20":
            px, self.calculo_precio_compra = self.calc_mecha_bajo_ema(20) 

        elif metodo=="mecha_bajo_ema_55":
            px, self.calculo_precio_compra = self.calc_mecha_bajo_ema(55) 

        elif metodo=="ema_menor":
            px, self.calculo_precio_compra = self.calc_ema_menor()
            self.log.log('calc.ema_menor',px)

        elif metodo=="menor_de_emas_y_cazaliq":    

            px, self.calculo_precio_compra = self.calc_menor_de_emas_y_cazaliq()   

        elif metodo=="mayor_de_emas_y_cazaliq":    

            px, self.calculo_precio_compra = self.calc_mayor_de_emas_y_cazaliq()
        
        

        

        elif metodo=="ema_minimos_1":
            px=ind.stoploss_ema_minimos(self.escala_de_analisis,1,0)
            self.calculo_precio_compra='ema_minimos_1'
        
        elif metodo=="ema_minimos_3":
            px=ind.stoploss_ema_minimos(self.escala_de_analisis,3,0)
            self.calculo_precio_compra='ema_minimos_3' 
        
        elif metodo=="ema_55_min_3":
            #si el precio está por debajo de la ema_55 toma una ema de minismo_3
            px=ind.ema(self.escala_de_analisis,55)
            if self.precio <= px:
                px = ind.stoploss_ema_minimos(self.escala_de_analisis,3,0)
            
            self.calculo_precio_compra='ema_55_min_3'
  

        
        elif metodo=="mejor_de_4":
            mm=ind.minmax(self.escala_de_analisis,15)
            pxm= mm[0] #el minimo de las ultimas 24 horas
            pxr= self.px_de_rsi_mas_bajo(self.escala_de_analisis,20)
            em1=ind.stoploss_ema_minimos(self.escala_de_analisis,5,0)
            em2=ind.ema(self.escala_de_analisis,55)

            px = self.encontrar_justo_el_menor(self.precio, [pxm,pxr,em1,em2]  )

            self.calculo_precio_compra='mejor_de_4'
            self.log.log('calc.dinamico mejor_de_4')

       
        elif metodo=="cazaliq": 
            px= self.px_de_rsi_mas_bajo(self.escala_de_analisis,15)

            self.calculo_precio_compra='cazliq'  
            self.log.log('calc.cazaliq soporte',px)  

        #correcion por las dudas, 
        #hay calculos que no estan funcionando bien o 
        #se basan en indicadores que se actualizan incorrectamente? 
        #o en el precio del libro que se actualiza incorractamente?
        #investigando... mientras tanto 
        #si todo sale mal compramos a precio-ticksize
        

        #px= self.restar_cuando_son_malas_condiciones(self.escala_de_analisis,px)

        precio = ind.precio(escala)
        if px > precio:
            self.log.log('ERRORCALCULO, ind.promedio_de_bajos',px,precio)
            px = self.precio / 1.01
            self.calculo_precio_compra='self.precio / 1.01'

        if px <=0:
            px=self.precio / 1.25 
            self.log.log('el método de cáculo utilizado no funcionó!! correccion del precio de compra!!!',px) 
        
        self.log.log('precio calculado -->',format_valor_truncando(px,8),'<--')
        
        return px,self.calculo_precio_compra

    def porcentaje_bajo(self,cant_compras):

        if self.btc_sube_y_no_habria_peligro_de_caer():    
            lista_porcentajes=[0.47,0.35,0.20]
        else:    
            lista_porcentajes=[0.20,0.10,0.05]    

        i = cant_compras
        max_i = len(lista_porcentajes) -1 
        if i >  max_i :
            i = max_i
        return lista_porcentajes[i]    

    def btc_sube_y_no_habria_peligro_de_caer(self):
        ret = False

        rsi = self.ind_btc.rsi('1d')
        self.log.log(f'rsi_btc 1d {rsi}')
        if rsi < 70:
            emas_btc_ok, diferencia_porcentual,pend_r,pend_l=self.ind_btc.ema_rapida_mayor_lenta2('1d',10,21,0.5,True)
            self.log.log(f'emas_btc_ok {emas_btc_ok} ,diferencia_porcentual {diferencia_porcentual},pend_r {pend_r},pend_l {pend_l}')
            ret = emas_btc_ok
       
        return ret


    def calc_pefil_volumen(self):
        vp = self.ind_par.vp(self.escala_de_analisis,24)
        precio_actual = self.ind_par.precio(self.escala_de_analisis)
        close =vp.sort_values(by ='total_volume' ,ascending=False)  # precios ordenados por volumen en orden inverso, lo de mas volumenprimero
        px = 0
        
        for p in close["mean_close"]:
            if p < precio_actual:
                px = p
                break
        return px

    def calc_retro_fibo(self):
        ind: Indicadores = self.ind_par
        ifib = 3 # 50%
 
        #obtengo los pxs del retroceso fibo 
        pxf = ind.retrocesos_fibo_macd_ema(self.escala_de_analisis,ifib)
        px=0
        if pxf[0] > 0:
            for p in pxf:
                if p < self.precio:
                    px = p
                    break

        # también calculo los retorcesos convergentes 
        pxfc = ind.retrocesos_convergentes_fibo_macd(self.escala_de_analisis)

        if px >0:
            px = min(px,pxfc)
        else:
            px =  pxfc   

        return px,'ret_fibo_'+str(self.g.ret_fibo[ifib])

    def calc_ema(self,periodos):
        ind: Indicadores = self.ind_par
        px  = ind.ema(self.escala_de_analisis,periodos)
        if isnan(px): 
            px = 0

        calculo_precio_compra='ema_'+str(periodos)   
        self.log.log('calc.ema_'+str(periodos),px)
        return px,calculo_precio_compra

    def calc_mecha_bajo_ema(self,periodos):   
        ind: Indicadores = self.ind_par
        px  = ind.ema(self.escala_de_analisis,periodos)
        periodos1 = periodos * 2
        px1 = ind.ema(self.escala_de_analisis,periodos1)
        if isnan(px):  
            px = 0
        if isnan(px1):  
            px1 = 0
        if px > px1 and px>0 and px1>0: #busco un precio de compra entre las dos emas    
            px = px - (px-px1)/2
        else:
            px = px / 1.1    

        calculo_precio_compra='mecha_bajo_ema_'+str(periodos)   
        self.log.log('calc.mecha_bajo_ema_'+str(periodos),px)
        return px,calculo_precio_compra


    def calc_ema_menor(self):
        emas={}
        px,metodo = self.calc_ema(20)
        emas[metodo] = px
        px,metodo = self.calc_ema(55)
        emas[metodo] = px

        menor=min(emas, key=emas.get) #obtiene la key del menor valor

        return emas[menor],menor

    def calc_menor_de_emas_y_cazaliq(self):
        dpx={}
        px,metodo = self.calc_ema(20)
        dpx[metodo] = px
        
        px,metodo = self.calc_ema(55)
        dpx[metodo] = px
        
        # px,metodo = self.calc_mp_slice_cazaliq()
        # dpx[metodo] = px
        
        menor=min(dpx, key=dpx.get) #obtiene la key del menor valor

        return dpx[menor],menor

        #Best: min(d, key=d.get) -- no reason to interpose a useless lambda indirection layer or extract items or keys!
    
    def calc_parte_baja_rango_macd(self): 
        '''
        precio promedio de los mas bajos de la loma macd actual
        '''
        ind: Indicadores =self.ind_par
        px = ind.promedio_bajos_macd(self.escala_de_analisis) 
        self.log.log('calc_parte_baja_rango_macd',self.escala_de_analisis,px)
        return px

    def calc_mayor_de_emas_y_cazaliq(self):
        dpx={}
        px,metodo = self.calc_ema(20)
        if px < self.precio:
            dpx[metodo] = px
        
        px,metodo = self.calc_ema(55)
        if px < self.precio:
            dpx[metodo] = px
        
        # 29/1/2020  cazaliq arriba se rompe fácil y subrimos, la quitamos y compramos solo por las emas 
        #px,metodo = self.calc_mp_slice_cazaliq()
        #if px < self.precio:
        #    dpx[metodo] = px
        
        dpx['px/1.25'] = self.precio /1.25 # agrego este precio para asegurar un valor en el diccionario siempre


        mayor=max(dpx, key=dpx.get) #obtiene la key del menor valor

        return dpx[mayor],mayor

        #Best: min(d, key=d.get) -- no reason to interpose a useless lambda indirection layer or extract items or keys!
    
    def px_de_rsi_mas_bajo(self,escala,rsi_restar):
        ind =self.ind_par

        rsi   = ind.rsi(escala,vela=1) #penultima vela
        rsi_bajo = rsi - rsi_restar

        if rsi_bajo < 0:
            rsi_bajo =  1

        px  = ind.precio_de_rsi(escala,rsi_bajo) 
        return px    

    def encontrar_justo_el_menor(self,valor, lista):
        lista.sort(reverse=True)
        ret = valor
        for v in lista:
            if v < valor:
                ret=v
                break
        return ret