# # -*- coding: UTF-8 -*-
import datetime
import time

class Logger:
    
    def __init__(self, nombrearchivolog=None,dirlogs="./logs/"):
        self.loguear= nombrearchivolog != None
        self.dirlogs = dirlogs
        self.nombrearchivolog = nombrearchivolog
        self.nlog=dirlogs+nombrearchivolog
        self.log_level=2
        self.__ultimas_lineas__=[]
        self.horario_actualizado=time.time()

    def __del__(self):
        for l in  self.__ultimas_lineas__:
            l = None
        del self.__ultimas_lineas__  
        self.horario_actualizado=time.time()  

    def set_log_level(self,log_level):
        self.log_level=log_level

    def log(self,*args):
        linea_log=self.__linealog__(' '.join([str(a) for a in args]))
        self.__logmem__(linea_log)
        if self.loguear and self.log_level > 1:
            self.__log_archivo__(linea_log)
        print(linea_log)

    def err(self,*args):
        linea_log=self.__linealog__(' '.join([str(a) for a in args]))
        self.__logmem__(linea_log)
        if self.loguear and self.log_level>0:
            self.__log_archivo__(linea_log)
        time.sleep(0.01)

    def tail(self): # entrega las ultimas líneas
        txt='últimas líneas del log:\n'
        for l in self.__ultimas_lineas__:
            txt+=l
        return txt
    
    def __linealog__(self,linea):
        if self.log_level < 1:
            a='*'
        else:
            a=' '
        return datetime.datetime.now().strftime('%m%d %H:%M') + a + linea+'\n'

    def __log_archivo__(self,linea_log):
        try:
            flog=open(self.nlog,'a')
            flog.write(linea_log)
            flog.close()
            time.sleep(0.01)
        except:
            print("no se pudo crear archivo log",self.nlog)
    
    def __logmem__(self,linea_log):
        self.horario_actualizado=time.time()
        self.__ultimas_lineas__.append(linea_log)
        if len(self.__ultimas_lineas__)==150:
            self.__ultimas_lineas__[0]=None
            self.__ultimas_lineas__.pop(0)  #elimina el primer elemento

    def tiempo_desde_ultima_actualizacion(self):
        return time.time() - self.horario_actualizado    
    
    def linea(self,*args):
        lin = ' '.join([str(a) for a in args])       
        lin += '\n'
        return lin 
