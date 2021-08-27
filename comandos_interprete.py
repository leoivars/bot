# # -*- coding: UTF-8 -*-
from acceso_db import Acceso_DB
from datetime import datetime,timedelta
from funciones_utiles import calcular_fecha_futura
import time



class ComandosPar:       

    def __init__(self,log,conn,par): #ind...>indicadores previamente instanciado y funcionando
        self.db= Acceso_DB(log,conn.pool)
        self.par=par
        self.log=log
        self.ultima_interpretacion=time.time() - 10

    def __del__(self):
        del self.db    
        del self.log
        del self.par
    
    def interpretar(self):
        # restriccion de una ejecucion cada 10 segundos
        
        ejecutado = False

        ahora=time.time()
        if ahora - self.ultima_interpretacion < 30:
            return ejecutado# no hago nada 
        else:
            self.ultima_interpretacion=time.time()

        try:
            #self.log.log('comando interpretar...')
            #obtengo lista de comando para le par
            comandos=self.db.comando_get_lista(self.par.idpar)
            #interpreto y ejecuto
            for cmd in comandos:
                self.log.log('COMANDO-->',cmd)
                tiempo_transcurrido = datetime.now().replace(microsecond=0)  - cmd['fecha']
                if tiempo_transcurrido < timedelta( minutes= 10  ):
                    parametros=cmd['parametros'].split()
                    if cmd['comando']=='tomar_ganancias':
                        self.tomar_ganancias(cmd['idcomando'],parametros)
                    if cmd['comando']=='estado_siguiente':
                        self.estado_siguiente(cmd['idcomando'])    
                    if cmd['comando']=='deshabilitar':
                        self.deshabilitar(cmd['idcomando'],parametros) 
                    if cmd['comando']=='reiniciar_estado':
                        self.reiniciar_estado(cmd['idcomando'],parametros)   
                    if cmd['comando']=='stop_loss_subir':
                        self.stop_loss_subir(cmd['idcomando'],parametros) 
                    if cmd['comando']=='stop_loss_iniciar':
                        self.stop_loss_iniciar(cmd['idcomando'],parametros)       
                    if cmd['comando']=='vender':
                        self.vender(cmd['idcomando'],parametros)
                    else:           
                        self.db.comando_respuesta(cmd['idcomando'],'? comando desconocido')    
                else:     
                    self.db.comando_respuesta(cmd['idcomando'],'no se ejecuta por ser viejo')     
        
        except  Exception as e:
            comandos=[]
            self.log.log('ERROR en ComandosPar.interpretar()',str(e))    
    
    
        if  len(comandos) >0:
            ejecutado = True

        return ejecutado          

    def vender(self,idcomando,parametros):
        self.log.log('COMANDO-->Vender') 
        self.log.log('iniciando el estado 4')  
        self.par.vender_solo_en_positivo=0#vende sin importar si hay pérdidas o no
        self.par.iniciar_estado(self.par.iniciar_estado(4)) #estado 4 vender 
        self.par.tiempo_reposo=1
        self.db.comando_respuesta(idcomando,'listo')


    def stop_loss_subir(self,idcomando,parametros=''):
        self.log.log('COMANDO-->stop_loss_subir',parametros)  
        
        if self.par.stoploss_habilitado==0:
            self.par.iniciar_stoploss()
            respuesta='stop loss iniciado'
        else:
            if len(parametros) > 0:
                ticks=int(parametros[0])
            else:
                ticks=0

            if ticks > 0: 
                respuesta = self.par.subir_stoploss(ticks,forzado=True)    
            else:
                respuesta ='ticks=0 no se sube sl'    

        self.log.log('RESPUESTA COMANDO-->',respuesta)  
        self.db.comando_respuesta(idcomando,respuesta)    

    def stop_loss_iniciar(self,idcomando,parametros=''):
        '''
        inicia un stoploss, en cualquer caso
        En al caso de ser negativo el stoploss habilita la posibilidad
        '''
        self.log.log('COMANDO-->stop_loss_iniciar',parametros)  
        
        self.par.stoploss_negativo = 1 # habilita la posibilidad de tener un stoploss negativo
        respuesta='?'

        if self.par.stoploss_habilitado==0:
            self.par.iniciar_stoploss()
            respuesta='stop loss iniciado'
        
        self.log.log('RESPUESTA COMANDO-->',respuesta)  
        self.db.comando_respuesta(idcomando,respuesta)      


    def reiniciar_estado(self,idcomando,parametros):
        self.log.log('COMANDO-->reiniciar_estado') 
        self.log.log('actualmente reinica la funciona, va la primer estado de la funcion')  
        self.par.iniciar_estado(self.par.primer_estado_de_funcion()) #reinicia el estado 
        self.par.tiempo_reposo=1
        self.db.comando_respuesta(idcomando,'listo')

    def deshabilitar(self,idcomando,parametros):
        try:
            tiempo=int(parametros[0])
        except:
            tiempo=1 
        self.log.log('COMANDO-->deshabilitar',tiempo)  
 
        self.db.set_no_habilitar_hasta(calcular_fecha_futura(tiempo),self.par.moneda,self.par.moneda_contra)
        self.par.tiempo_reposo=1
 
        self.db.comando_respuesta(idcomando,'listo')
            


    def estado_siguiente(self,idcomando):
        siguiente=self.par.estado_siguiente()
        self.log.log('COMANDO-->estado_siguiente inicio')
        self.par.iniciar_estado(siguiente)
        #self.par.reset = True
        self.db.comando_respuesta(idcomando,'estado-> '+str(siguiente)) 
        self.log.log('COMANDO-->estado_siguiente fin')

    def tomar_ganancias(self,idcomando,parametros):
        try:
            pganancias=float(parametros[0])
        except:
            pganancias=0   

        if pganancias==0:
            respuesta='pganancia=0, no hago nada'
        else:
            ganancias=self.par.ganancias()
            if 0 < ganancias <= pganancias:
                respuesta ='No se puede tomar ganancia' + str(ganancias)
                self.log.log(respuesta)
                #self.par.cambiar_funcion('vender+ya')  ### esto me estaba colgando el par... 
            else:
                px_stoploss=self.par.calc_precio(pganancias)
                self.par.cancelar_ultima_orden()
                respuesta=self.par.ajustar_stoploss( px_stoploss )
                if respuesta =='OK':
                    self.par.stoploss_habilitado=1
                    self.par.seguir_soniando = False
                    self.par.tiempo_inicio_stoploss = time.time()
                else:
                    self.par.stoploss_habilitado=0
        
        self.db.comando_respuesta(idcomando,respuesta)                








# class Comandos:

#     #esto no está terminado
#     def validar_par(self,parametros):
#         ret={} 
#         ret['idpar']=-1
#         error='MONEDA_ERRONEA'        
        
#         try:
#             moneda = parametros[0]
#         except:
#             moneda = error
        
#         try:
#             moneda_contra = parametros[1]
#         except:
#             moneda_contra = error  
        
#         ret['moneda'] = moneda
#         ret['moneda_contra'] = moneda_contra

#         if moneda != error and moneda_contra != error:
#             dpar=self.db.get_valores(moneda,moneda)
#             if dpar['idpar']!=-1:
#                 pass
#       #          ret=['idpar']=dpar['idpar']

#        # return ret







    
