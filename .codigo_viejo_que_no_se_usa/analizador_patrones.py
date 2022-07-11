# # -*- coding: UTF-8 -*-
import time
from par_propiedades import *
from indicadores2 import Indicadores
class Analizador_Patrones:       
    def __init__(self, ind): #ind...>indicadores previamente instanciado y funcionando
        self.ind: Indicadores =ind
        self.propiedades_par=Par_Propiedades(ind.par,ind.client,ind.log)


    def buscar_patron(self):
        ret=self.patron_01()
        if not ret[1]:
           ret=self.patron_02()

        return ret   




    #el precio está subiendo con volumen, se trata de comprar con poc de un minuto
    def patron_01(self):
        patron='2 velas encima ema 1h 30p + volumen'
        comprar=False
        precio_compra=0
        if self.ind.precio_mayor_ultimas_emas('1h',30,2):
            vol=self.ind.volumen_bueno5('1h',0.9)
            if vol['resultado']:
                precio_compra=self.ind.mp_slice('1m',self.propiedades_par.tickSize)[0]
                comprar=True

        return [patron,comprar,precio_compra]

    #el precio en 50 periodos está por encima del preico 200 en una hora
    def patron_02(self):
        patron='ema50 mayor que ema 200 1h'
        comprar=False
        precio_compra=0
        if self.ind.ema_rapida_mayor_lenta('1h',50,200):
            precio_compra=self.ind.mp_slice('1m',self.propiedades_par.tickSize)[0] /1.01
            comprar=True

        return [patron,comprar,precio_compra]    






