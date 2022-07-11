# # -*- coding: UTF-8 -*-

from logger import Logger


# import logging 
# logging.basicConfig(filename='./logs/auto_compra_vende.log',level=logging.DEBUG)


log=Logger('test_log.log') 

log.log('test 1')
log.err('test error')
log.loguear=False
log.log('esto no debe aparecer en el log')
log.err('error que sí debe aparecer')
print (log.tail())
