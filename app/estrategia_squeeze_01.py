from fauto_compra_vende.habilitar_pares import precio_cerca
from mercado_back_testing import Mercado_Back_Testing

from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from fpar.filtros import Filtros
from fpar.ganancias import calculo_ganancias

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
        if self.filtro.rango_de_compra(self.escala_rapida,-1,0.45):
            if self.filtro.hay_velas_de_impulso_con_fin(self.escala_rapida,-1,21,3,2):
                if self.filtro.rsi_minimo_cercano(self.escala_rapida,35,(2,14),55):
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
        return 'market'

    def precio_de_compra(self):
        return self.precio()

    def precio(self):
        return self.ind.precio(self.escala_rapida)

    def decision_recompra(self,precio_compra):
        ''' He comprado y el precio ha bajado. Si es suficientemente bajo, tomo la desición de hacer otra compra.
            No tengo claro si esta desición es parte de la estrategia o la manejo por fuera.
            ¿La decisión de compra es un stoploss fracasado?
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
        if gan >0:
            sl = precio -  self.ind.recorrido_maximo(self.escala_rapida,7 )
        else:    
            sl =0 # precio - (precio-precio) - self.ind.recorrido_maximo(self.escala_rapida,7 )
        
        return sl
    def stoploss_subir(self,sl_actual):
        precio = self.precio()
        sl = 0
        if self.filtro.rango_de_compra(self.escala_rapida,0.9,50):
            sl = self.ind.minimo(self.escala_rapida,3) - self.ind.recorrido_minimo(self.escala_rapida,30)   #precio - self.ind.recorrido_promedio(self.escala_rapida,3)
        elif self.ind.rsi(self.escala_rapida) > 70:
            sl = self.ind.minimo(self.escala_rapida,10) - self.ind.recorrido_minimo(self.escala_rapida,20)  #precio - self.ind.recorrido_minimo(self.escala_rapida,10)
        else:    
            sl = self.ind.minimo(self.escala_rapida,20) - self.ind.recorrido_minimo(self.escala_rapida,10)  #precio - self.ind.recorrido_maximo(self.escala_rapida,14)  
        if sl > sl_actual:
            self.log.log(f'subir_sl {sl_actual} --> {sl}')
        else:    
            sl = sl_actual    

        return sl  
 
    def __gan_limite__(self):
        return -0.5
        #gan_limite = self.g.escala_ganancia[self.escala_rapida] * -4
        #return gan_limite
    