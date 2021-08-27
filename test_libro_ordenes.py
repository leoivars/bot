from indicadores2 import *
from logger import *
import time
from LibroOrdenes import *



from pws import Pws
from binance.client import Client # Cliente python para acceso al exchangue

log=Logger('test_libro_ordenes.log') 

pws=Pws()
client = Client(pws.api_key, pws.api_secret)

libro=LibroOrdenes(client,'AMB','BTC',25)



#j=Indicadores('NASBTC',client,log)

#i=Indicadores('GVTBTC',client,log)


while True:
    #print 'BTCUSDT  4h 1h 15m 5m 1m' , b.analisis('4h' ,1.2), b.analisis('1h' ,1.3), b.analisis('15m',1.4), b.analisis('5m' ,1.5), b.analisis('1m' ,1.6), 'GVTBTC   4h 1h 15m 5m 1m' , i.analisis('4h' ,1.2), i.analisis('1h' ,1.3), i.analisis('15m',1.4), i.analisis('5m' ,1.5), i.analisis('1m' ,1.6)
    libro.actualizar()
    print ('mejor_precio_compra',libro.mejor_precio_compra())
    print ('primer_precio_compra',libro.primer_precio_compra())
    print ('ultimo_precio_compra',libro.ultimo_precio_compra())
    print ('precio_compra_grupo_mayor',libro.precio_compra_grupo_mayor())
    
    libro.imprimir()
    
    print ("")
    

    # plt.plot(bb[2],'r--')
    # plt.plot(bb[3],'r')
    # plt.plot(bb[4],'r')
    # plt.plot(bb[5],'g')
    # plt.plot(bb[6],'b')
    # plt.show()
    

   # print (i.par,'contar_resistencias      1h ', i.contar_resistencias('1h',0.5,10) )
   # print (i.par,'contar_resistencias      4h ', i.contar_resistencias('4h',0.5,10)   )      
    print ('--')
    time.sleep(5)
    
