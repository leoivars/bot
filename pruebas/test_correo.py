# # -*- coding: UTF-8 -*-

import sys
sys.path.append('..')  

from correo import Correo
from logger import Logger

log = Logger('Test_correo')
correo=Correo(log)
print('contraseña',correo.password)
correo.enviar_correo('Test','Esta es una prueba\n de correo.')