# # -*- coding: UTF-8 -*-
from funciones_utiles import linea
from threading import  Lock

class Metricas:
    __metricas = {}
    __lock_m   = Lock()

    #def __init__(self):
    #    pass

    #    self.referencia = referencia
    #    self.tiempo_creacion = time.time()
    #    self.idx_cola = idx_cola

    def __str__(self):
        ret = ''
        for m in self.__metricas:
            ret += linea(m,self.__metricas[m]) + '\n'
        return ret    
    
    def agregar(self,metrica,valor):
        self.__lock_m.acquire()
        
        if metrica in self.__metricas:
            self.__metricas[metrica].append(valor)
            if len(self.__metricas[metrica]) > 5:
                self.__metricas[metrica].pop()
        else:
            self.__metricas[metrica]=[valor]    
        
        self.__lock_m.release()

            

if __name__ =='__main__':
    from logger import *
    log=Logger('test_metricas.log') 
    metricas = Metricas()

    metricas.agregar('m1',11)
    metricas.agregar('m2',11)
    metricas.agregar('m3',11)
    metricas.agregar('m3',2)
    metricas.agregar('m1',11)
    metricas.agregar('m7',11)
    metricas.agregar('m8',11)
    metricas.agregar('m1',22)
    metricas.agregar('m1',33)
    metricas.agregar('m1',33)
    metricas.agregar('m1',44)
    metricas.agregar('m1',55)
    metricas.agregar('m1',66)
    
    print (metricas)

