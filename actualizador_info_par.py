# # -*- coding: UTF-8 -*-
from indicadores2 import Indicadores
from acceso_db import Acceso_DB
from ordenes_binance import OrdenesExchange
#from funciones_utiles import *
from datetime import datetime,timedelta
from numpy import isnan


class ActualizadorInfoPar:
    
    def __init__(self,db:Acceso_DB, oe,log):
        self.db  : Acceso_DB = db  # Acceso_DB(log,conn.pool)
        self.oe  : OrdenesExchange = oe
        self.oe.prioridad = 0 #hace  se meta al final de la cola
        self.log = log

    def __del__(self):
        del self.db
        del self.oe    
    
    def actualizar_info(self, ind, escala ,moneda,moneda_contra):
        try:
            # datos del par
            p=self.db.get_valores(moneda,moneda_contra)
            #ultimo historico
            ultimo_hist=self.db.ind_historico_ultimo_registro(p['idpar'])


            #determino si hay que actualizar datos
            actualizar= False
            if ultimo_hist['idpar']==-1:
                actualizar= True
            else:
                tiempo_transcurrido = datetime.now().replace(microsecond=0)  - ultimo_hist['fecha']
                if tiempo_transcurrido > timedelta( minutes=10  ):
                    actualizar= True

            if actualizar:
                balance = self.oe.tomar_cantidad(moneda)
                precio   = ind.precio(escala)
                volumen  = ind.volumen_sumado_moneda_contra(escala,8)
                coef_ems = ind.coeficiente_ema_rapida_lenta(escala,15,50)
                if isnan(coef_ems):
                    coef_ems = -111
                #guardo ultimo dateo en pares
                self.log.log("par_persistir_datos_estadisticos", moneda,moneda_contra,balance,volumen,precio,coef_ems)
                self.db.par_persistir_datos_estadisticos(moneda,moneda_contra,balance,volumen,precio,coef_ems)
                # datos históricos
                # por ahora tengo un solo indice histórico que guardar... id=1
                self.db.ind_historico_insert(p['idpar'],1,coef_ems)
        except Exception as e:
              self.log.log("---ERROR---ActualizadorInfoPar.actualizar_info", escala ,moneda,moneda_contra,str(e)) 