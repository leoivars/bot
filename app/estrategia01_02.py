#from abc import ABC,abstractmethod
from asyncore import loop
from datetime import timedelta
import time
from fpar.rango import Rango

from funciones_utiles import strtime_a_obj_fecha
from mercado_back_testing import Mercado_Back_Testing

from variables_globales import Global_State
from logger import Logger
from indicadores2 import Indicadores
from calc_px_compra import Calculador_Precio_Compra
from binance.client import Client #para el cliente
from fpar.filtros import Filtros
from fpar.ganancias import calculo_ganancias,precio_de_venta_minimo



class Estrategia():
    ''' la idea de esta clase es de ser la base de cualquier estrategia 
    que se quiera implementar
    '''
    
    def __init__(self,par,log,estado_general, mercado):
        self.nombre='parte_baja_ema_rsi'
        self.file = __file__
        self.log: Logger = log
        self.g: Global_State = estado_general
        self.mercado = mercado
        self.par = par
        self.ind = Indicadores(self.par,self.log,self.g,self.mercado)
        self.escala_de_analisis ='?'
        self.calculador_px_compra = Calculador_Precio_Compra(self.par,self.g,log,self.ind)
        self.filtro = Filtros(self.ind,self.log)
        self.recompra=True
        self.rango7v=Rango(self.ind,log,7)
        #print('--precio_mas_actualizado--->',self.ind.precio_mas_actualizado()  )

    def decision_de_compra(self,escala):
        ''' Hace evaluación del mercado y retorna True en caso 
            de ser momento de comprar, caso contrario False
        '''
        ret = False
        if self.filtro.rango_de_compra(escala,-1,0.45):
            if self.filtro.pendiente_positiva_ema(escala,9):
                if self.filtro.pendiente_positiva_sma_rsi(escala):
                    ret = True
        return ret    

    def decision_venta(self,escala,pxcompra):
        ind: Indicadores =self.ind

        #no decido vender si no estoy al menos en ganancia minima
        gan =   calculo_ganancias(self.g,pxcompra,ind.precio(escala))   
        gan_min = self.g.ganancia_minima[escala]
        if gan < gan_min:
            return False
        
        #no vendo si  el precio no es bajista y no he superado la ganancia minima multiplicada 
        precio_bajista = ind.el_precio_es_bajista(escala)
        if not precio_bajista:
            return False

        if self.filtro.rango_de_compra(escala,minimo_compra=0.9,maximo_compra=10):
            if self.filtro.pendiente_negativa_ema(escala,9,0):
                if self.filtro.pendiente_negativa_sma_rsi(escala):
                    return True
        
        return False

    def tipo_orden_compra(self):
        return 'market'

    def precio_de_compra(self,escala):
        return self.precio(escala)

    def precio(self,escala=None):
        if escala:
            return self.ind.precio(escala)
        else:    
            return self.ind.precio_mas_actualizado()

    def decision_recompra(self,escala,precio_compra):
        ''' He comprado y el precio ha bajado. Si es suficientemente bajo, tomo la desición de hacer otra compra.
            No tengo claro si esta desición es parte de la estrategia o la manejo por fuera.
            ¿La decisión de compra es un stoploss fracasado?
        '''
        gan_limite = self.g.escala_ganancia[escala] * -3
        precio = self.precio(escala)
        gan = self.g.calculo_ganancia_porcentual(precio_compra,precio)
        
        ret = False
        if gan < gan_limite:
            ret = True
            # vimpulso = self.ind.velas_de_impulso(escala,-1,-5)
            # self.log.log(f'impulsos {vimpulso}')
            # if not vimpulso:
            #     if self.filtro.pendiente_positiva_ema(escala,9):
            #         if self.filtro.pendiente_positiva_sma_rsi(escala):
            #             ret = True

        return ret    

    def stoploss(self,escala):
        precio = self.precio(escala)
        if self.filtro.pendiente_positiva_ema(escala,21):
            sl = precio - self.ind.recorrido_maximo(escala,30)
        else:
            sl = precio - self.ind.recorrido_maximo(escala,60)  
        
        return sl

    def stoploss_subir(self,escala,sl_actual,pxcompra):
        #minimo = self.ind.minimo(self.escala_de_analisis,cvelas=3)  
        #px_salir_derecho = precio_de_venta_minimo(self.g,0.1,pxcompra)
        precio = self.precio(escala)
        sl = 0
        if precio > sl_actual :
            if self.filtro.precio_en_rango(escala,0.8,10):
                sl = precio - self.ind.recorrido_maximo(escala,20)  
            else:    
                sl = precio - self.ind.recorrido_maximo(escala,40)  #px_salir_derecho + (  (precio - px_salir_derecho) /2 )

        if sl > sl_actual:
            self.log.log(f'subir_sl {sl_actual} --> {sl}')
        else:    
            sl = sl_actual    

        return sl    
