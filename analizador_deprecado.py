# # -*- coding: UTF-8 -*-
from analizador_riesgo_beneficio import Analizador_Riesgo_Beneficio
from analizador_patrones import Analizador_Patrones
from analizador_retroceso_fibo import Analizador_Retroceso_Fibonacci
from analizador_emas import Analizador_Emas
from analizador_market_profile import Analizador_Market_Profile
from analizador_minmax import Analizador_MinMax
from analizador_prom_alto_bajo import Analizador_Altos_Bajos
from par_propiedades import Par_Propiedades
class Analizador:       

    def __init__(self, ind): #ind...>indicadores previamente instanciado y funcionando
        self.ind = ind
        self.emas = Analizador_Emas(ind)
        self.patrones = Analizador_Patrones(ind)
        self.propiedades_par=Par_Propiedades(ind.par,ind.client,ind.log)
        
        self.riesgo_beneficio= Analizador_Riesgo_Beneficio(ind,self.propiedades_par)
        self.fibo=Analizador_Retroceso_Fibonacci(ind,self.propiedades_par)
        self.mkt=Analizador_Market_Profile(ind,self.propiedades_par)
        self.minmax=Analizador_MinMax(ind,self.propiedades_par)
        self.altobajo=Analizador_Altos_Bajos(ind,self.propiedades_par)

    #def actualizar_pocs    

    def tiene_fuerza(self,escala):
        # 0510 23:25 BTC:   precio......= 6496.04
        # 0510 23:25 BTC:15m ...........= Subiendo
        # 0510 23:25 BTC:15m adx.0.7.14.= [19.07, 1.69, 0.91, 0.11]
        # 0510 23:25 BTC:15m rsi........= 69.54
        # 0510 23:25 BTC:15m Vol........= 3.41 1.66
        # 0510 23:25 BTC:4h.............= Subiendo
        
        # 0510 23:25 BTC:4h   rsi.......= 77.01
        # 0510 23:25 BTC:4h   Vol.......= 1.04 1.24
        # 0510 23:25 BTC:4h  adx.0.7.14.= [38.35, 1.12, 1.37, 1.22] <-----1.12  creciendo!
        #0512 09:29 BTC:4h  adx.0.7.14.= [55.57, 0.44, 1.44, 1.63]  <----- 0.44 se está aplanando
         
        adx=self.ind.adx(escala)
        if adx[0]>=23 and abs(adx[0])>0.3 and abs(adx[2])>0.3 and abs(adx[2])>0.3 \
            and self.son_del_mismo_signo(adx[1],adx[2]) and self.son_del_mismo_signo(adx[2],adx[3]):
            return True
        else: 
            return False    


    def fuezas_x_escalas(self,escalas):
        ret={}
        for escala in escalas.split():
            if self.tiene_fuerza(escala):
                ret[escala]=1
            else:
                ret[escala]=0

        return ret     


    def esta_tomando_fuerza(self,escala):
        # 0510 23:25 BTC:   precio......= 6496.04
        # 0510 23:25 BTC:15m ...........= Subiendo
        # 0510 23:25 BTC:15m adx.0.7.14.= [19.07, 1.69, 0.91, 0.11]
        # 0510 23:25 BTC:15m rsi........= 69.54
        # 0510 23:25 BTC:15m Vol........= 3.41 1.66
        # 0510 23:25 BTC:4h.............= Subiendo
        
        # 0510 23:25 BTC:4h   rsi.......= 77.01
        # 0510 23:25 BTC:4h   Vol.......= 1.04 1.24
        # 0510 23:25 BTC:4h  adx.0.7.14.= [38.35, 1.12, 1.37, 1.22] <-----1.12  creciendo!
        #0512 09:29 BTC:4h  adx.0.7.14.= [55.57, 0.44, 1.44, 1.63]  <----- 0.44 se está aplanando

        
        adx=self.ind.adx(escala)
        if abs(adx[1])>0.3 and abs(adx[2])>0.1 and abs(adx[3])>0.1 \
            and self.son_del_mismo_signo(adx[1],adx[2]) and self.son_del_mismo_signo(adx[2],adx[3]) \
            and self.ind.volumen_porcentajes(escala)[5]>1:
            return True
        else: 
            return False    
        
    def tomando_fuerza_en_escalas(self,escalas):
        valores={'resultado': True}
        
        for escala in escalas.split():
            if self.esta_tomando_fuerza(escala):
                valores[escala]=1
            else:
                valores[escala]=0
                valores['resultado']=False
                break

        return valores    
       

    #Retoran Verdadero cuando hay fuerza en todas las escalas proporcionadas
    def tiene_fuerza_en(self,escalas):
        ret=True
        for escala in escalas.split():
            if not self.tiene_fuerza(escala):
                ret=False
                break
        return ret 



    def subiendo_sin_fuerza(self):    
        
        ema55=self.ind.ema('15m',55)
        ema9 =self.ind.ema('15m',9)
        adx  =self.ind.adx('15m')
        #self.log.log('Control BTC 15m  Ema9,Ema55',ema9,ema55)
        if ema9>ema55 and adx[0]<23:
            return True
            #self.log.log("BTC-------> Ema9,Ema55,adx OK!",ema9,ema55,adx[0])    
        else:
            #self.log.log("BTC-------> Ema9,Ema55,adx NO PASA!",ema9,ema55,adx[0])
            return False


    def son_del_mismo_signo(self,a,b):
        if a*b >0:
            return True
        else:
            return False    

    # devuelve True en caso de NO tener fuerza alcista
    def no_tiene_fuerza_alcista(self):
        adx=self.ind.adx('1h')
        ret=True
        print ('adx0',adx[0])
        if adx[0]>=23 or (adx[1]>0.01 and adx[2]>0.01 and adx[3]>0.01):
            macd=self.ind.macd_analisis('1h',72)
            emas_ok=self.ind.ema_rapida_mayor_lenta('1h',8,32)
            print ('macd','emas',macd,emas_ok)
            if macd[0]==1 or emas_ok: 
                ret=False

        return ret        

    # devuelve True cuando NO es buen momento para alts.
    def no_es_buen_momento_para_alts(self):
        mfi=self.ind.mfi('15m')
        ret=True
        print ('mfi',mfi)
        if mfi<70 and mfi>30: 
            #macd=self.ind.macd_analisis('15m',72)
            #emas_ok=self.ind.ema_rapida_mayor_lenta('15m',8,32)
            #print ('macd','emas',macd,emas_ok)
            #if macd[0]==1 or emas_ok: 
            ret=False

        return ret 

        




            


    