import time

class Error_recuperable:

    def __init__(self,log,tiempo_reset):
        self.log = log
        self.tiempo_reset = tiempo_reset
        self.suma_errores_recuperables = 0
        self.tiempo_ultimo_error_recuperable = time.time() - self.tiempo_reset

    def sumar(self,txt_error):
        ''' acumula 1 error por cada llamada pero si hace mas de una hora que no se han producido errores recuperables
            reseta el contador 
            La idea es intenter recuperarse de un error , pero si se producen muchos en poco tiempo la cuestión se torna 
            crítica y hay que tomar otras acciones
        '''
        if self.tiempo_ultimo_error_recuperable - time.time() > self.tiempo_reset:
            self.suma_errores_recuperables =0
            
        self.suma_errores_recuperables +=1
        self.tiempo_ultimo_error_recuperable = time.time()
        self.log.err(txt_error)
        return self.suma_errores_recuperables
