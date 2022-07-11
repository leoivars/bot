def retrocesos_convergentes_fibo_macd(self,escala,pos=0):
        '''
        calcula un retroceso fibo varias veces. ordena los resultados por distancia entre resultados.
        pos=0 el de la distancia mas corta
        pos=1 el primer retroceso menor (en precio) a pos=0
        pos=2 el segundo retroceso menor a pos=0

        '''
        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.mercado.get_vector_np_low(escala)
        high = self.mercado.get_vector_np_high(escala)
        
        iperiodo_alcista,fperiodo_alcista=self.periodo_alcista(close)
        
        #print('iperiodo_alcista,fperiodo_alcista',iperiodo_alcista,fperiodo_alcista)

        ret = []
        ifib =1 #el primer nivel despues de 0
        maximo,principio = self.busca_pico_loma_hist(hist,high,low, 1 ,fperiodo_alcista,velas_minimas_de_la_loma=3)
        if maximo != -1: 
            principio_min = principio -1
            
            c=0 #cuenta de macds
            while c<5 and principio_min > iperiodo_alcista:
                minimo,principio = self.busca_pico_loma_hist(hist,high,low, -1 ,principio_min,velas_minimas_de_la_loma=3)
                if minimo >=0:
                    #print('minimo',minimo)
                    for f in range( ifib , len(self.g.ret_fibo) ):
                        r = maximo - (maximo - minimo) * self.g.ret_fibo[f]
                        if r >0 : 
                            ret.append( r )
                else: 
                    break
                c += 1 
                
                principio_min = principio -1

        if len(ret)>0:
            ret.sort()
            dis=[]
            for i in range(1,len(ret)-1):
                di = ret[i]   - ret[i-1]
                dis.append([di, ret[i-1],ret[i]  ])
            
            dis.sort(key=lambda x: x[0])
    
            #print(dis)
            convergencia = dis[0][1]
        else:
            convergencia = 0    

        if pos >0 and convergencia >0:
        #en caso de pos >0 selecciono la convergenica menor 
            valores_por_distancia =[]
            for v in dis:
                valores_por_distancia.append(v[1])
                valores_por_distancia.append(v[2])
            p=1
            i=1
            while p <= pos:
                while valores_por_distancia[i] >= convergencia:
                    i +=1
                convergencia = valores_por_distancia[i]
                p +=1


        return convergencia    


def retrocesos_fibo_macd_ema(self,escala,ifib=2):
        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        ema  = talib.EMA(close, timeperiod=3)
        ret =[]
        maximo,principio = self.busca_pico_loma_hist_ema(hist,ema, 1 ,len(hist)-1,velas_minimas_de_la_loma=5)
        if maximo != -1: 
            principio_min = principio -1
            minimo,principio = self.busca_pico_loma_hist_ema(hist,ema, -1 ,principio_min,velas_minimas_de_la_loma=5)
       
        if minimo >=0:
            for f in range( ifib , len(self.g.ret_fibo) ):
                ret.append( maximo - (maximo - minimo) * (  self.g.ret_fibo[f] ) )
        else: 
            ret.append(0)    
            

        return ret     



def busca_mfi_menor(self,escala,cvelas,valor):
        
        
        
        high=  self.mercado.velas[escala].valores_np_high()
        low=   self.mercado.velas[escala].valores_np_low()
        close= self.mercado.velas[escala].valores_np_close()
        volume=self.mercado.velas[escala].valores_np_volume()

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        
        print(mfi)

        p=-1

        l=len(mfi)#utimo dato del vector
         
        for i in range(l-1,l-cvelas,-1):
            print(mfi[i])
            if mfi[i] <= valor:
                p=l-i-1
        
        return p
def busca_cruce_emas(self,escala,rapida=9,lenta=35,cant_velas=10,close=None):
        
        if close is None:
            vector=vector=self.mercado.get_vector_np_close(self.par,escala,lenta +10)
        else:
            vector = close     
    
        emar=talib.EMA(vector, timeperiod=rapida)
        emal=talib.EMA(vector, timeperiod=lenta)
    
        l=vector.size
        if cant_velas>l:
            c=l
        else:
            c=cant_velas  

        pos=0
        
        # 1 arriba -1 abajo - 0 iguales
        if emar[l-c]>emal[l-c]:
            pos=1
        elif emar[l-c]<emal[l-c]:
            pos=-1
        else:
            pos=0    

        
        cruces=0    
        icruce=0

        for i in range(l-c+1,l):
            if emar[i]>emal[i]:
                if pos<1: # es 0 o -1
                    icruce=i
                    cruces=+1
                pos=1    
                    
            elif emar[i]<emal[i]:
                if pos>-1:
                    icruce=i    
                    cruces=+1
                pos=-1 
            else:
                pos=0    
                    
        return [cruces,pos,l-icruce]  


def _deprecated_tres_emas_favorables(self,escala,per1=9,per2=20,per3=55):
        '''
          Saca las tres emas y si están ordenadas y al mismo tiempo la distancia entre ellas 
          es menor a pchica retorna verdadero
        '''
        
        vector = self.mercado.get_vector_np_close(self.par,escala,per3 +10) 
        
        ordenadas= False
        positivas = False
        ampliandose= False

        vema1=talib.EMA(vector, timeperiod=per1)
        if vema1[-1] > vema1[-2]:
            vema2=talib.EMA(vector, timeperiod=per2)
            if vema2[-1] > vema2[-2]:
                vema3=talib.EMA(vector, timeperiod=per3)
                if vema3[-1] > vema3[-2]:
                    positivas = True

        if positivas:            
            ema1=vema1[-1]
            ema2=vema2[-1]
            ema3=vema3[-1]
            
            if ema1 >= ema2 >= ema3: # las tres emas estan ordenadas
                ordenadas=True
                dfin=vema1[-1]-vema2[-1]
                dini=vema1[-5]-vema2[-5]
                if dfin >0 and dini>0 and dfin>dini:
                    ampliandose = True

                p1=self.pendientes(escala,vema1[-2:],1)[0]  
                p2=self.pendientes(escala,vema2[-2:],1)[0] 
                p3=self.pendientes(escala,vema3[-2:],1)[0] 
                self.log.log('ang,p3p1--->',self.angulo_de_dos_pendientes(p3,p1))
                self.log.log('ang,p3p2--->',self.angulo_de_dos_pendientes(p3,p2))

        
        return (positivas and ordenadas and ampliandose)
def rsi_baja_sin_divergencia(self,escala,rsi_minimo=50,distancia_picos=7,cvelas=28):
        ''' busca dos los dos picos de rsi mas grandes separados como mínimo a una distancia (distancia_picos)
            y si el primer pico mas antiguo es mayor que el pico mas actual y al mismo tiempo el precio está bajando
            retorna True
            caso contrario False

        '''
        df=self.mercado.get_panda_df(self.par,escala)
        # borro la ultima fila que es la de la vela que está en desarrolo
        #df.drop(df.tail(1).index,inplace=True)
        
        rsi = df.ta.rsi()
        #ema = df.ta.ema(length=per_ema)

        if rsi.iloc[-1]<rsi_minimo:
            return False

        l = len(rsi)
        maximos=[]
        ret = False

        #controlo desde la penúltima vela, encontrando los picos
        for i in range(l-cvelas,l-2): 
            if rsi.iloc[i]>=rsi_minimo and self.hay_maximo_en(rsi,i):
                maximos.append(  (rsi.iloc[i],i)  )

        if len(maximos)>1:
            _rsi=0
            _pos=1
            #genero nueva lista con maximos a distancia
            pico_b = maximos[-1]
            pico_a = None
            for r in maximos[:-1]:
                distancia =  pico_b[_pos] - r[_pos]
                if distancia >= distancia_picos:
                    if pico_a is None:
                        pico_a = r
                    else:
                        if pico_a[_rsi] > r[_rsi]:
                            pico_a =r
            
            if not pico_a is None:
                
                if pico_a[_rsi] > pico_b[_rsi]: # el rsi anterior es mayor que el actual
                    if df.iloc[ pico_a[_pos] ]['close'] > df.iloc[ pico_b[_pos]  ]['close']:
                        ret =True
                        self.log.log('rsi_baja_sin_divergencia!')
                
        return ret 

def detectar_patrones(self,escala,cvelas):
        
        o = self.mercado.get_vector_np_open(self.par,escala,cvelas)
        h = self.mercado.get_vector_np_high(self.par,escala,cvelas)
        l = self.mercado.get_vector_np_low(self.par,escala,cvelas)
        c = self.mercado.get_vector_np_close(self.par,escala,cvelas)
        # recolecto todos los patrones que encuentro
         
        valor_patron={} # 1 sube, -1 baja
        valor_patron['CDLMATCHINGLOW']=1
        
        r_pos=0
        r_neg=0
        patrones=[]
        for f in talib.get_functions():
            if f.startswith('CDL'):
                func = getattr(talib, f)
                ret = func(o,h,l,c)
                #print(f,ret)
                if ret[-1]!=0:
                    patrones.append(f)
                    if ret[-1]>0:
                        r_pos += ret[-1]
                    else:
                        r_neg += ret[-1]    

        return {'alcista':r_pos,'bajista':r_neg,'patrones':patrones}        

#esto todavia no está listo... reaprendiendo estadística
    def rango_porcentaje_acumulado(self,escala,tipo,porcentaje_casos=10,redondeo=2):
        ''' Retorna un porcentaje de rango minimo o maximo de una lista ordenada de casos agrupados por repeticiones.
            Ese porcentaje sería suficiente para cubrir todos los casos anteriores que son rangos inferiores
            escala = 1m..1M, tipo -1 = minimo, tipo = 1 maximo, porcentaje_casos = 10 por defecto
        '''    
        restar_velas=1
        
        vopen  = self.mercado.velas[escala].valores_np_open()
        vclose = self.mercado.velas[escala].valores_np_close()

        lx = vopen.size
        cvelas=lx
        
        #contruyo dict rangos 
        drangos={}
        px = self.mercado.velas[escala].ultima_vela().close
        tcasos=0
        for i in range(lx - cvelas, lx-1):
            mi , ma =  self.__valor_menor_mayor(vopen[i],vclose[i])
            if mi < ma:
                tcasos += 1
                rango_vela = round( (ma / mi  - 1 ) * 100,redondeo)
                if rango_vela in drangos:
                    drangos[rango_vela] += 1
                else:
                    drangos[rango_vela] = 1

        #construyo histograma
        vrangos=[]
        for k in drangos.keys():
            
            vrangos.append (  [ k,drangos[k] ]   )

        if tipo == -1:
            vrangos.sort (key=lambda x: x[0]) #ordento los datos de menor a mayor
        else:
            vrangos.sort (key=lambda x: x[0], reverse=True) #ordento los datos de mayor a menor
                   
        suma_porcentaje=0
        ret=0
        for r in vrangos:
            
            suma_porcentaje += r[1]/tcasos * 100
            if suma_porcentaje >= porcentaje_casos:
                ret = r[0] #encontré el valor que abara a todos los casos inferiors a porcentaje_casos
                print ( '----------------------->',ret )
                break

        return  ret

    def __valor_menor_mayor(self,v1,v2):
        if v1 < v2:
            menor = v1
            mayor = v2
        else:
            menor = v2
            mayor = v1
        
        return menor, mayor    

def rango(self,escala,prango_max=2,cvelas=None):
        ''' retorna el rango_actual y el rango que no se supere el prango_max
            tambien retorna la vela donde se superó el rango o la ultima vela posible 
            siempre contando desde lo mas nuevo a lo mas viejo
        '''    
        restar_velas=1
        
        vopen  = self.mercado.velas[escala].valores_np_open()
        vclose = self.mercado.velas[escala].valores_np_close()

        lx = vopen.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        
        px = self.mercado.velas[escala].ultima_vela().close

        #calculo rango actual (ultima vela)
        min , max = self.__valor_menor_mayor(vopen[lx-1],vclose[lx-1])
        prango_actual= round( (max - min) / px * 100 ,2)

        #comienzo de busqueda de rango maximo
        min , max = self.__valor_menor_mayor(vopen[lx-1-restar_velas],vclose[lx-1-restar_velas])
        prango= round( (max - min) / px * 100 ,2)
        
        for i in range(lx - restar_velas - 2, lx-2-cvelas,-1):
            
            mi , ma =  self.__valor_menor_mayor(vopen[i],vclose[i])
            if mi < min:
                min = mi
            if ma > max:
                max = ma
            
            irango= round( (max - min) / px * 100 ,2)

            #print(i,prango)
            if irango > prango_max:
                break
            
            prango = irango # esta rango es bueno, me lo quedo
        
        vela = lx - 2 - i  # lx -1 - i-1

        return  prango_actual, prango, vela

def detectar_patron_rsi_sar(self,p,vela_ini=0,vela_fin=0):
        
        escala = p['escala']
        cvelas = p['cvelas']
        df=self.mercado.get_panda_df(self.par,escala,cvelas + vela_fin + 42 )   #self.velas[escala].panda_df(cvelas + vela_fin +42)
        rsi = df.ta.rsi()
        patron_ok = False
        log=f'p {p}' + '\n'
        
        print(log)
        for i in range(vela_ini,vela_fin):
            arsi = self.analisis_rsi(escala,cvelas,rsi,i)
            if arsi['rsi'] < p['rsi'] and arsi[45]>=p[45] and arsi[35] >=p[35] and arsi[30] >=p[30] and arsi[25] >=p[25] and arsi[20] >=p[20]:
                log+=f'arsi {arsi}, i {i}' + '\n'
                patron_ok = True
                break

        if patron_ok:
            sar = self.sar(escala,vela_ini)
            px  = self.precio(escala)
            if sar < px:
                ret = True
            else:
                ret = False
                log += f'detectar_patron_rsi_sar_NOOK sar {sar}, px {px}'    
        else:
            ret = False
            log += 'detectar_patron_rsi_sar_NOOK'

        return ret,log
    
    def detectar_patron_rsi(self,p):
        
        escala = p['escala']
        cvelas = p['cvelas']
        patron = p['patron']
        df=self.mercado.get_panda_df(self.par,escala,cvelas + 44 )   #self.velas[escala].panda_df(cvelas + vela_fin +42)
        rsi = df.ta.rsi()
        patron_ok = False
        
        arsi = self.analisis_rsi2(escala,cvelas,rsi,1)
        patron_arsi=arsi['patron']
        log=f'arsi {arsi}'
        
        patron_ok = True
        if arsi['rsi'] > p['rsi']: 
            patron_ok=False
        else:    
            for k in patron.keys():
                if patron_arsi[k] < patron[k]:
                    patron_ok = False
                    break

        return patron_ok,log    
   


    def analisis_BB_inferior(self,escala,cant_velas):
        
        vc= self.mercado.get_vector_np_close(self.par,escala) 
        vo= self.mercado.get_vector_np_open(self.par,escala) 
        bs, bm, bi = talib.BBANDS(vc, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

        l=vc.size
        if cant_velas>l:
           c=l
        else:
           c=cant_velas   

        salida=[]

        
        #print ("l,c",l,c,l-c,l-1) 

        for i in range(l-c,l): #recorrido desde el ultimo elemento, el mas atual, al mas viejo
           # print ("i,",i)
            if vo[i]<vc[i]: #vela alsista
                if vo[i]>=bi[i]:  #abre y cierra por encima de la banda inferior
                    salida.append( 3)
                elif vo[i]<=bi[i] and vc[i] >=bi[i]:  #la vela abre abajo de la bi (banda inferior) y cierra encima de la bi
                    salida.append( 2)
                elif vc[i]<=bi[i]:  #la vela abre y cierra por debajo  abajo de la bi (banda inferior)
                    salida.append( 1)
                else:
                    salida.append( 0)   

            else: #vela bajista
                if vc[i] >= bi[i]:  #abre y cierra por encima de la banda inferior
                    salida.append( -1)
                elif vo[i]>=bi[i] and vc[i] <=bi[i]:  #la vela abre encima de bi y cierra debajo de bi
                    salida.append( -2)
                elif vo[i]<=bi[i]:  #labre y cierra por bajo de la banda inferior
                    salida.append( -3)
                else:
                    salida.append( 0)         

        return salida            
    

    def tendencia_adx(self,escala,per_rapida=10,per_lenta=55,c=None,h=None,l=None):
        '''
         evalua la tendencia y el adx retornando los siguientes valores
          5 ascendente con mucha fuerza
          4 ascendente con fuerza
          3 ascendente sin fuerza pero creciendo el interés
          2 ascendente con fuerza y perdinedo interé
          1 ascendente sin fuerza y perdiendo el interes
         -1 bajista , sin fuerza y perdiendo fuerza (adx hacia abajo)
         -2 bajista , con fuerza pero perdiendo fuerza (adx hacia abajo)
         -3 bajista , sin fuerza y fuerza creciente (adx hacia hacia arriba)
         -4 bajista , con fuerza y creciendo

        '''
        if c is None:
            c=self.mercado.get_vector_np_close(escala)
            h=self.mercado.get_vector_np_high(escala)
            l=self.mercado.get_vector_np_low(escala)

        emar=talib.EMA(c , timeperiod=per_rapida)
        emal=talib.EMA(c , timeperiod=per_lenta)
        adx = self.adx(escala,c,h,l)
        #print(adx)
        ret=0
        confirmacion_adx = self.g.confirmacion_adx
        if emar[-1] > emal[-1]: #alcista
            if adx[1]>0: #pendiente positiva
                if adx[0] >= confirmacion_adx:
                    if adx[0] >= confirmacion_adx * 1.1:
                        ret=5 # hay mucha fuerza
                    else:
                        ret=4 # hay fuerza
                else:
                    ret=3 # está creciendo el interés pero no hay fuerza
            else:
                if adx[0] >= confirmacion_adx: 
                    ret=2 # hay fuerza pero se está perdiendo el interés
                else:
                    ret=1 # no hay fuerza y se está perdiendo el interés
        else: #bajista
            if adx[1]>0:
                if adx[0] >= confirmacion_adx:
                    ret=-4
                else:
                    ret=-3
            else:
                if adx[0] >= confirmacion_adx:
                    ret=-2
                else:
                    ret=-1

        return ret            

    def situacion_adx_macd(self,escala):
        ''' Evalua la situación del adx con el macd
            si hist-,pend+ adx- y menor a 23 ----> 2 --> rango o caída pero  ya sin fuerza y recuperando 
            si hist+,pend+ adx+ y mayor=23 ------> 1 --> subiendo con fuerza
            cual quier otro caso 0 ----> no comprar
        '''
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)
    
        _, _, hist = talib.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)
        dhist = self.macd_describir(escala,hist)
        adx = self.adx(escala,c,h,l)

        ret = 0

        if dhist[1] == 1: # la pendiente debe ser positiva en ambos casos
            if dhist[0] == -1  and adx[1] < 0 and adx[0] < 23:
                ret = 2
            elif dhist[0] == 1 and adx[1] > 0 and adx[0] >= 23:
                ret = 1    

        return  ret

    def situacion_adx_macd_rango_caida(self,escala):
        ''' Evalua la situación del pendiete/adx con el macd
           ---> rango o caída  --> True
            sino retorna False
            
        '''
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        tadx = self.tendencia_adx(escala,9,55,c,h,l) 
        if  tadx < 3:
            _, _, hist = talib.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)
            dhist = self.macd_describir(escala,hist)
            ret = dhist[0] == -1 and dhist[1] == 1 
        else:
            ret = False    
        
        return ret


    def adx(self,escala,close=None,high=None,low=None):
        if close is None or high is None or low is None:
            
            c=self.mercado.get_vector_np_close(escala)
            h=self.mercado.get_vector_np_high(escala)
            l=self.mercado.get_vector_np_low(escala)
        else:
            c = close
            h = high
            l = low    

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size

        
        try:
            radx=round(vadx[l-1],2)
            m01= round( vadx[l-1] - vadx[l-2] ,2 ) 
            m02= round( vadx[l-2] - vadx[l-3] ,2 )
            m03= round( vadx[l-3] - vadx[l-4] ,2 )
            m04= round( vadx[l-4] - vadx[l-5] ,2 )
        except:
            radx=0
            m01=-1
            m02=-1
            m03=-1
            m04=-1

        
        return [radx,m01,m02,m03,m04]
    def adx_negativo(self,escala,close=None,high=None,low=None):
        ''' retorna una lista con
            [0] = True si es negativa la pendiente del adx
            [1] el pico negativo del adx
            [2] el valor actual del adx
        '''
        if close is None or high is None or low is None:
            
            c=self.mercado.get_vector_np_close(escala)
            h=self.mercado.get_vector_np_high(escala)
            l=self.mercado.get_vector_np_low(escala)
        else:
            c = close
            h = high
            l = low    

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size
        lneg = l * -1

        pico = 0
        padx = -1
        
        negativo = False
         
        try: 

            if vadx[-2] > vadx[-1]: #hay pendiente negativa
                negativo = True
                #busco cual fue el pico
                i=-2
                while i > lneg:
                    if vadx[i-1] < vadx[i]:
                        pico = i
                        break
                    i -= 1

            if pico < 0: #encontró el pico 
                padx = vadx[pico]   
        except Exception as e:
            self.log.log(str(e)) 

    
        return [negativo,padx,vadx[-1]]           

        
        

    def adx_mr(self,escala):
        '''
        Es casi lo mismo que adx per las pendienteas con relativas a la ultima vela
        '''
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        vadx=talib.ADX(h,l, c, timeperiod=14)
        l=vadx.size

        
        try:
            radx=round(vadx[l-1],2)
            m01= round( vadx[l-1] - vadx[l-2] ,2 ) 
            m02= round( (vadx[l-1] - vadx[l-3])/2 ,2 )
            m03= round( (vadx[l-1] - vadx[l-4])/3 ,2 )
            m04= round( (vadx[l-1] - vadx[l-5])/4 ,2 )
        except:
            radx=0
            m01=-1
            m02=-1
            m03=-1
            m04=-1

        return [radx,m01,m02,m03,m04]
    

    def rsi_minimo(self,escala,close=None):
        ''' retorna el rsi minimo local y el rsi actual
        '''
        if close is None:
            
            c = self.mercado.get_vector_np_close(escala)
        else:
            c = close

        rsi=talib.RSI( c , timeperiod=14)
        
        minimo = 100
        l=rsi.size
        mi = 0
        
        
        i=-1
        lneg = l * -1
        try:
            if rsi[-2] < rsi[-1]:
                while i > lneg:
                    if rsi[i-1] > rsi[i]:
                        mi = i
                        break
                    i -= 1

                if mi < 0:
                    minimo = rsi[mi]    
    
        except Exception as e:
            self.log.log(str(e))  

        return minimo,rsi[-1]  # si no ecuetra minimo retorna 100 que es un valor seguro para la toma de desiciones que se pretende tomar con esta funcion  

    def sar(self,escala,vela_ini=0):
        h=self.mercado.get_vector_np_high(self.par,escala) #   self.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(self.par,escala)  #     self.get_vector_np_low(escala)
        vsar=talib.SAR(h,l, acceleration=0.02, maximum=0.2)
        vela = -1 + vela_ini * -1

        return float(vsar[vela]) # -2 es la ultima vela cerrada -1 vela en desarrollo 

    def macd(self,escala):
        
        close = self.mercado.get_vector_np_close(escala)
        
        r_macd, r_macdsignal, r_macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        l=len(r_macd)-1
        
        return [r_macd[l], r_macdsignal[l], r_macdhist[l]]    

    def macd_analisis(self,escala,cvelas):
        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        
        senial=0
        p=-1
        for u in range(l-1,l-cvelas,-1):
            #print (u,hist[u-1], hist[u])
            if hist[u]==0 or hist[u-1]<0 and hist[u]>0: #histograma positivo y creciente
                if mac[u]>=sig[u]:
                    for i in range(u-1, u-5, -1): 
                        if mac[i] < sig[i] and mac[u]>mac[i]:
                            #deteccion de cruce positivo
                            senial=1
                            p=l-u-1
                            break
            elif hist[u]==0 or hist[u-1]>0 and hist[u]<0: #histograma negativo y decreciente
                if mac[u]<=sig[u]:
                    for i in range(u-1, u-5, -1): 
                        if mac[i] > sig[i] and mac[u] < mac[i]:
                            #deteccion de cruce negativo, señar de salida
                            senial=-1
                            p=l-u-1
                            break
            if senial !=0:
                break 
        
        #analisis del histotrama para detectar si pasa por el punto cero
        senial_hist=0
        psenial_hist=-1
        for u in range(l-2,l-cvelas,-1): 
            if hist[u-1] == 0:
                senial_hist=1
                psenial_hist = l - u - 2
                break
            elif hist[u-1] > 0  and hist[u] <0:
                senial_hist=3
                psenial_hist = l - u - 1
                break
            elif hist[u-1] < 0 and  hist[u] > 0:
                senial_hist=2
                psenial_hist = l - u - 1
                break

        #si hay señal devuelvo el histograma
        #if senial==0: #no se encontró un cruce
        #    h=-9999
        #else:
        #    h=hist[u]  

        #pendiente de 
        #m00=  mac[l-1]-mac[l-2]     #aca iria /1 pero es al pedo dividir por 1
        #mp2= (mac[l-1]-mac[l-int(cvelas/2)])/7 # vela intermedia
        #mpp= (mac[l-1]-mac[l-14])/14

        mhist=  hist[l-1]-hist[l-2]     #aca iria /1 pero es al pedo dividir por 1        
        



        return [senial,p,hist[l-1],mhist,senial_hist,psenial_hist]                        
    

     def retroceso_macd_hist_max(self,escala):
        ''' en la escala seleccionada retorna un precio entre el precio
        desde que el histograma =0 hasta que el histograma toma su valor máximo '''

        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        px=0

        #1) busco maximo historial de macd
        imax=-1
        for i in range(l-1,1,-1):
            
            if hist[i-1] <  hist[i]  and hist[i-1] >0 and  hist[i] >0 : #estamos en bajada, seguimos
                imax = i
                break
        
        if imax > -1:
            icero = - 1

            #2) busco la primer vela positiva
            for i in range(imax,1, -1):
                
                if hist[i-1] <0 and  hist[i]>=0:
                    icero=i
                    break
  
            px =  close[icero] + ( close[imax] - close[icero] ) *.5

        return px    

    def divergenica_macd(self,escala):

    
        ''' busca divergencias en el macd '''

        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        i= l - 1
        
        ipos=[]
        zona_signo= 1 if hist[i] > 0 else -1
        signo_hist= zona_signo * -1 # si entoy en positivo busco negativo y si estoy en negativo, busco positivo
        max = 0
        imax= -1
        cambios = 0
        while i > -1:
            signo = 1 if hist[i] > 0 else -1 
            
            if signo == zona_signo:#cambio de signo
                if signo_hist and signo: #sigo en la misma zona
                    if signo == 1:
                        if hist[i] > max:
                            max = hist[i]
                            imax = i
                    else:
                        if hist[i] < max:
                            max = hist[i]
                            imax = i
            else:
                
                if signo_hist == zona_signo:
                    ipos.append(imax)
                
                zona_signo = signo
                imax=i
                max=hist[i]
            
            if len(ipos)==2:
                break    
            i -= 1

       # print ('ipos',ipos)
        div = 0
        if len(ipos)==2:
            a = ipos[1]
            b = ipos[0]
           # print (l-b,l-a)
            if signo_hist: # signo positivo
                if hist[a] > hist[b] and close[a] < close[b]:
                    div = -1 #divergencia bajista
                elif hist[a] < hist[b] and close[a] >= close[b]:
                    div = 1
            else: # signo negativo
                if hist[a] < hist[b] and close[a] >= close[b]:
                    div = 1 
                elif hist[a] > hist[b] and close[a] < close[b]:
                    div = -1  

        print (signo_hist)
        return div            
        
    def promedio_bajos_macd(self,escala):
        
        close = self.mercado.get_vector_np_close(escala)
        _, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.mercado.get_vector_np_low(escala)
        ultimo = len(low)-1
        principio,final = self.busca_princpipio_y_final_loma(hist,ultimo)

        subset = low[principio:final+1]
        vector_emas  = talib.EMA(subset, timeperiod=3)
        ret =  vector_emas[-1] 

        #si no se pudiera calcular la ema, se toma el valor mas chico del rango
        if np.isnan(ret):
            #print('ema',ret)
            top = int(len(subset)/5)
            if top == 0:
                top=1
            subset[::1].sort() 
            ret = np.average(subset[ 0 : top+1 ] )

        return float( ret) 

    def buscar_escala_con_rango_o_caida_macd(self,escala):
        ''' empieza por la escala  y si encuentra rango o caída retorna esa escala 
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de 1m '''
        esc = escala
        while esc != "1m": # si llega a 1m  la retorna
            if self.situacion_adx_macd_rango_caida(esc): 
                break
            else:
                esc = self.g.escala_anterior[esc]
        
        return esc 

    def buscar_subescala_con_tendencia(self,escala,per_rapida=10,per_lenta=55):
        ''' empieza por la escala  y si encuentra tendencia   retorna esa escala
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de 1m '''
        esc = self.g.escala_anterior[escala]
        escala_tope="5m"
        while esc != escala_tope: # solo busca hasta escala_tope
            if self.tendencia_adx(esc,per_rapida,per_lenta) >=3 :  #3 tendendia 4 tendencia confirmada
                break
            else:
                esc = self.g.escala_anterior[esc]
        if esc == escala_tope:
            esc ='xx' # se llegó a tope y no se encontró nada.
        return esc 

    def buscar_subescala_con_rango_o_caida_macd(self,escala):
        ''' empieza por la escala  y si encuentra rango o caída retorna esa escala 
            caso contrario se fija en una escala mas chica
            si no encuntra nada, retorna la escala de xx '''
        esc = self.g.escala_anterior[escala]
        while esc != "xx": # si llega a 1m  la retorna
            if self.situacion_adx_macd_rango_caida(esc) : 
                break
            else:
                esc = self.g.escala_anterior[esc]
        
        return esc     


    
    def busca_principio_macd_hist_min(self,escala):
        ''' retorna la posición del primer  histograma en minimo
        '''
        
        close = self.mercado.get_vector_np_close(escala)
        mac, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector
        
        li=l-1

        lfin=-1
        lini=-1
        

        while li >=0:
            if lfin==-1:
                if hist[li]<0:
                    lfin = li
                    
            if lfin > -1:
                if hist[li] <0:
                    lini=li
                else:
                    break
            li -= 1    

        if lini > -1:
            ret = l - lini
        else:
            ret =-1

        return ret                

    
    def el_precio_puede_caer(self,escala):
        ''' situacion1:
            macd+ pendiente- no compramos
        
            situacion2:
            estando en una loma de hist+ de 2 o mas de velas y adx+ 
            busca en el histograma negativo anterior el precio máximo alcanzado 
            y si ese precio no es superado ( se rompió la resistencia ) es posible 
            que el precio caiga '''

        
        hist,sqz = self.sqzmon_lb(escala)
        low  = self.mercado.get_vector_np_low(escala)
        high = self.mercado.get_vector_np_high(escala)
        close = self.mercado.get_vector_np_close(escala)

        ult_vela=len(close) -1 
        ret = False
        
        #situacion 1
        desc_hist = self.squeeze_describir(escala,hist,sqz)
        if desc_hist[0] == 1 and desc_hist[1]  == -1: 
            ret = True

        # situacion 2
        if not ret: 
            tam,signo_loma,principio,pxpico = self.propiedades_macd_loma(hist,high,low,ult_vela)

            #print("tam,signo_loma,principio,pxpico",tam,signo_loma,principio,pxpico)

            if tam > 2 and signo_loma ==1:
                #adx = self.adx(escala,close,high,low)
                #print('adx',adx)
                #if adx[1] > 0:
                siguiente = principio - 1
                #print('siguiente',siguiente)
                if siguiente >0:
                    pico, principio = self.busca_pico_loma_hist(hist,high,low,-1,siguiente,1)
                    #print('pico, principio,precio',pico, principio,close[ult_vela])
                    if pico > close[ult_vela]:
                        ret = True # el precio puede caer!


        return ret            
    
    
    def retrocesos_fibo_macd(self,escala,ifib=2):
        
        close = self.mercado.get_vector_np_close(escala)
        mac, sig, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        low  = self.mercado.get_vector_np_low(escala)
        high = self.mercado.get_vector_np_high(escala)
        ret =[]
        minimo =-1
        maximo,principio = self.busca_pico_loma_hist(hist,high,low, 1 ,len(hist)-1,velas_minimas_de_la_loma=5)
        if maximo != -1: 
            principio_min = principio -1
            minimo,principio = self.busca_pico_loma_hist(hist,high,low, -1 ,principio_min,velas_minimas_de_la_loma=5)
        if minimo >=0:
            for f in range( ifib , len(self.g.ret_fibo) ):
                #print(self.g.ret_fibo[f])
                ret.append( maximo - (maximo - minimo) * (  self.g.ret_fibo[f] ) )
        else: 
            ret.append(0)    

        return ret  
       

    def busca_macd_hist_min(self,escala,vela_fin=0):
        ''' 
        dede vela_fin (0 es la ultima)
        busca el mínimo del histograma en el macd y retornas
        [0] = -1 si no encontró minimo
        [0] > -1 si no encontró minimo
        [1] distancia del minimo a la posicion actual
        [2] signo del ultimo histograma y anterior
            -1 los dos son negativos
             1 los dos son positivos
             0 uno es positivo y el otro es negativo para cuando [0] >-1
        [3] pendiente entre el penultimo y ultimo histograma
        [4] cantidad de velas del minimo
        [5] cantidad de velas con pendiente positiva
        [6] rsi de minimo
        [7] incremento del precio experado en atrdebajos
        
          
        '''

        
        close = self.mercado.get_vector_np_close(escala)
        mac, _, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        l=len(mac)#utimo dato del vector

        #1) busco minimo histograma de macd
        imin=-1
        for i in range(l-1-vela_fin,1,-1):
            #print(i,hist[i],close[i])
            if hist[i-1] >  hist[i]  and hist[i-1] < 0 and  hist[i] < 0 : #estamos en bajada, seguimos
                imin = i
                break
        
        #print('---->imax',imax)
        
        if imin > -1:
            mxhist = hist[l-1] - hist[l-2]
            dx=l-imin-1-vela_fin
            if hist[l-1] < 0  and hist[l-2]  < 0:
                signo = -1
            elif hist[l-1] > 0  and hist[l-2]  > 0:
                signo = 1
            else:
                signo = 0 
            
            #cuento las velas del minimo
            chist_neg=1
            i= imin + 1 #l-imin es el indice absoluto
            while i < l-1:
                if hist[i] < 0:
                    chist_neg += 1
                    i +=1
                else:
                    break
            i= imin - 1
            while i >= 0:
                if hist[i] < 0:
                    chist_neg += 1
                    i -=1
                else:
                    break

            #calculo del rsi del minimo
            vrsi=talib.RSI(close, timeperiod=14)
            rsi=vrsi[imin]    
               

        else:
            mxhist=-1
            dx=-1
            signo = 0
            chist_neg = 0
            imin=-1
            rsi=None
        
        #cuento velas con pediente positivas y seguidas desde la vela actual
        cant_velas_pen_positiva=0
        if signo < 1 and mxhist>=0:
            #print(l-1,l-dx-1)
            for i in range(l-1,l-dx-1,-1):
                #print(i,hist[i-1],hist[i],)
                if hist[i-1]<=hist[i]: #el histo de la vela actual es menor o igual que el anteior sumo 1
                    cant_velas_pen_positiva+=1
                else: # se corta la seguidilla, dejo de sumar
                    break 

        #incremento 
        # saco el aumento del precio y si hay un aumento
        # lo comparo con el atr_bajos aumentado en la cantidad de velas que ha trascurrido
        # si el incremoento porcentual es muy grande ( a determiar ) se puede
        # interpretar como un posible pump
        incremento= -1
        if imin >0:
            vi: Vela = self.mercado.velas[escala].get_vela(imin)
            vf: Vela = self.mercado.velas[escala].ultima_vela()

            deltap = vf.close - vi.low
            if deltap >0:
                atrb = self.atr_bajos(escala,top=50,cvelas=None,restar_velas=1)
                incremento= round( variacion((atrb * (dx+1)) , deltap) ,2 )

        
        return [imin,dx,signo,mxhist,chist_neg,cant_velas_pen_positiva,rsi,incremento]
    def macd_describir(self,escala,histo=None):
        '''
        Hace macd y describe su histograma

        [0] = 1  macd positivo
        [0] = -1 macd negativo
        [1] = 1 pendiente positiva distancia del minimo a la posicion actual
        [1] = -1 pendiente negativa
          
        '''
        if histo is None:
            #vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 10) 
            close = self.mercado.get_vector_np_close(self.par,escala)
            _, _, hist = talib.MACD(close, fastperiod=10, slowperiod=26, signalperiod=9)
        else:
            hist = histo   

        l=len(hist)-1#utimo dato del vector

        #signo del histograma
        signo=-1
        if hist[l]>0:
            signo=1

        #
        pendiente=-1
        if hist[l-1] < hist[l]:
            pendiente=1

        return [signo,pendiente]     

    def squeeze_describir(self,escala,hist=None,sqz=None):
        '''
        Hace squeeze y describe su histograma

        [0] = 1  squeeze positivo
        [0] = -1 squeeze negativo
        [1] = 1 pendiente positiva distancia del minimo a la posicion actual
        [1] = -1 pendiente negativa
          
        '''

        if hist is None:
            hist,sqz = self.sqzmon_lb(escala)
        
        l=len(hist)-1#utimo dato del vector

        #signo del histograma
        
        signo=0
        if hist[l]>0:
            signo=1
        else:
            signo=-1    

        pendiente=0
        if hist[l-1] < hist[l]:
            pendiente=1
        else:
            pendiente=-1    

        return [signo,pendiente,sqz[-1]]    
 

    

    
                    
    def busca_rsi_menor(self,escala,rsi_menor,cant_velas):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        vrsi=talib.RSI(vector, timeperiod=14)
        l=vector.size
        if cant_velas>l:
           c=l
        else:
           c=cant_velas  

        imenor=0# indi
        rsim=100# valor del rsi menor
        for i in range(l-c,l):
            if vrsi[i]<rsim:
                imenor=i
                rsim=vrsi[i]

        ic=l-1-imenor
        return [rsim<=rsi_menor and ic<=c,round(rsim,2),ic]       

    def tres_emas_favorables2(self,escala,per1=9,per2=20,per3=55):
        '''
          Saca las tres emas y si están ordenadas y al mismo tiempo la distancia entre ellas 
          es menor a pchica retorna verdadero
        '''
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per3 +10) 
        
        ordenadas= False
        positivas = False
        sar_ok = True

        vema1=talib.EMA(vector, timeperiod=per1)
        if vema1[-1] > vema1[-2] and vema1[-1]>vema1[-3] and vema1[-1]>vema1[-4] and vema1[-1]>vema1[-5]:
            vema2=talib.EMA(vector, timeperiod=per2)
            if vema2[-1] > vema2[-2] and  vema2[-1]>vema2[-3]:
                vema3=talib.EMA(vector, timeperiod=per3)
                if vema3[-1] > vema3[-2]:
                    positivas = True

        if positivas:            
            ema1=vema1[-1]
            ema2=vema2[-1]
            ema3=vema3[-1]
            
            # uv:Vela = self.mercado.par_escala_ws_v[self.par][escala][1].ultima_vela()
            # vela_corta_ema3 = uv.signo ==1 and uv.open < ema3 < uv.close
                


            if ema1 > ema3 and  ema2 > ema3 : # las dos emas rápidas mayor que la lenta
                ordenadas=True
                sar = self.sar(escala)
                px = self.precio_mas_actualizado()
                if sar < px:
                    sar_ok = True

                # p1=self.pendientes(escala,vema1[-2:],1)[0]  
                # p2=self.pendientes(escala,vema2[-2:],1)[0] 
                # p3=self.pendientes(escala,vema3[-2:],1)[0] 

                # vema4=talib.EMA(vector, timeperiod=55)
                # p4=self.pendientes(escala,vema4[-2:],1)[0]
                

                # self.log.log('ang,p1--->',self.angulo_de_dos_pendientes(0,p1))
                # self.log.log('ang,p2--->',self.angulo_de_dos_pendientes(0,p2))
                # self.log.log('ang,p3--->',self.angulo_de_dos_pendientes(0,p3))
                # self.log.log('ang,p4--->',self.angulo_de_dos_pendientes(0,p4))
                # dfin=vema1[-1]-vema2[-1]
                # dini=vema1[-3]-vema2[-3]
                # ampliandose = dfin >0 and dini>0 and dfin>dini
                #ampliandose = self.distancia_entre_emas_ampliandose(self.g.zoom_out(escala,1),per1,per2,3)
        
        return (positivas and ordenadas and sar_ok) #and ampliandose)

    def dos_emas_favorables(self,escala,per1=9,per2=20):
        '''
          Saca las dos emas si la rápida > que lenta y sar por debajo del precio, ok

        '''
        rsi = self.rsi_vector(escala,cvelas=5)
        if not ( rsi[-1] > rsi[-2] and rsi[-1]>rsi[-3] and rsi[-1]>rsi[-4] ) :
            return False

        vector=self.mercado.get_vector_np_close(self.par,escala,per2 +30) 
        
        ordenadas= False
        positivas = False
        sar_ok = True

        vema1=talib.EMA(vector, timeperiod=per1)
        if vema1[-1] > vema1[-2] and vema1[-1]>vema1[-3] and vema1[-1]>vema1[-4] and vema1[-1]>vema1[-5]:
            vema2=talib.EMA(vector, timeperiod=per2)
            if vema2[-1] > vema2[-2] and  vema2[-1]>vema2[-3]:
                positivas = True

        if positivas:            
            ema1=vema1[-1]
            ema2=vema2[-1]
            
            # uv:Vela = self.mercado.par_escala_ws_v[self.par][escala][1].ultima_vela()
            # vela_corta_ema3 = uv.signo ==1 and uv.open < ema3 < uv.close

            if ema1 > ema2:
                ordenadas=True

                sar = self.sar(escala)
                px = self.precio_mas_actualizado()
                if sar < px:
                    sar_ok = True

                
        return (positivas and ordenadas and sar_ok)

    
    def distancia_entre_emas_ampliandose(self,escala,rapida,lenta,velas_de_distancia):
        vector=vector=self.mercado.get_vector_np_close(self.par,escala,lenta +30)
        vema_rap=talib.EMA(vector, timeperiod=rapida)
        vema_len=talib.EMA(vector, timeperiod=lenta)
        iantes = velas_de_distancia * -1
        distancia_ahora = vema_rap[-1] - vema_len[-1]
        distancia_antes = vema_rap[iantes] - vema_len[iantes]
        if distancia_ahora > 0 and distancia_antes > 0 and distancia_antes > distancia_ahora:
            return True
        else:
            return False    
    #retorna verdadero si la ema rápida está por debajo de la lenta
    def ema_rapida_menor_lenta(self,escala,per_rapida,per_lenta):
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 10) 
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)
        r = emar[-1]
        l = emal[-1]
        self.log.log('ema_rapida_menor_lenta',r,l)
        return r < l

    def _deprecated_ema_rapida_menor_lenta_2(self,escala,per_rapida,per_lenta,diferencia_porcentual_maxima=0,pendientes_negativas=False):
        ''' calcula la ema rapia y la lenta luego saca la diferencia_porcentual
        y si la diferencia_porcentual es menor diferencia_porcentual_maxima o las pendientes
        de ambas emas son negativa  retorna True, tambien retorna datos para log..
        si pendientes_negativas=True exige que las pendientes sean negativas al mismo tiempo que se de la diferencia porcentual''' 
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per_lenta + 50) 
        
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        r = emar[-1] 
        l = emal[-1] 

        pend_r=round(self.pendientes(escala,emar,1)[0] * 100,4)
        pend_l=round(self.pendientes(escala,emal,1)[0] * 100,4)

        try:
            diferencia_porcentual= round(    (( r / l ) -1 )  * 100       ,2)
        except:
            diferencia_porcentual= -100

        if pendientes_negativas:
            emas_ok = diferencia_porcentual < diferencia_porcentual_maxima and (pend_r <0 and pend_l <0)
        else:    
            emas_ok = diferencia_porcentual < diferencia_porcentual_maxima or (pend_r <0 and pend_l<0)

        return emas_ok, diferencia_porcentual,round(pend_r,2),round(pend_l,2)


    def ema_vector_completo(self,escala,periodos):
        
        vector=self.mercado.velas[escala].valores_np_close()
        ema=talib.EMA(vector, timeperiod=periodos)
        return ema  


    def coeficiente_ema_rapida_lenta(self,escala,per_rapida,per_lenta):   
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        emar=talib.EMA(vector, timeperiod=per_rapida)
        emal=talib.EMA(vector, timeperiod=per_lenta)

        return float(round ( (1 - emal[emal.size-1] / emar[emar.size-1] )*100,2))
 
        def rsi_mom(self,escala):
        
        

        vector=self.mercado.velas[escala].valores_np_close()

        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        rsi=vrsi[vrsi.size-1]
        mom=vmom[vmom.size-1]
     

        return [rsi,mom]

    def rsi_vector(self,escala,cvelas=5):

        
        vector=self.mercado.get_vector_np_close(self.par,escala,40)
        vrsi=talib.RSI(vector, timeperiod=14)
        v = cvelas * -1
        return vrsi[v:] 

    def mfi_vector(self,escala,cvelas=5):

        
        high=   self.mercado.get_vector_np_high(self.par,escala,40)
        low=    self.mercado.get_vector_np_low(self.par,escala,40)
        close=  self.mercado.get_vector_np_close(self.par,escala,40)
        volume= self.mercado.get_vector_np_volume(self.par,escala,40)

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        v = cvelas * -1
        return mfi[v:]   


    def precio_de_rsi(self,escala,rsi_buscado):
        ''' retorna el precio (mas bajo) para llegar al ris
            indicado como parámetro de las escala en que se busca.
        '''
        
        
        vector=self.mercado.get_vector_np_close (self.par,escala)
        vrsi=talib.RSI(vector, timeperiod=14)
        rsi_verdadero=vrsi[vrsi.size-1]

        ultimo = vector.size -1
        px_orig= vector[ultimo]
        
        salto = px_orig  / 100
        
        if rsi_buscado < rsi_verdadero:
            signo = -1
        else:
            signo = 1    
        
        i=1
        j=0
        diff_anterior=1000
        px_anterior=px_orig
        while i <20 and j<40:
            px = px_orig + salto * signo * i 
            vector[ultimo] = px
            vrsi = talib.RSI(vector, timeperiod=14)
            rsi_nuevo = vrsi[vrsi.size-1]
            
            diff = abs(rsi_nuevo - rsi_buscado)
           
            #print ('--',px, diff,diff_anterior)

            if  diff > diff_anterior:
                #print ('--->')
                if abs(diff) > 0.5:
                    salto = salto * 0.4
                    signo = signo * -1
                    px_orig = px_anterior
                    i = 0
                else:
                    break
            else:
                diff_anterior = diff  
                px_anterior = px  
            
            i += 1
            j+=1
            
        print(rsi_nuevo,px)
       


        return px


        

    def compara_rsi(self,escala,cant_rsi):
        ''' retorna un vector con la diferencias de la rsi actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        
        close=self.mercado.velas[escala].valores_np_close(50)
        vrsi=talib.RSI(close, timeperiod=14)
        l=vrsi.size
        ret=[]
        for i in range( l - cant_rsi , l):
            #print(vema[i], vema[i-1],vema[i] - vema[i-1])
            diferencia = vrsi[i] - vrsi[i-1]
            ret.append( diferencia ) 
        
        return ret    



    def mfi(self,escala):
        
        
        
        high=  self.mercado.velas[escala].valores_np_high(40)
        low=   self.mercado.velas[escala].valores_np_low(40)
        close= self.mercado.velas[escala].valores_np_close(40)
        volume=self.mercado.velas[escala].valores_np_volume(40)

        mfi = talib.MFI(high, low, close, volume, timeperiod=14)
        
        return round(float(mfi[mfi.size-1]),2)



    def mom(self,escala):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        mom=vmom[vmom.size-1]
        

        return mom

    def momsube(self,escala,x_mas_de_la_ema):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)
        vema=talib.EMA(vmom  , timeperiod=10)
       
        mom=vmom[vmom.size-1]
        ema=vema[vema.size-1]

        return [mom > ema * x_mas_de_la_ema,mom,ema]    
    
    #vector de momentums, retorna un vector con los tres ultimos momentums
    def vmom(self,escala,periodos):
        
        vector=self.mercado.get_vector_np_close(escala)
        vmom=talib.MOM(vector, timeperiod=periodos)

        return [ vmom[vmom.size-3],vmom[vmom.size-2] , vmom[vmom.size-1] ]

    

    def esta_subiendo4(self,escala):

        
        uv   =self.mercado.velas[escala].ultima_vela()
        close=self.mercado.velas[escala].valores_np_close()
        vemas=talib.EMA(close, timeperiod=14)
        l=vemas.size
        ema=vemas[l-1]

        if  uv.close >ema and uv.open<uv.close and uv.close > close[l-2]: 
            return True
        else:
            return False    
    def ema_minimos(self,escala,periodos):
        
        low=self.mercado.get_vector_np_low ( self.par,escala,periodos + 10 )
        vemas=talib.EMA(low, timeperiod=periodos)
        return vemas[vemas.size-1]

        def periodos_ema_minimos(self,escala,cvelas):
        '''
        busca los periodos para la ema de escala indicada
        en lo que los mínimos de las cvelas son superiores 
        a la ema de esos periodos
        '''
        periodos=9
        
        low=self.mercado.get_vector_np_low(escala)
        
        lx = low.size
        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1  

        while periodos < 100:
            vemas=talib.EMA(low, timeperiod=periodos)
            se_cumple=True
            for i in range(lx - 1, lx-cvelas-1,-1):
                #print(i,vemas[i] , low[i])
                if vemas[i] > low[i]:
                    se_cumple=False
                    break
            if se_cumple:
                break
            else:
                periodos += 1

        return periodos        


    def stoploss_ema_minimos(self,escala,cvelas,restar_velas=1):
        '''
        busca los periodos para la ema de escala indicada
        en lo que los mínimos de las cvelas son superiores 
        a la ema de esos periodos.
        En caso de no cumplir retorna el valor mas chico que encuentre de la ultima ema
        '''
        periodos=4
        
        low=self.mercado.get_vector_np_low(escala)
        
        lx = low.size
        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1  

        ret = self.precio_mas_actualizado()

        while periodos < 60:
            #print('periodos',periodos)
            vemas=talib.EMA(low, timeperiod=periodos)
            se_cumple=True
            primero = lx - 1 - cvelas - restar_velas
            ultimo = lx - 1 - restar_velas
            #print(primero,ultimo)
            for i in range( ultimo, primero ,-1):
                #print(i,vemas[i] , low[i])
                if vemas[i] > low[i]:
                    se_cumple=False
                    break
            if se_cumple:
                ret = float(vemas[vemas.size-1])
                break
            else:
                periodos += 1
                e = float(vemas[vemas.size-1])
                if e < ret:
                    ret = e

        #print('periodos',periodos) 
        #print(vemas)
        return  ret

def stoploss_emas_escalas_minimos(self,escala):
        '''busco la ema justo debajo del precio
           y retorno el precio de la ema de n periodos +10
        '''
        
        low=self.mercado.get_vector_np_low(escala)
        px = self.mercado.velas[escala].ultima_vela().close
        ret=-1
        periodos=10
        while periodos < 200:
            vemas=talib.EMA(low, timeperiod=periodos)
            e=vemas[vemas.size-1]
            print(px,e,periodos)
            if e < px:
                
                ret = vemas[vemas.size-1] - self.atr(escala)
                break
            periodos += 1

        return ret     


    #
    def precio_mayor_ultimas_emas(self,escala,periodos,cant_velas=1,porcentaje_mayor=0):
        '''
        retorna True si el precio es mayor que la la ema en las ultimas n velas
        escala = 1h 4h etc
        periodos = 9 10 25 200 etc
        cant_velas = cantidad de velas que el precio debe ser mayor a la ema
        '''
        
        precio=self.mercado.get_vector_np_close(escala)
        vemas=talib.EMA(precio, timeperiod=periodos)

        ret=True
        for  i in range(vemas.size-cant_velas,vemas.size):
            
            if precio[i] * (1+ porcentaje_mayor/100) < vemas[i]: #subo el precio un porcentje extra pra seguir comprando en esa ema
                ret=False
                break 
        return ret
    

  
    def compara_emas1(self,escala,periodos,cant_emas):
        ''' retorna un vector con la diferencias de la ema actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        
        close=self.mercado.velas[escala].valores_np_close()
        #print(close)
        vema=talib.EMA(close, timeperiod=periodos)
        l=vema.size
        ret=[]
        for i in range( l - cant_emas , l):
            #print(vema[i], vema[i-1],vema[i] - vema[i-1])
            diferencia = vema[i] - vema[i-1]
            ret.append( diferencia ) 
        return ret

    def compara_emas(self,escala,periodos,cant_emas):
        ''' retorna un vector con la diferencias de la ema actual
        menos la ema anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        
        close=self.mercado.velas[escala].valores_np_close(periodos * 3)
        #print (close)
        try:
            vema=talib.EMA(close, timeperiod=periodos)
            l=vema.size
            ret=[]
            for i in range( l - cant_emas , l):
                #print(vema[i], vema[i-1],vema[i] - vema[i-1])
                diferencia = vema[i] - vema[i-1]
                ret.append( diferencia ) 
        except:
            ret=[-1]        
        
        return ret

    def compara_adx(self,escala,cant):
        ''' retorna un vector con la diferencias de la adx actual
        menos el adx anterior. Si el valor es positivo, esta subiendo 
        y si es negativo esta bajando '''
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)
        v=talib.ADX(h,l, c, timeperiod=14)
        l=v.size

        ret=[]
        for i in range( l - cant , l):
            diferencia = v[i] - v[i-1]
            ret.append( diferencia ) 
        return ret    

   





    #busca que existan cpendientes con un coeficiente mayor al dado
    def pendientes_ema_mayores(self,escala,periodos,cpendientes,coeficiente):
        
        close=self.mercado.velas[escala].valores_np_close()
        vema=talib.EMA(close, timeperiod=periodos)
        l=vema.size-1
        unidad=vema[l-1]
        ret=True
        for i in range(l-cpendientes,l):
            
            m= round(   (vema[i] - vema[i-1]) /unidad ,8)
            
            if m < coeficiente:
                ret=False
                break
        return ret   

       



    def atr(self,escala,vela=0,cvelas=1):
        ret=0
        
        

        c=self.mercado.get_vector_np_close(self.par,escala)
        h=self.mercado.get_vector_np_high(self.par,escala)
        l=self.mercado.get_vector_np_low(self.par,escala)
        
        try:

            vatr = talib.ATR(h, l, c, timeperiod=14)
            
            v=vatr.size-1-vela
            if cvelas==1:
                ret=vatr[v]
            else:
                ret=vatr[v-cvelas+1:v+1]
        except:
            pass            
            
        
        return ret

    def hay_pump3(self,escala,cvelas,xatr=10,xvol=10):
        
        c=self.mercado.get_vector_np_close(self.par,escala)
        h=self.mercado.get_vector_np_high(self.par,escala)
        l=self.mercado.get_vector_np_low(self.par,escala)
        
        vvol=self.mercado.get_vector_np_volume(escala)

        vatr = talib.ATR(h, l, c, timeperiod=14)

        atr =self.atr_bajos(escala,100,200,0)
        vol =self.promedio_volumenes_bajos(escala,100,200,0)


        lx = vatr.size
        if cvelas > lx:
            cvelas = lx -1
        ret = False 
        for i in range(lx-cvelas,lx):
            if vvol[i]/vol > xvol or vatr[i]/atr > xatr:
                self.log.log('hay_pump3 escala',escala,'cvelas',cvelas,'i',i,'vvol[i]/vol',vvol[i]/vol, xvol ,'vatr[i]/atr', vatr[i]/atr , xatr )
                ret =True
                break

        return ret    

    def detectar_pumps(self,escala,cvelas,xatr=10,xvol=10):
        esc = escala
        ret = False
        while esc!='1w':
            if self.hay_pump3(esc,cvelas,xatr=10,xvol=10):
                ret = True
                break
            esc = self.g.escala_siguiente[esc]

        return ret    










            

    def vatr(self,escala,velas=5):
        

        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        vatr = talib.ATR(h, l, c, timeperiod=14)
        
        v=vatr.size - 1

        print (vatr)
        return vatr[ vatr.size - velas : vatr.size ]   


    def volumen_porcentajes(self,escala):

        
        vector=self.mercado.get_vector_np_volume(self.par,escala,50)

        vemavol=talib.EMA(vector, timeperiod=20)

        ret=[]
        for i in range(-10,0):
            ret.append(  round( vector[i]/vemavol[i] ,2)  )

        pend = self.pendientes('1m',vector,10)    

        return {'%':ret,'p':pend}




    def volumen_proyectado(self,escala):
        
        p=self.mercado.velas[escala].porcentaje_ultima_vela()
        v=self.mercado.velas[escala].ultima_vela().volume
        return round(  v/p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo

    def volumen_proyectado_moneda_contra(self,escala):
        
        p=self.mercado.velas[escala].porcentaje_ultima_vela()
        v=self.mercado.velas[escala].ultima_vela().volume
        precio = self.precio(escala)
        return round(  v * precio  /p,8) #al dividir por p obtengo un volumen proyectado ya que la vela está en desarrollo    
    
    def volumen_creciente(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return ( vc[l-3]<vc[l-2]  and vc[l-2]<vc[l-1] and vc[l-2]>0.9 and vc[l-1]>1 )


    def volumen_bueno5(self,escala,coef):
        
        vector_volumenes=self.mercado.velas[escala].valores_np_volume()
        vemavol=talib.EMA(vector_volumenes, timeperiod=20) #20 periodos es lo que usa tradingview por defecto para mostral el promedio del volumen
        ultima_vela=len(vector_volumenes)-1
        
        ret=( vector_volumenes[ultima_vela]   > vemavol[ultima_vela]   * coef or \
                 vector_volumenes[ultima_vela-1] > vemavol[ultima_vela-1] * coef   )
        return {'resultado':ret,'vol':[round(vector_volumenes[ultima_vela-1],2) , round(vector_volumenes[ultima_vela],2) ],'ema':[round(vemavol[ultima_vela-1],2) , round(vemavol[ultima_vela],2) ]  }

    def volumen_moneda_contra(self,escala): #entrega el volumen expresado en la moneda contra
        
        vector=self.mercado.velas[escala].valores_np_volume()
        precio=self.precio(escala)
        l=len(vector)
        
        if l >= 5:
            ini=l-5
        else:
            ini=l

        vol_mc=[]
        for i in range (ini,l):
            vol_mc.append(  self.redondear_unidades(  vector[i]*precio)  )

        return vol_mc     

    def volumen_sumado_moneda_contra(self,escala,velas=1): #entrega el volumen expresado en la moneda contra
        
        vector=self.mercado.velas[escala].valores_np_volume()
        precio=self.precio(escala)
        l=len(vector)
        
        if l >= velas:
            ini=l-velas
        else:
            ini=0

        volumen=0
        for i in range (ini,l):
            volumen +=  self.redondear_unidades(  vector[i]*precio) 

        return volumen       





    # volumen_bueno trata de detectar un aumento creciente del volumen donde la ultima vela cerrada debe tener al menos un incremento superior a un coeficiente pasado como parametro
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    # no tengo en cuenta la ultima vela puesto que está en desarrollo y como es proyectada, no es exacto el calculo
    def volumen_bueno(self,escala):  
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return ( vc[l-4]>self.incremento_volumen_bueno*0.3 and vc[l-4]>self.incremento_volumen_bueno*0.4 and vc[l-3]>self.incremento_volumen_bueno*0.5 and vc[l-2]>self.incremento_volumen_bueno ) 

    # volumen_bueno2v trata de detectar un aumento casi instantaneo teniendo solamente encuenta la última vela cerrada y la vela en desarrollo
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    def volumen_bueno2v(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        
        return  vc[l-2]>self.incremento_volumen_bueno*0.5 and vc[l-1]>self.incremento_volumen_bueno

    # volumen_bueno_ultima_v trata de detectar un aumento "instantaneo" ya que solo tiene en cuenta a la vela en desarrollo.
    # incremento_volumen_bueno: es el coeficiente de incremento, respecto del volumen promedio, que se considera suficientemente grande para inferir que el volumen actual el bueno
    def volumen_bueno_ultima_v(self,escala):
        vc=self.volumen_porcentajes(escala)
        l=len(vc)
        return  vc[l-1]>self.incremento_volumen_bueno
        
    
 def esta_subiendo15m(self):
        self.actualizar_velas('15m')
        
        vector=self.velas['15m'].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        

        return (r0<r1 and m0<m1 and self.volumen_mayor_al_promedio('15m'))  # rsi sube, momento sube, y hay volumen



    def esta_subiendo(self,escala):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        

        return (r0<r1 and m0<m1 and self.volumen_mayor_al_promedio(escala))  # rsi sube, momento sube, y hay volumen

    

    def esta_subiendo2(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
        uvela=self.mercado.velas[escala].ultima_vela()
        #self.log.log("Precios",escala,vector[vector.size-3],vector[vector.size-2],vector[vector.size-1])
        if uvela.open<uvela.close and ( (vector[vector.size-3]<=vector[vector.size-2] and  vector[vector.size-2]<=vector[vector.size-1] ) or vector[vector.size-3]<vector[vector.size-1]):
            return True
        else:     
            return False

    
    # def control_de_inconsistemcias(self,escala):
    #     self.log.log('ini inconsistencia',self.par)
    #     ifea = self.mercado.par_escala_ws_v[self.par][escala].inconsistencias()
    #     if ifea > -1:
    #         hora_fea = self.mercado.par_escala_ws_v[self.par].[escala].df.index[ifea]
    #         print('---> inconsitencai:',hora_fea)
    #         self.log.log('inconsistencia',self.par)
    #         self.actualizado[escala] = hora_fea /1000 -1
    #         self.carga_de_actualizacion_escala(escala)

    #     return ifea         

    # cuando el momentum pierde fuerza, la diferencia entre el momento actual y el aterior se hace cada vez mas chica
    # eso indica que la velocidad de subia está disminuyendo,la curva de aplana y muy posiblemente comience a bajar
    # entonces esta funciona de True cuando NO pierde fuerza.
    def mom_bueno(self,escala):
        
        vector=self.mercado.velas[escala].valores_np_close()
        vmom=talib.MOM(vector, timeperiod=10)


        if vmom[vmom.size-4]<vmom[vmom.size-1]: #Controla que el mom sea creciente

            # if vmom[vmom.size-4]!=0:  
            #    m3=round(vmom[vmom.size-3]/vmom[vmom.size-4],3)
            # else:
            #    m3=0

            # if vmom[vmom.size-3]!=0:  
            #    m2=round(vmom[vmom.size-2]/vmom[vmom.size-3],3)
            # else:
            #    m2=0
            
            # if vmom[vmom.size-2]!=0:  
            #    m1=round(vmom[vmom.size-1]/vmom[vmom.size-2],3)
            # else:
            #    m1=0   

            # self.log.log("Cociente MOMs",m3,m2,m1)

            # if m3<m2<m1: # controla que no sea deshacelerado
            #     return True
            # else:
            #     return False    
            return True
        else:
            #self.log.log("MOM no es creciente")
            return False


    
    def esta_bajando(self,escala):
        
        
        vector=self.mercado.velas[escala].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]
        
        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

      

        return (r1<r0 and m1<m0 )  # rsi sube, momento sube, y hay volumen
        
    def esta_lateral(self,escala):
        return (    not self.esta_subiendo(escala) and   not self.esta_bajando(escala)    )

    def tendencia(self):
        ten=0
        if self.ema('15m',25) < self.ema('15m',12): #la ema rápida es mayor que la lenta, está subiendo
            ten+=3
        if self.esta_subiendo('5m'):
            ten+=1
        if self.esta_subiendo('15m'):
            ten+=1
        if self.esta_subiendo('1h'):
            ten+=1
        if self.esta_subiendo('4h'):
            ten+=1
        if self.esta_subiendo('1d'):
            ten+=1    
        if self.esta_bajando('5m'):
            ten-=1
        if self.esta_bajando('15m'):
            ten-=1
        if self.esta_bajando('1h'):
            ten-=1
        if self.esta_bajando('4h'):
            ten-=1
        if self.esta_bajando('1d'):
            ten-=1    
        return ten    

   



    # def esta_subiendo(self,escala):
    #     self.actualizar_velas('15m')
        
    #     vector=self.velas15m.valores_np_close()
        
    #     vrsi=talib.RSI(vector, timeperiod=14)
    #     vmom=talib.MOM(vector, timeperiod=10)
        
    #     r1=vrsi[vrsi.size-1]
    #     r0=vrsi[vrsi.size-2]
        
    #     m1=vmom[vmom.size-1]
    #     m0=vmom[vmom.size-2]

    

    #     return (r0<r1 and m0<m1 and volumen_mayor_al_promedio('15m'))  # rsi sube, momento sube, y hay volumen    

    def esta_subiendo4h(self):

        if not self.la_ultima_vela_es_linda('4h'):
            return False
        
        vector=self.velas['4h'].valores_np_close()
        
        vrsi=talib.RSI(vector, timeperiod=14)
        vmom=talib.MOM(vector, timeperiod=10)
        
        r1=vrsi[vrsi.size-1]
        r0=vrsi[vrsi.size-2]

        m1=vmom[vmom.size-1]
        m0=vmom[vmom.size-2]

        #print "r0 r1 m0 m1",r0 ,r1 ,m0 ,m1

        return (r0<r1 and m0<m1) #el rsi subiendo y momento subiendo    

    def puntos_pivote(self,escala):
        

        vela=self.mercado.velas[escala].ultima_vela_cerrada()
        pp=( vela.high + vela.low + vela.close) / 3 # PP (P) = (H + L + C) / 3
        r2= pp + (vela.high - vela.low)
        r1= pp + (pp - vela.low)
        s1= pp - (vela.high - pp)
        s2= pp - (vela.high - vela.low)

        return [s2,s1,pp,r1,r2]

    def puntos_pivote_fibo(self,escala):
        
        vela=self.mercado.velas[escala].ultima_vela_cerrada()
        R = vela.high - vela.low
        PP = ( vela.high + vela.low + vela.close) / 3
        R1 = PP + (R * 0.382)
        R2 = PP + (R * 0.618)
        R3 = PP + (R * 1.000)
        R4 = PP + (R * 1.618)
        S1 = PP - (R * 0.382)
        S2 = PP - (R * 0.618)
        S3 = PP - (R * 1.000)
        S4 = PP - (R * 1.618)
        #print ([R4,R3,R2,R1,PP,S1,S2,S3,S4])
        return [R4,R3,R2,R1,PP,S1,S2,S3,S4]


    #detecta con respecto al precio actual si hay un movimiento (una diferencia porcentual del precio) > al coeficiente
    def __deprecated___movimiento(self,escala,cvelas,porcentaje):
        
        ot=self.mercado.velas[escala].ultima_vela().open_time
        o =self.mercado.velas[escala].ultima_vela().open
        h =self.mercado.velas[escala].ultima_vela().high
        l =self.mercado.velas[escala].ultima_vela().low
        c =self.mercado.velas[escala].ultima_vela().close  

      
        p=self.diff_porcentaje(o,h,l,c)

        #print (69,datetime.utcfromtimestamp(int(ot)/1000).strftime('%Y-%m-%d %H:%M:%S'),o,h,l,c,p)


        if ( abs(p) > porcentaje ):
            ret=[True,p,-1,ot]
        else:
            ret=[False,p,-1,'-']
            
            fin =len(self.mercado.velas[escala].velas)-2
            ini = fin - cvelas +1
            for i in range(fin,ini,-1):

                ot=self.mercado.velas[escala].velas[i].open_time
                o =self.mercado.velas[escala].velas[i].open
                h =self.mercado.velas[escala].velas[i].high
                l =self.mercado.velas[escala].velas[i].low
                
                
                #c = es el de la ultima vela que tenemos, para conpararlo con las velas enterirore

                q=self.diff_porcentaje(o,h,l,c)


                if (abs(q) > porcentaje ):
                    ret=[True,q,i,ot]
                    break
          
        return ret



    def bollinger(self,escala,periodos=20,desviacion_standard=2,velas_desde_fin=60):
        

        vc=self.mercado.get_vector_np_close(self.par,escala,velas_desde_fin+ 10) 
        #vc=self.mercado.velas[escala].valores_np_close(velas_desde_fin) # solo los ultimos <velas_desde_fin> elementos
        bs, bm, bi = talib.BBANDS(vc, timeperiod=periodos, nbdevup=desviacion_standard, nbdevdn=desviacion_standard, matype=0)

        return float(  bs[-1]  ),float(  bm[-1]  ),float(  bi[-1]  )
    

    #trata de determinar el precio donde hubo la menor volatilidad posible
    #entorno a un vela dada 
    #para ello saca la diferencia entre la banda superior y la inferior de bollinger
    #donde la diferencia es menor, tomamos el precio cierre redondeado como precio de rango
    def rango_por_bollinger(self,escala,velas_desde_fin):
        
        vc=self.mercado.velas[escala].valores_np_close() #vector close
        #vo=self.mercado.velas[escala].valores_np_open()  #vector open
        bs, bm, bi = talib.BBANDS(vc, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    
        ultimo= len(bs)-1 
        
        ini= ultimo -velas_desde_fin
        if ini<0:
           ini=0

        
        p= ultimo  
        diff_bb=bs[p]-bi[p]  # saco la diferencia entre la banda superior e inferior 
       
        for i in range(ultimo,ini,-1):
            diff_bb_i=bs[i]-bi[i]
            if diff_bb==0:
                pass
            if diff_bb_i < diff_bb:

                diff_bb=diff_bb_i
                p=i

        #p ahora debe tener la posicion donde las bandas de bollinguer son mas angostas
        #el valor de la bm de bollinguer determina el rango
          
        return (p,bm[p]/10000000)


    def atr_altos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top atr mas altos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        valores = talib.ATR(h, l, c, timeperiod=14)
        
        valores= valores[~np.isnan(valores)] #limpieza de nan

        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = valores.size
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=valores[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::-1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )    

def atr_bajos(self,escala,top=10,cvelas=None,restar_velas=0):
        ''' retorna un promedio de los top atr mas bajos
            top entre 2 y la maxima cantidad de velas
            memorizadas 
        '''    
        
        c=self.mercado.get_vector_np_close(escala)
        h=self.mercado.get_vector_np_high(escala)
        l=self.mercado.get_vector_np_low(escala)

        valores = talib.ATR(h, l, c, timeperiod=14)
        
        #correciones de entradas erroneas
        if top < 2:
            top = 2
        lx = valores.size
        if top > lx:
            top = lx -1

        if cvelas == None or cvelas > lx:
            cvelas=lx
        
        #sub array
        subset=valores[ lx-cvelas: lx - restar_velas]

        #print ('subset',subset)

        subset[::1].sort() #odenada de menor a Mayor

        #print ('subset ordenado',subset)

        #print ('top', subset[ 0 : top ] )

        return float( np.average(subset[ 0 : top ]) )
    
   
def rango_ema(self,escala,periodos,prango_max=2,cvelas=None):
        ''' retorna el rango_actual y el rango que no se supere el prango_max
            tambien retorna la vela donde se superó el rango o la ultima vela posible 
            siempre contando desde lo mas nuevo a lo mas viejo
        '''    
        
        vclose = self.mercado.velas[escala].valores_np_close()

        ema=talib.EMA(vclose, timeperiod=periodos)

        

        lx = ema.size

        if cvelas == None or cvelas > lx:
            cvelas=lx
        if cvelas < 1:
            cvelas = 1    

        #la ultima vela se descarta que es px y es al base del calculo del rango actual
        px = ema[lx-1]
        rango_actual=abs(round( (ema[lx-2] / px -1 ) * 100 ,2))



        #comienzo de busqueda de rango maximo
        prango= rango_actual
        # 
        for i in range(lx - 3, lx-1-cvelas,-1):
            
            irango= abs(round( (ema[i] / px -1) * 100 ,2))

            #print(i,prango)
            if irango > prango_max:
                break
            
            prango = irango # esta rango es bueno, me lo quedo
        
        vela = lx - 3 - i  # lx -1 - i-1

        return  rango_actual, prango, vela
    
 def cuatro_emas_ordenadas(self,escala,per1,per2,per3,per4):
        
        vector=self.mercado.get_vector_np_close(self.par,escala,per4+10)
        ema1=talib.EMA(vector, timeperiod=per1)[-1]
        ema2=talib.EMA(vector, timeperiod=per2)[-1]
        ret = False
        if ema1 > ema2:
            ema3=talib.EMA(vector, timeperiod=per3)[-1]
            if ema2 > ema3:
                ema4=talib.EMA(vector, timeperiod=per4)[-1]
                if ema3 > ema4:
                    ret = True
        return ret  
    
   def pendientes_ema(self,escala,periodos,cpendientes):
        
        ret=[]
        try:
            close=self.mercado.get_vector_np_close (self.par,escala,max(periodos,cpendientes) + 10 )
            vema=talib.EMA(close, timeperiod=periodos)
            l=vema.size-1
            unidad=vema[l-1]
            for i in range(l-cpendientes,l):
                m= round(   (vema[i] - vema[i-1]) /unidad ,8)
                ret.append(m) 
                #print(close[i],vema[i])
        except Exception as e: 
            self.log.err(str(e))       

        return ret          
                


                    
                    

                







          


