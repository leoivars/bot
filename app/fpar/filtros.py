from fpar.volume_profile import Volume_Profile
from indicadores2 import Indicadores
from logger import Logger
from fpar.rango import Rango

class Filtros():
    def __init__(self,ind:Indicadores,log:Logger):
        self.ind:Indicadores = ind
        self.log:Logger = log
        self.rango=Rango(ind,log,200)
        self.vp=Volume_Profile(ind,log,400)

    def parte_baja_rango(self,escala,cvelas,porcentaje_bajo=.382):
        minimo,maximo = self.ind.minimo_maximo(escala,cvelas)
        maximo_compra =  minimo + (maximo - minimo) *  porcentaje_bajo 
        precio = self.ind.precio(escala)
        ret = precio < maximo_compra
        
        return ret 

    def rango_de_compra(self,escala,minimo_compra=.2,maximo_compra=.382):
        minimo,maximo = self.rango.min_max(escala)
        rango = maximo - minimo
        precio = self.ind.precio(escala)
        pos_rango =round( (precio - minimo) / rango ,3)
        ret = minimo_compra < pos_rango < maximo_compra
        self.log.log( f'rango_de_compra ({minimo_compra};{maximo_compra}) pos_rango {pos_rango:.2f}  {escala} maximo {maximo}  px {precio}  {ret}'  )
        return ret 

    def precio_en_rango(self,escala,minimo,maximo):
        precio=self.ind.precio(escala)
        return minimo <= self.rango.posicion_precio(escala,precio) <= maximo    

    def pendiente_positiva_sma_rsi(self,escala):
        pendiente = self.ind.pendiente_sma_rsi(escala)
        ret = pendiente > 0
        self.log.log( f'pendiente_positiva_sma_rsi {ret} {pendiente}'  )
        return ret  

    def pendiente_negativa_sma_rsi(self,escala):
        pendiente = self.ind.pendiente_sma_rsi(escala)
        ret = pendiente < 0
        self.log.log( f'pendiente_negativa_sma_rsi {ret} {pendiente}'  )
        return ret        

    def parte_alta_rango(self,escala,cvelas,porcentaje_bajo=.75):
        minimo,maximo = self.ind.minimo_maximo_por_rango_velas_imporantes(escala,cvelas)
        maximo_compra =  minimo + (maximo - minimo) *  porcentaje_bajo 
        precio = self.ind.precio(escala)
        ret = precio > maximo_compra
        self.log.log( f'parte_alta_rango {escala} min {minimo} px {precio} [max_compra {maximo_compra}] maximo {maximo} {ret}'  )
        return ret 

    def precio_mayor_maximo(self,escala,cvelas,vela_ini):
        maximo = self.ind.maximo_x_vol(escala,cvelas,3,vela_ini)   #3 velas
        if maximo is None:
            ret = False
            precio = None
        else:
            precio = self.ind.precio(escala)
            ret = precio > maximo
        self.log.log( f'precio_mayor_maximo {escala} cvel {cvelas} ini {vela_ini} maximo {maximo} px {precio} {ret}' )
        return ret

    def precio_mayor_minimo(self,escala,cvelas,vela_ini):
        minimo = self.ind.minimo_x_vol(escala,cvelas,3,vela_ini)
        if minimo is None:
            ret = False
            precio = None
        else:    
            precio = self.ind.precio(escala)
            ret = precio > minimo
        self.log.log( f'precio_mayor_minimo {escala} cvel {cvelas} ini {vela_ini} minimo {minimo} px {precio} {ret}' )
        return ret

    def zona_volumen(self,escala,periodos):
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,200,'close',15,15) 
        if len(maximos)>0:
            fin = -maximos[0][0]
            pos_pico, r_vol_pico, r_vol, vol_ema = self.ind.zona_de_alto_volumen(escala,-1,fin) 
            self.log.log(f'pos {pos_pico} volpico {r_vol_pico}, vol {r_vol}, vol_ema {vol_ema}')

        #hay un pico a menos de 25,
        # el volumen pico es mayor a 2
        # el volumen pico es mayor el que volumen promedio de las ultimas velas
        # el volumen de la ultima vela cerrada esta por debajo del promedio (ma)
        ret = pos_pico < 7 and r_vol_pico > 2 #and r_vol_pico > r_vol and r_vol > vol_ema 
        
        return ret

    def picos_volumen(self,escala,periodos,max_pos_ultimo_pico=17,min_cant_picos=3):
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,200,'close',15,15) 
        if len(maximos)>0:
            fin = -maximos[0][0]
            lista_picos = self.ind.picos_de_alto_volumen(escala,fin) 
            cantidad_picos = len(lista_picos)
            if cantidad_picos >0:
                pos_ultimo=lista_picos[0][0]
                self.log.log(f'picos_de_alto_volumen parametro_fin {fin}  pos {pos_ultimo} {lista_picos}')
                ret = pos_ultimo < max_pos_ultimo_pico and cantidad_picos >=min_cant_picos
        
        return ret

    def velas_de_impulso(self,escala,periodos,max_pos_ultimo_impulso=17,min_cant_impulsos=3):
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,300,'close',4,4) 
        if len(maximos)>0:
            fin = -maximos[0][0]
            lista_velas_impulso = self.ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
            xvol_impulso = self.ind.xvolumen_de_impulso(escala,sentido=-1,vela_fin=fin) 
            self.log.log(f'lista_velas_impulso {lista_velas_impulso}')
            self.log.log(f'xvol_impulso {xvol_impulso}')
            cantidad_velas = len(lista_velas_impulso)
            if cantidad_velas >0:
                pos_ultimo=lista_velas_impulso[0][0]
                cvelas_x_10 = 0                          #contador de velas de impulso > a 10x
                for vi in lista_velas_impulso:
                    if vi[1]>10:
                        cvelas_x_10 += 1
                ret =cvelas_x_10 > 0 and pos_ultimo < max_pos_ultimo_impulso and cantidad_velas >=min_cant_impulsos
                self.log.log(f'velas_de_impulso {ret} {cantidad_velas} parametro_fin {fin}  pos {pos_ultimo}')
        
        return ret

    def xvolumen_de_impulso(self,escala,periodos,sentido=-1,xmin_impulso=50):
        '''  desde que empezó a bajar, suma todo el volumen de las velas segun el sentido( -1 bajista, 1 alcista, 0 todo) y lo compara con el volumen promedio
            convirtiendolo en x veces mas. 
            Si ese volumen comparado es mayor al parametrizado(xmin_impulso): retorna True
        '''
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,300,'close',6,6) 
        if len(maximos)>0:
            fin = -maximos[0][0]
            lista_velas_impulso = self.ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
            xvol_impulso = self.ind.xvolumen_de_impulso(escala,sentido,vela_fin=fin) 
            self.log.log(f'velas {-fin} lista_velas_impulso {lista_velas_impulso} ')
            self.log.log(f'xvol_impulso {xvol_impulso}')
            ret = xvol_impulso >= xmin_impulso
            self.log.log(f'xvolumen_de_impulso {ret}')

            return ret

    def xvolumen_de_impulso(self,escala,periodos,sentido=-1,xmin_impulso=50):
        '''  desde que empezó a bajar, suma todo el volumen de las velas segun el sentido( -1 bajista, 1 alcista, 0 todo) y lo compara con el volumen promedio
            convirtiendolo en x veces mas. 
            Si ese volumen comparado es mayor al parametrizado(xmin_impulso): retorna True
        '''
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,300,'close',6,6)
        if len(maximos)>0:
            if maximos[0][1] > self.ind.precio(escala):
                fin = -maximos[0][0]
                xvol_impulso = self.ind.xvolumen_de_impulso(escala,sentido,vela_fin=fin) 
                self.log.log(f'velas {-fin} xvol_impulso {xvol_impulso}')
                ret = xvol_impulso >= xmin_impulso
                self.log.log(f'xvolumen_de_impulso {ret}')
        
        return ret    

    def xvolumen_total(self,escala,periodos, xmin_impulso=50):
        '''  desde que empezó a bajar, suma todo el volumen todas las velas y lo compara con el volumen promedio
            convirtiendolo en x veces mas. 
            Si ese volumen comparado es mayor al parametrizado(xmin_impulso): retorna True
        '''
        ret = False
        maximos=self.ind.lista_picos_maximos_ema(escala,periodos,300,'close',6,6) 
        if len(maximos)>0:
            fin = -maximos[0][0]
            lista_velas_impulso = self.ind.velas_de_impulso(escala,sentido=-1,vela_fin=fin) 
            xvol_impulso = self.ind.xvolumen_de_impulso(escala,sentido=-1,vela_fin=fin) 
            self.log.log(f'velas {-fin} lista_velas_impulso {lista_velas_impulso} ')
            self.log.log(f'xvol_impulso {xvol_impulso}')
            ret = xvol_impulso >= xmin_impulso
            self.log.log(f'xvolumen_de_impulso {ret}')

            return ret

    def pico_minimo_ema(self,escala,periodos):
        ret=False
        minimos = self.ind.lista_picos_minimos_ema(escala,periodos,10,'close',5,1)
        if len(minimos)>0:
            pos = minimos[0][0]
            if pos <=3:
                ret = True
        self.log.log(f'pico_minimo_ema {minimos} {ret}')        
        return ret    

    def pico_minimo_ema_low(self,escala,periodos):
        ret=False
        minimos = self.ind.lista_picos_minimos_ema(escala,periodos,4,'low',5,1)
        if len(minimos)>0:
            pos = minimos[0][0]
            if pos <=3:
                ret = True
        self.log.log(f'pico_minimo_ema_low {minimos} {ret}')        
        return ret    


    def pendientes_emas_positivas(self,escala,periodos,cpendientes=4):
        ret = self.ind.pendientes_positivas_ema(escala,periodos,cpendientes)
        self.log.log(f'pendientes_emas_positivas {ret}')
        return ret

    
    def pendiente_positiva_ema(self,escala,ema_per):
        ret = self.ind.pendiente_positiva_ema(escala,ema_per)
        self.log.log(f'ema_positiva ({escala},{ema_per}) {ret}')
        return ret 

    def cambio_pendiente_ema_de_negativa_a_positiva(self,escala,ema_per):
        pend = self.ind.pendientes_ema(escala,ema_per)
        ret = pend[-1]>0 and pend[-2]<0 and pend[-3]<0
        self.log.log(f'cambio_pendiente_ema_de_negativa_a_positiva {ret},pend {pend}')
        return ret 


    def pendiente_negativa_ema(self,escala,ema_per,pend_max):
        ret = self.ind.pendiente_negativa_ema(escala,ema_per,pend_max)
        self.log.log(f'ema_no_positiva ({escala},{ema_per}) {ret}')
        return ret     

    def dos_emas_positivas(self,escala,ema1_per,ema2_per):
        ret = False
        if self.ind.pendiente_positiva_ema(escala,ema1_per):
            self.log.log('dos_emas_positivas ema1_ok')
            ret = self.ind.pendiente_positiva_ema(escala,ema2_per)
            
        self.log.log(f'dos_emas_positivas {ret}')

        return ret 

    def tres_emas_positivas(self,escala,ema1_per,ema2_per,ema3_per):
        ret = False
        if self.ind.pendiente_positiva_ema(escala,ema1_per):
            self.log.log(f'tres_emas_positivas ema {ema1_per} ok')
            if self.ind.pendiente_positiva_ema(escala,ema2_per):
                self.log.log(f'tres_emas_positivas ema {ema2_per} ok')
                ret = self.ind.pendiente_positiva_ema(escala,ema3_per)
            
        self.log.log(f'tres_emas_positivas {ret}')

        return ret 


    def rsi_minimo_cercano(self,escala,rsi_inferior,pos_rsi_inferior=(2,15),max_rsi=55):
        rsi_min,rsi_min_pos,_,rsi= self.ind.rsi_minimo_y_pos(escala,  pos_rsi_inferior[1]    )
        resultado_filtro=  rsi_min < rsi_inferior and pos_rsi_inferior[0] <= rsi_min_pos <= pos_rsi_inferior[1]  and rsi<max_rsi
        self.log.log(f'{resultado_filtro} <-- de_rsi_minimo_cercano: ')
        self.log.log(f'    busco {rsi_inferior}, actual {rsi_min}')
        self.log.log(f'    rango de cercanía {pos_rsi_inferior}, actual {rsi_min_pos}')
        self.log.log(f'    rsi maximo {max_rsi}, actual {rsi}')
        return resultado_filtro


    def ema_rapida_lenta(self,escala,rapida,lenta,diferencia):
        ok,dif,pl,pr = self.ind.ema_rapida_mayor_lenta2( escala, rapida,lenta,diferencia_porcentual_minima=0.01,pendientes_positivas=True ) 
        self.log.log(f'    {escala} diferencia% {dif}, pend rapida {pr} pend lenta {pl}')
        self.log.log(f'{ok} <--ok_ema_rapida_lenta: {ok}')
        return ok    

    def rsi_maximo(self,escala='1h',valor_maximo=60): 
            ''' True si el rsi es menor al valor_maximo pasado como parámetro'''
            
            rsi =  self.ind.rsi(escala)
        
            ok = rsi < valor_maximo 
            
            self.log.log(f'rsi {escala} max {valor_maximo} rsi {rsi} {ok}')  

            return ok


    def cruce_emas_hacia_arriba(self,escala,per_rapida,per_lenta,cvelas):
        cruce,pos = self.ind.cruce_de_emas(escala,per_rapida,per_lenta,cvelas)
        resultado = cruce ==1 and pos<cvelas
        self.log.log(f'cruce_emas_hacia_arriba cruce {cruce} pos {pos} ')  
        return resultado

    def pendiente_histograma_squeeze_positivo(self,escala):
        pend,histo = self.ind.pendiente_histograma_squeeze(escala,2)    
        ret =  pend[-1] >0 and histo[-2] <0 and histo[-1] <0    #pendiente positiva en squeeze
        self.log.log(f'squeeze_hitograma_positivo {ret}  {pend} {histo}')  
        return ret

    
    

    def histograma_squeeze_a_positivo(self,escala):
        pend=self.ind.pendiente_histograma_squeeze(escala,4)    
        ret = pend[-4] < 0 and pend[-3] < 0 and pend[-2] > 0 and pend[-1] > 0 
        self.log.log(f'histograma_squeeze_a_positivo {ret}  {pend} ')  
        return ret

    def histograma_squeeze_a_negativo(self,escala):
        pend=self.ind.pendiente_histograma_squeeze(escala,4)    
        ret = pend[-4] > 0 and pend[-3] > 0 and pend[-2] < 0 and pend[-1] < 0 
        self.log.log(f'histograma_squeeze_a_negativo {ret}  {pend} ')  
        return ret
    
    def pendiente_adx_negativa(self,escala):
        pend,adx = self.ind.pendientes_adx(escala,2)
        ret = pend[-1] <0
        self.log.log(f'pendiente_adx_negativa {ret}  pend {pend} adx {adx}')  
        return ret
    
    def cambio_de_pendiente_adx(self,escala):
        pend,adx = self.ind.pendientes_adx(escala,2)
        ret = ( pend[-1] * pend[-2] ) < 0
        self.log.log(f'combio_de_pendiente_adx {ret}  pend {pend} adx {adx}')  
        return ret

    def squeeze_negativo_sqz_off(self,escala):
        ret = self.ind.squeeze_negativo_sqz_off(escala,2)
        self.log.log(f'squeeze_negativo_sqz_off {ret}   ') 
        return ret 
    
    def histograma_squeeze_negativo(self,escala):
        histo = self.ind.histograma_squeeze(escala,2)
        ret = histo[-1]<0
        self.log.log(f'histograma_squeeze_negativo {ret}  {histo} ')  
        return ret

    def histograma_squeeze_positivo(self,escala):
        histo = self.ind.histograma_squeeze(escala,2)
        ret = histo[-1]>0
        self.log.log(f'histograma_squeeze_positivo {ret}  {histo} ')  
        return ret
    
    def histograma_squeeze_negativo_con_pendiente_positiva(self,escala):
        pend,histo,cvelas_histo = self.ind.pendiente_histograma_squeeze(escala,2)    
        ret = pend[-1] >0 and histo[-1] < 0 #and cvelas_histo > 4  #pendiente positiva en squeeze
        self.log.log(f'histograma_squeeze_negativo_con_pendiente_positiva {ret} {cvelas_histo}')  
        return ret

    def histograma_squeeze_positivo_con_pendiente_negativa(self,escala):
        pend,histo,cvelas_histo = self.ind.pendiente_histograma_squeeze(escala,2)    
        ret = pend[-1] <0 and histo[-1] > 0 and cvelas_histo > 4  #pendiente positiva en squeeze
        self.log.log(f'histograma_squeeze_positivo_con_pendiente_negativa {ret} {cvelas_histo}')  
        return ret    

    def pendiente_adx_positiva(self,escala):
        pend,adx = self.ind.pendientes_adx(escala,2)
        ret = pend[-2] <0 and pend[-1] <0
        self.log.log(f'pendiente_adx_positiva {ret}  pend {pend} adx {adx}')  
        return ret    

    def cambio_de_pendiente_adx_positiva_a_negativa(self,escala):
        pend,adx = self.ind.pendientes_adx(escala,3)
        ret =  pend[-1] <0 and pend[-2]<0 and pend[-3]>0 
        self.log.log(f'combio_de_pendiente_adx_positiva_a_negativa {ret}  pend {pend} adx {adx}')  
        return ret
    
    def cambio_de_pendiente_adx_negativa_a_positiva(self,escala):
        pend,adx = self.ind.pendientes_adx(escala,3)
        ret =  pend[-1]>1 and pend[-2]>0 and pend[-3]<0 
        self.log.log(f'cambio_de_pendiente_adx_negativa_a_positiva {ret}  pend {pend} adx {adx}')  
        return ret    
    
    def hay_vela_de_agotamiento_de_volumen(self,escala,sentido,velas_hacia_atras):
        vvol=self.ind.velas_volumen(escala,-velas_hacia_atras)
        ret=False
        tipos=[]
        for vv in vvol:
            if vv[2]==sentido:
                tipos.append(vv[1])
        
        if tipos:
            ret = sorted(tipos) == tipos

        self.log.log(f'hay_vela_de_agotamiento_de_volumen {ret}  vvol {vvol}  tipos {tipos} ')      
        return ret         

    def hay_velas_de_impulso_o_volumen(self,escala,sentido,velas_hacia_atras,cantidad_minima=1):
        vvol=self.ind.velas_volumen(escala,-velas_hacia_atras)
        ret=False
        tipos=[]
        for vv in vvol:
            if vv[2]==sentido and vv[1] != 1 :
                tipos.append(vv[1])
        
        ret = len(tipos)>=cantidad_minima

        self.log.log(f'hay_velas_de_impulso_o_volumen {ret}  vvol {vvol}  tipos {tipos} ')      
        return ret 
    
    def hay_velas_de_impulso(self,escala,sentido,velas_hacia_atras,cantidad_minima=1):
        '''busca que existan velas de impulso'''
        vvol=self.ind.velas_volumen(escala,-velas_hacia_atras)
        velas_volumen=[]
        for vv in vvol:
            if vv[2]==sentido and vv[1] >2 : #tipo3  Grandes sin volumen o tipo4 Grande con volumen
                velas_volumen.append(vv[1])
        
        ret = len(velas_volumen)>=cantidad_minima
        self.log.log(f'hay_velas_de_impulso {ret}  \n  velas_volumen {velas_volumen} ')   
        return ret

    def hay_velas_de_impulso_con_fin(self,escala,sentido,velas_hacia_atras,cantidad_minima,cant_minima_fin):
        '''busca que existan velas de impulso pero la ultima se vela pequeña'''
        vvol=self.ind.velas_volumen(escala,-velas_hacia_atras)
        ret=False
        velas_volumen=[]
        velas_fin=None
        for vv in vvol:
            if vv[2]==sentido and vv[1] >2 : #tipo3  Grandes sin volumen o tipo4 Grande con volumen
                velas_volumen.append(vv[1])
        
        ret = len(velas_volumen)>=cantidad_minima
        if ret:
            velas_fin=[]
            for vv in vvol:
                if  vv[1] >2:
                    break
                else:
                    velas_fin.append(vv[1])
            ret = ret and len(velas_fin)>=cant_minima_fin

        self.log.log(f'hay_velas_de_impulso_con_fin {ret}  \n  velas_volumen {velas_volumen} ,\n  velas_fin {velas_fin}')      
        return ret                 
    
    def precio_en_vp(self,escala):
        px = self.ind.precio(escala)
        vp_min,vp_med,vp_max = self.vp.min_med_max(escala)
        zona_max = vp_max     #vp_med + (vp_max-vp_med) *.75  
        zona_min = vp_min     #vp_min + (vp_med-vp_min) *.25
        ret = zona_min < px < zona_max
        self.log.log(f'precio_en_vp {ret}  min {zona_min:.2f} max {zona_max:.2f}  {vp_min} {vp_med} {vp_max} ')      
        return ret

    def precio_en_vp_bajo(self,escala):
        px = self.ind.precio(escala)
        vp_min,vp_med,vp_max = self.vp.min_med_max(escala)
        zona_max = vp_med       
        zona_min = vp_min     
        ret = zona_min < px < zona_max
        self.log.log(f'precio_en_vp {ret}  min {zona_min:.2f} max {zona_max:.2f}  {vp_min} {vp_med} {vp_max} ')      
        return ret    


