import os
import sys
from pathlib import Path
sys.path.append(str(Path('..').absolute().parent))          #para que se pueda usar app. como mudulo
sys.path.append(str(Path('..').absolute().parent)+"/app")   #para que los modulos dentro de app encuent

from app.escalas import *

for x in range(1,10):
    print(f'--------------  {x}  ------------------')
    for e in escala_tiempo:
       print (f'{zoom(e,x)}   <--- {e}  -->  {zoom_out(e,x)}')
