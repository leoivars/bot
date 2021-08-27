# # -*- coding: UTF-8 -*-
from threading import  Lock
import time
import random
import datetime

import datetime

class Ticket:
    def __init__(self,referencia,idx_cola):
        self.referencia = referencia
        self.tiempo_creacion = time.time()
        self.idx_cola = idx_cola

    def __str__(self):
        return self.referencia + '_' +  datetime.datetime.fromtimestamp(self.tiempo_creacion ).strftime('%Y-%m-%d %H:%M:%S.%f')
        



class Cola_de_uso:
    '''
    Mision: Administrar cola de acceso al cliente del exchange que no soporta
    muchas consultas simultanes y fracasa. 
    Entonces tratamos de ordenar el acceso en la medida de lo posible ya que esperar turno tiene
    una espera máxima y si no se cumple libera la espera igual
    27/6/2020 transformé a cola en multicola 
    los tickets se agregan a la cola que menos tickets tiene
    '''
    
    lock_cola= Lock()
    colas=[[],[],[]]
    idx_cola=0
    lista_demoras=[]
    demora_promedio=1

    def __init__(self,log,estado_general):
        self.log = log
        self.ticket_acceso=''
        self.estado_general = estado_general

    def largo(self):
        largo_total=0
        for c in Cola_de_uso.colas:
            largo_total += len(c)
        return largo_total  

    def tiempo_espera_total_estimado(self):
        return self.largo() * self.demora_promedio    

    def mostrar_cola(self):
        i=0
        todas_las_colas=""
        for cola in Cola_de_uso.colas:
            toda_la_cola="-------Cola["+str(i)+"]----------\n"
            for ti in cola:
                toda_la_cola += str(ti) + "\n"
            i +=1 
            todas_las_colas +=  toda_la_cola       
        return todas_las_colas

    def seleccionar_cola(self):
        #busca la cola con la menor cantidad de elementos
        idx=0
        l=len(Cola_de_uso.colas[0])
        for i in range(1, len(Cola_de_uso.colas)):
            li=len(Cola_de_uso.colas[i])
            if li <l:
                l=li
                idx=i
        return idx        

    def acceso_pedir(self,referencia='_',prioridad = 0):
            Cola_de_uso.lock_cola.acquire(True)
            idx=self.seleccionar_cola()
            self.ticket_acceso = Ticket( referencia,idx)
            try:
                if prioridad == 1:
                    Cola_de_uso.colas[idx].insert(0,self.ticket_acceso)
                elif prioridad == 2:
                    largo=len(Cola_de_uso.colas[idx])
                    if  11 <= largo < 20:
                        Cola_de_uso.colas[idx].insert(5,self.ticket_acceso)  
                    elif  21 <= largo < 50:
                        Cola_de_uso.colas[idx].insert(25,self.ticket_acceso)
                    elif  51 <= largo < 100:
                        Cola_de_uso.colas[idx].insert(50,self.ticket_acceso)
                    else:
                        Cola_de_uso.colas[idx].append(self.ticket_acceso)   
                else:    
                    Cola_de_uso.colas[idx].append(self.ticket_acceso)
            finally:
                pass        
            
            Cola_de_uso.lock_cola.release()

    def acceso_esperar_mi_turno(self):
            primero=''
            tprimero = 0
            idx = self.ticket_acceso.idx_cola
            esperar = True
            espera_random = random.randint(1,5) # un adicional de espera a espera_maxima de entre 1 y 5 segundos para disminuir la probabilidad de colisiones
            espera_maxima = espera_random + self.demora_de_cola() * len(Cola_de_uso.colas[idx]) * 1.1 # la espera máxima me asegura que nunca se quedará el par trabado
            inicio_espera = time.time()
            
            while esperar and time.time() - inicio_espera < espera_maxima and self.estado_general.trabajando:
                
                Cola_de_uso.lock_cola.acquire(True)   
                #self.motrar_cola()
                try:
                    #el primero se está demorando mucho?
                    if len(Cola_de_uso.colas[idx]) > 0 and primero != Cola_de_uso.colas[idx][0]:
                        primero = Cola_de_uso.colas[idx][0]
                        tprimero = time.time()
                        esperar_en_este_loop = False #no hago la espera al final del loop
                    else:
                        esperar_en_este_loop = True
                        demora = time.time() - tprimero
                        dpromedio=self.demora_de_cola()
                        if demora >  dpromedio * 1.1: #self.__tiempo_maximo_espera_cola:
                            print('Espera agotada',primero,'<-- borrado cola =',len(Cola_de_uso.colas[idx]),'demora_promedio',dpromedio,'demora',demora )
                            if len(Cola_de_uso.colas[idx]) > 0:
                                Cola_de_uso.colas[idx].pop(0)
                            else:    
                                esperar=False # la cola está vacia, no espero mas

                    if primero == self.ticket_acceso: #soy yo el primero, no espero mas
                        esperar=False
                finally:        
                    Cola_de_uso.lock_cola.release() 
                
                if esperar and esperar_en_este_loop: 
                    time.sleep( self.demora_de_cola() / 3 )        

    def acceso_finalizar_turno(self,demora):
        #retardo_extra = False
        Cola_de_uso.lock_cola.acquire(True)
        try:
            idx=self.ticket_acceso.idx_cola
            self.demora_de_cola(demora)     
            i=Cola_de_uso.colas[idx].index(self.ticket_acceso)
            Cola_de_uso.colas[idx].pop(i)
        except:
            pass
            #self.log.err('ERROR NO EXISTIA! acceso_finalizar_turno: ',self.ticket_acceso)
            #retardo_extra = True
            
        Cola_de_uso.lock_cola.release()

    def demora_de_cola(self,mi_demora=None):
        if mi_demora != None:
            Cola_de_uso.lista_demoras.append(round(mi_demora,4))
            if len(Cola_de_uso.lista_demoras) >30:
                Cola_de_uso.lista_demoras.pop(0)
            suma=0  
            for d in Cola_de_uso.lista_demoras:
                suma += d
            Cola_de_uso.demora_promedio=round(suma/len(Cola_de_uso.lista_demoras),4)        

        return Cola_de_uso.demora_promedio     
class Promediador_de_tiempos:
    
    lock_cola= Lock()
    lista_demoras=[]
    demora_promedio=0

    def __init__(self):
        pass
    
    def agregar_tiempo(self,tiempo):
        self.lock_cola.acquire(True)
        
        self.lista_demoras.append(tiempo)
        if len(self.lista_demoras) >50:
            self.lista_demoras.pop(0)
        suma=sum(self.lista_demoras)  
        self.demora_promedio=round( suma / len(self.lista_demoras) )        
        
        self.lock_cola.release()
               