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


                


                    
                    

                







          


