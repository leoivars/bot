# # -*- coding: UTF-8 -*-
import time
import sys
from binance.websockets import BinanceSocketManager
from binance.client import Client
from pws import Pws



from twisted.internet import reactor

#trataré de hacer el lector de precios con websockets, no est'a terminaod eso


class LectorPrecios:
    cantidad_de_muestras=50
    operando=False
    precios={}

    def __init__(self, log): 
        
        self.log=log 
        
        self.client = None
        self.crear_cliente()


        self.bm=BinanceSocketManager(self.client)
        
        


    def crear_cliente(self):
        if self.client != None:
            self.log.err( "Re creando Cliente")
            time.sleep(35)
            self.client = None
            del self.client 
        pws=Pws()
        while True:
            try:
                self.client= Client(pws.api_key, pws.api_secret, { "timeout": (10, 27)})  #timeout=(3.05, 27
                break
            except Exception as e:
                time.sleep(35)
                self.log.err( "XXX No se puede crear Cliente",str(e))
                self.client = None
                del self.client     

    def empezar(self):
        
        self.conn_key = self.bm.start_miniticker_socket(self.process_message,3000)
        print('empezar',str(self.conn_key))
        self.bm.start()

    def detener(self):
        print ('xxx detener')
        self.bm.stop_socket(self.conn_key)
        self.bm.close()
        #reactor.stop()
        
        
        
    def cerrar(self): # esto se usa al final del programa para que libere todos los recursos
        pass
        #reactor.stop_socket()



    def process_message(self,msg):
        #print("message type: {}".format(msg['e']))
        print ('---> recibiendo')
        #print(msg)
        
        self.agregar_precios(msg)
        self.pendientes('RCNBTC')
        self.pendientes('RCNBTC')
        print ('RCNBTC No baja =', self.precio_no_baja('RCNBTC') )
        self.pendientes('WANBTC')
        print ('WANBTC No baja =', self.precio_no_baja('WANBTC') )


        try:
            if msg['e'] == 'error':
                print ('---> error',msg)
        except Exception as e:
            pass        

    
    def pendientes(self,simbol):
        if simbol in LectorPrecios.precios:
            pxs = LectorPrecios.precios[simbol]
            print (pxs)
            pultimo = len( pxs ) - 1
            if pultimo > 1:
                vultimo = pxs[ pultimo ]
                print ('Pendientes',simbol)
                for i in range(0,pultimo):
                    dy = vultimo[0] - pxs[i][0]
                    dx = vultimo[1] - pxs[i][1] 
                    #print('dy',dy,vultimo[0] , pxs[i][0])
                    #print('dx',dx,vultimo[1] , pxs[i][1] )

                    print (pxs[i][0],vultimo[0],  dy / dx     )    


    def imprimir(self,msg):
        print('imprimir')
        for k in msg:
            if k["s"]=='BTCUSDT':
                for i in k.keys():
                    print(i,'----->',k[i])


        #else:
            # process message normally

        #print('--------->',msg)
    # do something

    def agregar_precios(self,msg):
        for p in msg:
            simbol = p["s"]
            precio = [   float(p["c"]) ,  int(p["E"])  ]
            if simbol in LectorPrecios.precios:
                LectorPrecios.precios[simbol].append(precio)
                if len( LectorPrecios.precios[simbol] ) > 10:
                    LectorPrecios.precios[simbol].pop(0)

            else:
                LectorPrecios.precios[simbol]=[ precio ] 


    def precio_no_baja(self,simbol):
        '''retorna true si el precio no baja 
           monitoreado a partir de 5 pendientes frescas
        ''' 
        ret = False
        if simbol in LectorPrecios.precios:
            pxs = LectorPrecios.precios[simbol]
            pf=self.calcular_pendientes_frescas(pxs)
            if len( pf ) > 0:
                cant_pend_ok =0
                for p in reversed(pf):
                    if p >= 0:
                        cant_pend_ok += 1
                        if cant_pend_ok >=5:
                            ret = True
                            break
                    else:
                        ret = False
                        break

        return ret                





    def calcular_pendientes_frescas(self,pxs):
        pultimo = len( pxs ) - 1
        pendientes_frescas=[]
        if pultimo > 1:
            vultimo = pxs[ pultimo ]
            antiguedad =  time.time() - vultimo[1]/1000
            print("antiguedad",antiguedad)
            if  antiguedad< 15:
                print ('Pendientes')
                for i in range(0,pultimo):
                    dy = vultimo[0] - pxs[i][0] 
                    dx = vultimo[1] - pxs[i][1] 
                    pendientes_frescas.append(  dy / dx )
        return pendientes_frescas            






    def imp_precios(self,simbol):
        print('precios de ',simbol)
        if simbol in LectorPrecios.precios: 
            for p in LectorPrecios.precios[simbol]:
                print(p)
        
    def tomar_precios_de_pares(self):
        for p in (self.pares):
            muestras=len(p[1])
            if muestras>self.cantidad_de_muestras: # elimino primer muestra para mantener una cantidad razonable
                p[1].pop(0)
            #print p[0]    
            p[1].append(self.tomar_precio(p[0])) # tomo el precio del par


    def tomar_precio(self,par):
        precio=-1    
        for px in (self.precios):
            if px['symbol']==par:
                precio=float(px['price'])
                break
        return precio

        

    def  valor_usdt(self, cantidad,par):

        pxpar=self.tomar_precio(par)
        if par.endswith('USDT'):
            px=1
        elif par.endswith('BTC'):
            px=self.tomar_precio('BTCUSDT')
        elif par.endswith('BNB'):    
            px=self.tomar_precio('BNBUSDT')
        elif par.endswith('ETH'):    
            px=self.tomar_precio('ETHUSDT')
 
        return cantidad*pxpar*px    

    def  valor_btc(self, cantidad,par):

        pxpar=self.tomar_precio(par)
        if par.endswith('BTC'):
            px=1
        elif par.endswith('USDT'):
            px=1/self.tomar_precio('BTCUSDT')
        elif par.endswith('BNB'):    
            px=self.tomar_precio('BNBBTC')
        elif par.endswith('ETH'):    
            px=self.tomar_precio('ETHBTC')

        return cantidad*pxpar*px    




    def usdt_cantidad(self,monto,par):
        pxunidad=self.valor_usdt(1,par)
        cant=self.redondear_unidades(monto/pxunidad)
        return cant 

    def unidades_posibles(self,cant_en_moneda_contra,par):
        pxpar=self.tomar_precio(par)
        unidades=self.redondear_unidades(cant_en_moneda_contra/pxpar)
        return unidades

    def redondear_unidades(self,unidades):
        cant=unidades
        if  0 < cant <1:
            cant=round(cant,4)
        elif 1 <= cant <9:
            cant=round(cant,2)
        else:
           cant=int(cant)
        return cant   

    
    # def imprimir_promedios(self):
    #     for p in (self.pares):
    #         print "Par:", p[0],"Promedio:",self.promedio(p[1])

    def promedio(self,muestras):
        suma=0
        for m in (muestras):
            suma+=m
        return suma / len (muestras)        
        
