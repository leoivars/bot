import time
class Datos_par:

    def __init__(self):
        self.actualizado={'1m':0,'5m':0,'15m':0,'30m':0,'1h':0,'2h':0,'4h':0,'1d':0,'1w':0,'1M':0}
        self.velas={} #diccionario de Velasets 
        ahora = time.time()
        for k in self.actualizado:
            self.actualizado[k]= ahora - 999999 #inicio con un valor que se considera desactualizado

    def set_velas(self,escala,velaset):
        if velaset is None:
            self.velas[escala] = None
            self.actualizado[escala] = time.time() -999999
        else:
            self.velas[escala] = velaset
            self.actualizado[escala] = time.time()

