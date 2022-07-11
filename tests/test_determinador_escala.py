import os
import sys
from pathlib import Path
sys.path.append(str(Path('..').absolute().parent))          #para que se pueda usar app. como mudulo
sys.path.append(str(Path('..').absolute().parent)+"/app")   #para que los modulos dentro de app encuent

from app.fpar.determinador_escalala  import *

print ( determinar_escala(12.5,15,'5m',100))