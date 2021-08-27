from indicadores2 import Indicadores
from logger import Logger
from variables_globales import VariablesEstado
from funciones_utiles import format_valor_truncando
from numpy import isnan


class Calculador_Precio_Compra:
    def __init__(self,par,g: VariablesEstado,log:Logger,ind_par):
        self.par = par 
        self.ind_par :Indicadores = ind_par
        self.log:Logger = log
        self.g :VariablesEstado = g
        self.escala_de_analisis = '1d'

    def calcular_precio_de_compra(self,metodo,escala):
        ind: Indicadores = self.ind_par
        self.precio = ind.precio_mas_actualizado()
        self.escala_de_analisis = escala
 
        px=0

        self.metodo_compra_venta=metodo
        self.log.log('metodo_compra--->',metodo)

        if metodo=="parte_baja_rango_macd":
            px = self.calc_parte_baja_rango_macd()
            self.calculo_precio_compra = 'parte_baja_rango_macd'

        if metodo=="ret_fibo":
            px,self.calculo_precio_compra = self.calc_retro_fibo()
            if px == 0:
                self.log.log('no puedo calcular por ret_fibo')
                metodo='menor_de_emas_y_cazaliq'

        if metodo=="pefil_volumen":
            px= self.calc_pefil_volumen()
            if px == 0:
                self.log.log('no puedo calcular por pefil_volumen')
                metodo='mayor_de_emas_y_cazaliq'  
            else:
                self.calculo_precio_compra = 'pefil_volumen'          

        # if metodo=="mp_slice_bajo":
        #     px = self.rango[0] #el inferior del rango
        #     if px == 0:
        #         self.log.log('no puedo calcular por mp_slice_scalp')
        #         metodo='cazaliq'
        #     else:
        #         self.calculo_precio_compra=metodo
        #         self.log.log('calc.'+metodo,px)

        # if metodo=="mp_slice_cazaliq":
        #     px, calc = self.calc_mp_slice_cazaliq()
        #     if px <=0:
        #         metodo=="caza_rsi_bajo"
        #     else:
        #         self.calculo_precio_compra=calc    
        
        if metodo=="ema_9":
            px, self.calculo_precio_compra = self.calc_ema(9)
        
        if metodo=="ema_20":
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
        
        elif metodo=="mercado":
            px= ind.precio_mas_actualizado()
            self.calculo_precio_compra='mercado'
            self.log.log('calc.scalping mercado',px) 
     

        elif metodo=="scalping":
            '''
            metodo mas agresivo despues de mercado

            '''
            escala_chica='15m'
            indicador="ema"
            px = ind.ema(escala_chica,55)

            if self.precio<= px:
                indicador="ema_minimos_5,0"
                px = ind.stoploss_ema_minimos(escala_chica,5,0)

            if self.precio <= px:
                indicador="minmax_2"
                mm  = ind.minmax(escala_chica,2)
                px = mm[0] 
            
            if self.precio <= px:
                indicador="precio_de_rsi_20"   
                px = ind.precio_de_rsi(escala_chica,20)   
            
            self.calculo_precio_compra='scalping_'+indicador
            self.log.log('calc.scalping minimo',indicador,escala_chica,px)

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

        elif metodo=="caza_rsi_bajo":  
            px= self.px_de_rsi_mas_bajo(self.escala_de_analisis,self.g.resta_caza_rsi_bajo)
            self.calculo_precio_compra='caza_rsi_bajo'  
            self.log.log('calc.caza_rsi_bajo soporte',px) 
        
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
        

        if px > self.precio:
            px= ind.precio_de_rsi('15m',35)
            self.log.log('calc.cazaliq 15m 35',px) 
            self.calculo_precio_compra='calc.cazaliq 15m 35' 

        if px > self.precio:
            px= ind.precio_de_rsi('15m',29)
            self.log.log('calc.cazaliq 15m 29',px) 
            self.calculo_precio_compra='calc.cazaliq 15m 29'

        if px > self.precio:
            px= ind.precio_de_rsi('15m',19)
            self.log.log('calc.cazaliq 15m 19',px) 
            self.calculo_precio_compra='calc.cazaliq 15m 19'    
        
        if px > self.precio:
            self.log.log('ERRORCALCULO, ind.promedio_de_bajos',px,self.precio)
            px = self.precio / 1.01
            self.calculo_precio_compra='self.precio - self.tickSize'

        if px <=0:
            px=self.precio / 1.25 
            self.log.log('el método de cáculo utilizado no funcionó!! correccion del precio de compra!!!',px) 
        
        self.log.log('precio calculado -->',format_valor_truncando(px,8),'<--')
        
        return px,self.calculo_precio_compra

    
    def calc_pefil_volumen(self):
        vp = self.ind_par.vp(self.escala_de_analisis,24)
        precio_actual = self.ind_par.precio_mas_actualizado()
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