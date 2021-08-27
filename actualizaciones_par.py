import datetime

class ActualizacionesWS:

    def __init__(self):
        self.actualizaciones = [0]
        self.hora_actualizacion = datetime.datetime.now().hour
        #self.hora_actualizacion = datetime.datetime.now().minute
        self.max_actualizaciones = 5


    def sumar_actualizacion(self):
        hora = datetime.datetime.now().hour
        #hora = datetime.datetime.now().minute
        if hora == self.hora_actualizacion:
            self.actualizaciones[-1] += 1
        else: # hay hora nueva
            self.hora_actualizacion = hora
            self.actualizaciones.append(1) 
            if len(self.actualizaciones) > self.max_actualizaciones:
                self.actualizaciones.pop(0)

                





