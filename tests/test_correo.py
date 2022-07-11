# # -*- coding: UTF-8 -*-

import os
import sys
from pathlib import Path
sys.path.append(str(Path('..').absolute().parent))          #para que se pueda usar app. como mudulo
sys.path.append(str(Path('..').absolute().parent)+"/app")   #para que los modulos dentro de app encuentren a otros modulos dentro de su mismo directorio

# print ('------------------getcwd()----->', os.getcwd())
# print ('----------------__file__------->', __file__)
# print ('---------------DIR_LOGS-------->', os.getenv('DIR_LOGS', '????'))
# print ('---------------CONFIG_FILE----->', os.getenv('CONFIG_FILE', '????'))

from app.correo import Correo
from app.logger import Logger

log = Logger('Test_correo')
correo=Correo(log)
correo.enviar_correo('Test','Esta es una prueba\n de correo.')