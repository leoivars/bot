from mercado_back_testing import Mercado_Back_Testing
from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from fpar.filtros import Filtros
from fpar.ganancias import calculo_ganancias, precio_de_venta_minimo


class Estrategia():
    ''' Conservadora, se clava poco. No estudiada muy bien n periodos alcistas.
    '''
    
    def __init__(self,par,log,estado_general, mercado,escala_rapida):
        self.nombre="squeeze"
        self.file = __file__
        self.log: Logger = log
        self.g: Global_State = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        self.escala_de_analisis ='?'
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        self.filtro = Filtros(self.ind,self.log)
        self.escala_rapida = escala_rapida
        #print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def set_escala(self,escala):
        self.escala_rapida = escala

    def decision_de_compra(self):
        ''' Hace evaluación del mercado y retorna True en caso 
            de ser momento de comprar, caso contrario False
        '''
        
        if self.filtro.pendiente_positiva_ema(self.escala_rapida,55):
            if self.filtro.rsi_maximo(self.escala_rapida,57):
                return True
        else:
            if self.filtro.rsi_maximo(self.escala_rapida,45):                             # para no entrar en un momento sobrecalentado
                if self.filtro.rango_de_compra(self.escala_rapida,-20,0.5):                # para no comprar en la parte alta
                    if self.filtro.squeeze_negativo_sqz_off(self.escala_rapida):  # para agarrar 
                        return True
    
        return False

    def decision_venta(self,pxcompra):
        ind: Indicadores =self.ind

        #no decido vender si no estoy al menos en ganancia minima
        gan =   calculo_ganancias(self.g,pxcompra,ind.precio(self.escala_rapida))   
        #gan_min = self.g.ganancia_minima[self.escala_rapida]
        if gan < 0.1:
            return False
        
        if self.ind.rsi(self.escala_rapida) > 90:
            if self.filtro.pendiente_negativa_sma_rsi(self.escala_rapida):
                return True
    
        return False

    def tipo_orden_compra(self):
        return 'limit'

    def precio_de_compra(self):
        px = self.ind.precio(self.escala_rapida)
        pxc = 0
        if self.filtro.pendiente_positiva_ema(self.escala_rapida,55):
            px_ema=self.ind.ema(self.escala_rapida,55)
            if px > px_ema:
                pxc = px_ema

        if pxc ==0:
            vp_min,vp_med,vp_max = self.filtro.vp.min_med_max(self.escala_rapida)
            pxc = vp_min #+(vp_med-vp_min) *.1
            if pxc > px:
                pxc = px

        self.log.log(f'precio_de_compra {pxc}')
        return pxc    

    def precio(self):
        return self.ind.precio(self.escala_rapida)

    def decision_recompra(self,precio_compra):
        ''' He comprado y el precio ha bajado. Si es suficientemente bajo, tomo la desición de hacer otra compra.
            No tengo claro si esta desición es parte de la estrategia o la manejo por fuera.
            ¿La decision_recompra es un stoploss fracasado? 
        '''
        
        ret = False
        precio = self.precio()
        gan = self.g.calculo_ganancia_porcentual(precio_compra,precio)
               
        if gan < self.__gan_limite__():
            
            if self.ind.la_ultima_vela_es_positiva(self.escala_rapida):
                if self.decision_de_compra():
                    ret = True
            
        return ret 

    def stoploss(self,precio_compra):
        precio = self.precio()
        gan = self.g.calculo_ganancia_porcentual(precio_compra,precio)
        if gan <0:
            return 0
        
        if self.filtro.hay_velas_de_impulso(self.escala_rapida,1,2,7):
            if self.ind.rsi(self.escala_rapida) > 60:
                sl = precio_de_venta_minimo(self.g, gan * 0.7 ,precio_compra)
                self.log.log(f'stoploss_por_pump {sl} ')
                return sl 
                
        px_vta_minimo =  self.ind.minimo(self.escala_rapida,7)
        gan_stoploss = self.g.calculo_ganancia_porcentual(precio_compra,   px_vta_minimo   )
        self.log.log(f'stoploss  gan_stoploss {gan_stoploss}    ')
        if  gan_stoploss>0:
            sl = self.ind.minimo(self.escala_rapida,4)
            self.log.log(f'sl pendiente_positiva_ema {sl}')     
        else:    
            sl =0 # precio - (precio-precio) - self.ind.recorrido_maximo(self.escala_rapida,7 )
        
        return sl

    def stoploss_subir(self,sl_actual):
        precio = self.precio()
        sl = 0
        if self.filtro.histograma_squeeze_positivo_con_pendiente_negativa(self.escala_rapida):    
            sl = self.ind.minimo(self.escala_rapida,5) - self.ind.recorrido_minimo(self.escala_rapida,10)   #precio - self.ind.recorrido_promedio(self.escala_rapida,3)
        elif self.ind.rsi(self.escala_rapida) > 70:
            sl = self.ind.minimo(self.escala_rapida,7) - self.ind.recorrido_minimo(self.escala_rapida,10)  #precio - self.ind.recorrido_minimo(self.escala_rapida,10)
        else:    
            sl = self.ind.minimo(self.escala_rapida,21) - self.ind.recorrido_minimo(self.escala_rapida,10)  #precio - self.ind.recorrido_maximo(self.escala_rapida,14)  
        if sl > sl_actual:
            self.log.log(f'subir_sl {sl_actual} --> {sl}')
        else: 
            sl = sl_actual    

        return sl  
    
 
    def __gan_limite__(self):
        return -0.8
        #gan_limite = self.g.escala_ganancia[self.escala_rapida] * -4
        #return gan_limite
    