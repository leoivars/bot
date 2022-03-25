# # -*- coding: UTF-8 -*-
from correo import Correo
from logger import Logger

log = Logger('Test_correo')
correo=Correo(log)
correo.enviar_correo('Test','Esta es una prueba\n de correo.')