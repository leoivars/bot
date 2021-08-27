from cola_de_uso import Promediador_de_tiempos
import random


pt = Promediador_de_tiempos()


for i in range(1,100):
   pt.agregar_tiempo(random.randint(1,200) )
   print (pt.demora_promedio,len(pt.lista_demoras))




