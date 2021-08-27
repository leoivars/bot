from cola_de_uso import *
from variables_globales import VariablesEstado
from logger import *



log=Logger('Test_indicadores.log') 
e=VariablesEstado()

cola = Cola_de_uso(log,e)


for i in range(1,17):
   cola.acceso_pedir(str(i))

cola.acceso_pedir(str('------------------>YO'))
print(cola.mostrar_cola())

cola.acceso_esperar_mi_turno()

print(cola.mostrar_cola())
cola.acceso_finalizar_turno(1)
print(cola.mostrar_cola())

print('--------------------------------------------------------------------------------------------')

for i in range(1,5):
   cola.acceso_pedir('22222222'+str(i))

cola.acceso_pedir(str('---------222--------->YO'))
print(cola.mostrar_cola())

cola.acceso_esperar_mi_turno()
print(cola.mostrar_cola())

cola.acceso_finalizar_turno(1)
print(cola.mostrar_cola())



