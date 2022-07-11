# # -*- coding: UTF-8 -*-
#from binance.enums import * #para  create_order
import sys
import time
from termcolor import colored


class LibroOrdenes:

    client=''
    libro=''
    cant_grupos=0
    par=''
    asks='' # los que queiren vender a un precio x
    bids='' # los que quieren comprar a un precio x
    tot={}
    tot['bids']=0
    tot['asks']=0
    grupo_imax={}
    grupo_imax['bids']=0
    grupo_imax['asks']=0
    momento_ultima_actuazacion=0

    def __init__(self, client,moneda,moneda_contra,cant_grupos): 
        self.client=client
        self.cant_grupos=cant_grupos
        self.par=moneda+moneda_contra 

    def actualizar(self):
        ahora=time.time()
        if ahora-self.momento_ultima_actuazacion<10:
            #se considera actualizado
            return
          
        # get market depth
        libro_oficial=None
        while True:
            try:
                libro_oficial = self.client.get_order_book(symbol=self.par, limit=1000)
                break
            except Exception as e:
                print  ('client.get_order_book',self.par,'espero 15s')
                time.sleep(15)
         
        #grupo de bids, quiern comprar a x 
        self.asks=self.agrupar('asks',libro_oficial)
        #grupo de asks, quieren vender a x
        self.bids=self.agrupar('bids',libro_oficial)
        self.momento_ultima_actuazacion=ahora
            
        #print (max_bids[0][2]/max_asks[0][2]*100,"%")    
        #return ( float(depth['bids'][0][0])  )# el primer precio de los bids
  

    def agrupar(self,cod,oderbook): #cod c oferta demanda,  cantidad de grupos
        filas_grupo=int(len(oderbook[cod])/self.cant_grupos)
        ifila=1 
        igrupo=0
        grupos=[]
        total=0
        for pxs in oderbook[cod]:
            subtotal=self.pxc(pxs)
            total+=subtotal
            if (ifila==1):
                grupos.append([pxs[0],'',subtotal])# pxini,nada, subtotal
            else:
                grupos[igrupo][2]+=subtotal #agrego al subtotal
            ifila+=1    
            if (ifila==filas_grupo):
                grupos[igrupo][1]=pxs[0] #pxfin 
                ifila=1
                igrupo+=1
        if (ifila != filas_grupo and ifila!=1): #agrego ultima fila suelta
            grupos[igrupo][1]=pxs[0] #pxfin 
                #grupos[igrupo][1]=oderbook[cod][len(oderbook[cod])][0] #pxfin

        self.tot[cod]=total#guardo el total         

        #nuevo grupo con los porcentajes y acumulados    
        #y el mayor
        grupos1=[] 
        mayor=0
        imayor=0
        porce_acum=0
        for i in range (len(grupos)):
            g=grupos[i]
            p=g[2]/total * 100
            porce_acum+=p

            grupos1.append([g[0],g[1],g[2],p,porce_acum,False])
            #ahora comparo y guardo el mayor y la posicion        
            if mayor<g[2]:
               mayor=g[2]
               imayor=i 
        grupos1[imayor][5]=True #verdadero para el elemento mayor
        self.grupo_imax[cod]=[imayor] # guardo la posicion del maximo
      
        return grupos1  

    def tot_compran_venden(self):  
        self.actualizar()  
        return [ self.tot['bids'],self.tot['asks'], ]

    def g1_compran_venden(self):  
        self.actualizar()  
        return [ self.tot['bids']*self.bids[0][3]/100 , self.tot['asks']*self.asks[0][3]/100 ]
    
    def relacion_compra_venta(self):
        rel=-1

        try:
            tc=self.tot['bids'] #total de presion compradora
            tv=self.tot['asks'] #total de presion vendedora
            gc=self.tot['bids']*self.bids[0][3]/100 #subtotal de presion compradora en el primer grupo
            gv=self.tot['asks']*self.asks[0][3]/100 #subtotal de presion vendedora en el primer grupo
            
            if tc > tv    and gc > gv * 10:
                rel=6
            elif  tc < tv and gc > gv * 10:
                rel=5
            elif  tc > tv and gc > gv * 2:   
                rel=4
            elif  tc < tv and gc > gv * 2:
                rel=3
            elif  tc > tv and gc > gv:     
                rel=2
            elif  tc < tv and gc > gv:
                rel=1
            elif  tc < tv and gc < gv:    
                rel=0

        except Exception as e:
                print  ('relacion_compra_venta')
                #time.sleep(15)        

        return rel    


    def pxc(self,pxs):
        return float(pxs[0])*float(pxs[1])

    def imprimir(self):
        
        self.printgrpinversa(self.asks)
        print ("--/\Oferta/\ --",self.par,"-- \/Pedidos\/" )
        self.printgrp(self.bids)
        print ("------------------------------------------")
        
   
    def dump_libro(self):
        ret = ''
        ret += self.log_grpinversa(self.asks)
        ret += self.linea ("--/\Oferta/\ --",self.par,"-- \/Pedidos\/" )
        ret += self.log_grp(self.bids)
        print ("------------------------------------------")
        ret += self.linea('grupo_mayor',self.precio_compra_grupo_mayor())
        return ret
       

    def mejor_precio_compra(self):
        ''' es el segundo precio al que se puede colocar
        una orden de compra de los grupos de precios captados por el libro 
        eventualmente se ejecutará pero no es seguro, se puede demorar
        '''
        self.actualizar()
        p=self.grupo_imax['bids'][0]
        if p>0: #tomo siempre el precio de arriba salvo que sea el primero
           p-=1
        return float(self.bids[p][1])

    def primer_precio_compra(self):
        ''' es el precio al que se puede poner y orden de compra 
        con alta probabilidad de que sea ejecutada '''
        self.actualizar()
        return float(self.bids[0][0])       

    def ultimo_precio_compra(self):
        ''' precio mas bajo registrado en el libro de ordenes
        ofreciendo comprar '''
        self.actualizar()
        return float(self.bids[len(self.bids)-1][1])    

    def mejor_precio_venta(self):
        self.actualizar()
        p=self.grupo_imax['asks'][0]
        if p>0: #tomo siempre el precio de arriba salvo que sea el primero
           p-=1
        return float(self.asks[p][1])

    def primer_precio_venta(self):
        self.actualizar()
        return float(self.asks[0][0])

    def segundo_precio_venta(self):
        self.actualizar()
        return float(self.asks[0][1])    

    def segundo_precio_compra(self):
        self.actualizar()
        return float(self.bids[0][1])    
    

    def stoploss_con_resistencia(self):
        self.actualizar()
        p=self.grupo_imax['bids'][0]
        if p<self.cant_grupos: #tomo siempre el precio de arriba( o es el de abajo? //todo:"repensar este comentario") salvo que sea el primero
           p+=1
        return float(self.bids[p][1])/1.01

    def precio_compra_grupo_porc_acumulado(self,porcenteja_acumulado):
        self.actualizar()
        ret=0
        for g in (self.bids):
            if g[4]>porcenteja_acumulado:
                ret=float(g[1])
                break
        return ret        
            
    def calculo_porcentaje_stoploss_con_resistencia(self,porcentaje_resistencia_libro):
        self.actualizar()

        ret=(1-self.precio_compra_grupo_porc_acumulado(porcentaje_resistencia_libro)/self.precio_compra())*100
        #print 'calculo_porcentaje_stoploss_con_resistencia=',ret
        return ret
           
    def precio_compra(self):
        self.actualizar()
        return float(self.bids[0][0])


    
    def precio_compra_grupo_mayor_inicio(self):
        ''' es el precio mas alto del grupo que mayor porcentaje de ordenes, podria
        considerarse a este precio el principio de una pardes de ordenes '''
        self.actualizar()
        ret=0
        for g in (self.bids):
            if g[5]: #si es el mayor
                ret=float(g[0])
        return ret  

    def precio_compra_grupo_mayor(self):
        ''' es el precio mas bajo del grupo que mayor porcentaje de ordenes, es un precio en el que
        si se ejecuta la orden, debería haber un rebote '''
        self.actualizar()
        ret=0
        for g in (self.bids):
            if g[5]: #si es el mayor
                ret=float(g[1])
        return ret        
               
    
    def printgrp(self,grupos):  
        for g in (grupos):
            if g[5]: #si es el mayor
                print (self.c1(g[0]),self.c1(g[1]),self.c2(g[2]),'\t',self.c2(g[3]),'\t',self.c2(g[4]))
            else:
                print (g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4])
                    
    def printgrpinversa(self,grupos):
        for g in reversed(grupos):
            if g[5]: #si es el mayor
                print (self.c1(g[0]),self.c1(g[1]),self.c2(g[2]),'\t',self.c2(g[3]),'\t',self.c2(g[4]))
            else:
                print ( g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4])

    def log_grp(self,grupos):  
        ret = ''
        for g in (grupos):
            if g[5]: #si es el mayor
                ret+= self.linea (g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4],'**\n')
            else:
                ret+= self.linea (g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4],'\n')
        return ret        
                    
    def log_grpinversa(self,grupos):
        ret = ''
        for g in reversed(grupos):
            if g[5]: #si es el mayor
                ret+= self.linea ( g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4],'**\n')
            else:
                ret+= self.linea ( g[0],g[1],"%.2f" % g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4],'\n')
        
        return ret        
            
    
    def c2(self,dato): #formatea un float y lo colorea
        return colored("%.2f" % dato,'cyan', attrs=['bold'])

    def c1(self,dato): #foratea una dato y lo colorea
        return colored( dato,'blue', attrs=['bold'])

    
    def txtbids(self):
        return self.txtgrp(self.bids)

    def txtgrp(self,grupos):
        txt=''  
        for g in (grupos):
            txt+=self.linea (g[0], g[1], g[2],'\t',"%.2f" % g[3],'\t',"%.2f" % g[4])
            if g[5]: #si es el mayor
                txt+="#"
            txt+= '\n'
        return txt    
    
    def linea(self,*args):
        return  ' '.join([str(a) for a in args])                


    