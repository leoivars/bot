import sys
sys.path.append('..')   #agrego al path de python el directorio padre para que el import funcione

from variables_globales import Global_State

g = Global_State()

print (g.hay_pump)

