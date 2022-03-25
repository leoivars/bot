from controlador_de_tiempo import Controlador_De_Tiempo
import time

i = 900

ct=Controlador_De_Tiempo(10)
while i > 0:
    print (ct.tiempo_cumplido())
    time.sleep(1)