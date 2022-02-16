import mailbox
from mercado import Mercado
from indicadores2 import Indicadores
from logger import *
import time
from pws import Pws
from binance.client import Client #para el cliente
from numpy import isnan
from par_propiedades import Par_Propiedades
from variables_globales import VariablesEstado
from  formateadores import format_valor_truncando
from acceso_db import Acceso_DB
from acceso_db_conexion import Conexion_DB
from vela import Vela
#from gestor_de_posicion import Gestor_de_Posicion

pws=Pws()

client = Client(pws.api_key, pws.api_secret)

log=Logger('Test_indicadores.log') 

#apertura del pull de conexiones
conn=Conexion_DB(log)
#objeto de acceso a datos
db=Acceso_DB(log,conn.pool)
#gestor_de_posicion = Gestor_de_Posicion(log,client,conn)
globales = VariablesEstado()
mercado = Mercado(log,globales,client)


monedas=['XTZ','EDO','BRD','VITE','OGN','AION','GO','GRS','BQX','ALGO','RDN']

primeras_monedas=['PNT','ETH','XRP','LTC','EOS','BNB','XTZ','LINK','ADA','XLM','XMR' \
                 ,'TRX','ETC','DASH','NEO','ATOM','IOTA','ZEC','XEM','ONT','BAT'\
                 ,'DOGE','FTT','QTUM','ALGO','DCR'  ,'LSK'  ]

#pares=['LSKBTC','PIVXBTC','CELRBTC','EDOBTC']

#pares=['ETHBTC','EDOBTC','ATOMBTC']
escala_prango = {'1m':1 ,'5m':1.5 ,'15m':2,'30m':2.5,'1h':2.7,'2h':2.9,'4h':3,'1d':4,'1w':5,'1M':6}




monedas_ahora =['FTM','QLC','ZIL','STRAT']
#pares=['APPCBTC','NAVBTC','NAVBTC','POWRBTC','BATBTC','BQXBTC','GVTBTC','RCNBTC','BTCUSDT']
#pares=['BTCUSDT','PNTBTC','RLCBTC']
pares=['AGIBTC','YOYOBTC','XRPBTC']
#for m in primeras_monedas:
#    pares.append(m+'BTC')

def calculo_ganancias(pxcompra,pxventa,fee = 0.001):  #esta es la funcion definitiva a la que se tienen que remitir el resto.
    comision=pxcompra * fee
    comision+=pxventa * fee
    gan=pxventa - pxcompra - comision #- self.tickSize
    return round(gan/pxcompra*100,3) 

def probar(par):
    prop=Par_Propiedades(par,client,log)
    ind=Indicadores(par,log,globales,client)
    atr=ind.atr('1d')
    escala='1d'
    atr1=ind.atr(escala,0,3)
    resultado=ind.atr_altos(escala,top=5)

    
    print(par,format_valor_truncando(resultado,prop.moneda_precision ),format_valor_truncando(atr,prop.moneda_precision )  )
    
    for a in atr1:
        print(a/resultado)



def probar_divergencia(par):
   
    prop=Par_Propiedades(par,client,log)
    ind=Indicadores(par,log,globales,client)
    resultado=ind.divergenica_macd('1d')
    
    print(par,resultado  )    


def probar_rsi(par):
    
    prop=Par_Propiedades(par,client,log)
    ind=Indicadores(par,log,globales,client)
    
    for esc in ['1M','1w','1d','4h']:
        resultado=ind.rsi(esc)
        print(par,resultado  ) 

def probar_adx(par):
    
    prop=Par_Propiedades(par,client,log)
    ind=Indicadores(par,log,globales,client)
    
    for esc in ['1d','4h']:
        resultado=ind.adx(esc)
        print(par,esc,resultado  ) 


def probar_compara_adx_emas(par):
    
    prop=Par_Propiedades(par,client,log)
    ind=Indicadores(par,log,globales,client)
    
    for esc in ['1d','4h']:
        adx=ind.compara_adx(esc,3)
        ema=ind.compara_emas(esc,55,3)
        ok=True
        for i in range(0,3):
            if adx[i]<=0 or ema[i]<0:
                ok=False
                break


        print(par,esc,adx,ema,ok ) 

def probar_hay_pump3(par):
    ind=Indicadores(par,log,globales,client)
    print ( par, ind.hay_pump3('15m',5,10,10))


def rsi_menos_20(par):
    ind=Indicadores(par,log,globales,client)
    print('calculo el rsi')
    rsi=ind.rsi('1d')
    print('calculo el px')
    px=ind.precio_de_rsi('1d',rsi-20)

    print('precio_rsi-20',rsi,px )
    


def probar_macd_describir(par,escala):
    ind=Indicadores(par,log,globales,client)
    result = ind.macd_describir(escala)
    adx = ind.compara_adx(escala,3)
    ema = ind.compara_emas(escala,55,3)
    
    
    
    print(par,escala,result,adx,ema)

def probar_buscar_la_vela_mas_grande(par,escala,velas):
    ind=Indicadores(par,log,globales,client)
    result = ind.buscar_la_vela_mas_grande(escala,velas)
    print(par,escala,result)    


def probar_volumen_sumado_moneda_contra(par,escala):
    ind=Indicadores(par,log,globales,client)
    for v in range(1,10):
        result = ind.volumen_sumado_moneda_contra(escala,v)
        print(par,escala,v,result)    

def probar_adxs(par,escala): 
    ind=Indicadores(par,log,globales,client)
    a = ind.adx(escala)
    b = ind.adx_mr(escala)
    print(par,escala,'adx',a,'adx_mr',b)  


def probar_busca_principio_macd_hist_min(par,escala): 
    ind=Indicadores(par,log,globales,client)
    m = ind.busca_principio_macd_hist_min(escala)
    print(par,escala,m)  

def probar_busca_macd_hist_min(par,escala): 
    ind=Indicadores(par,log,globales,client)
    m = ind.busca_macd_hist_min(escala)
    print(par,escala,m)  

def probar_patron_180(par,escala,vela_ini): 
    ind=Indicadores(par,log,globales,client)
    p = ind.patron_180(escala,vela_ini)
    if p > 0:
        print(par,escala,vela_ini,p)
def probar_patron_rebote_macd(par,escala,vela_ini): 
    ind=Indicadores(par,log,globales,client)
    p = ind.patron_rebote_macd(escala,vela_ini)
    if p > 0:
        print(par,escala,vela_ini,p)

def probar_patron_seguidilla_negativa_rebote_macd(par,escala,vela_ini): 
    ind=Indicadores(par,log,globales,client)
    p = ind.patron_seguidilla_negativa_rebote_macd(escala,vela_ini)
    if p > 0:
        print(par,escala,vela_ini,p)

def probar_pendientes_ema(par,escala,periodos,cpen):
    ind=Indicadores(par,log,globales,client)
    pendientes = ind.pendientes_ema(escala,periodos,cpen)
    print(par,pendientes)
    imprimir=0
    for p in pendientes:
        if abs(p)<0.0005:
            imprimir += 1
    if imprimir ==cpen:        
        print('horizontal',par,escala,periodos,pendientes)

    imprimir=0
    for p in pendientes:
        if p>0:
            imprimir += 1
    if imprimir ==cpen:        
        print('positiva',par,escala,periodos,pendientes)
    
def probar_promedio_de_maxmin_velas_negativas(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.promedio_de_maxmin_velas_negativas(escala,top=10,cvelas=20,restar_velas=1)
    print(par,escala,p)

def probar_retroceso_fibos(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.retroceso_fibo_mm(escala)
    print('retroceso_fibo_mm',par,escala,p)    
    p = ind.retrocesos_fibo_macd(escala,3)
    print('retroceso_fibo_macd',par,escala,p)
    p = ind.retrocesos_fibo_macd_ema(escala,3)
    print('retroceso_fibo_macd_ema',par,escala,p)
    
    
    ret = ind.retrocesos_convergentes_fibo_macd(escala)
    print('retrocesos_convergentes_fibo_macd',par,escala,ret)

def probar_atr_bajos(par,escala):
    ind=Indicadores(par,log,globales,client)
    p = ind.atr_bajos(escala)
    print('atr_bajos',par,escala,p)

    
def probar_rango_retro_fibo(par,escala): 
    ind=Indicadores(par,log,globales,client)
    pmin,pmax = ind.calc_rango_fibo(escala)
    print ('rango:',pmin,pmax)
    px_en_rango = ind.precio_en_rango(escala,pmin,pmax) 
    print (ind.precio_mas_actualizado(),px_en_rango)

def probar_retrocesos_convergentes_fibo_macd(par,escala): 
    ind=Indicadores(par,log,globales,client)
    for i in range(3):
       p = ind.retrocesos_convergentes_fibo_macd(escala,i)
       print('retrocesos_convergentes_fibo_macd',par,escala,i,p) 


def probar_el_precio_puede_caer(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.el_precio_puede_caer(escala)
    print('probar_el_precio_puede_caer',par,escala,p)    
              
def probar_promedio_bajos_macd(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.promedio_bajos_macd(escala)
    print('probar_promedio_bajos_macd',par,escala,p) 

def probar_buscar_escala_con_rango_o_caida_macd(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.buscar_escala_con_rango_o_caida_macd(escala)
    b = ind.promedio_bajos_macd(p)
    print('buscar_escala_con_rango_o_caida_macd y precio de compra',par,escala,p,b)     

def probar_tendencia_adx(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.tendencia_adx(escala)
   
    print('tendencia_adx',par,escala,p)   

def probar_detectar_pumps(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.detectar_pumps(escala,cvelas=5,xatr=10,xvol=10)
    print('detectar_pumps',par,escala,p)

def probar_adx_negativo(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p = ind.adx_negativo(escala)
    print('adx_negativo',par,escala,p)

def probar_sqzmon_lb(par,escala): 
    ind=Indicadores(par,log,globales,client)
    p,q = ind.sqzmon_lb(escala)
    print (p,q)

def probar_rsi_minimo(par,escala):
    print('---probar_rsi_minimo---')
    ind=Indicadores(par,log,globales,client)
    p,q = ind.rsi_minimo(escala)
    print (p,q)


def probar_squeeze_df_describir(par,escala): 
    print('---squeeze_df_describir---')
    ind=Indicadores(par,log,globales,client)
    sqz = ind.squeeze_df_describir(escala)
    print (sqz)

def probar_pendiente_positiva_ema(par,escala,periodos): 
    ind=Indicadores(par,log,globales,client)
    p = ind.pendiente_positiva_ema(escala,periodos)
    print('pendiente_positiva_ema',par,escala,periodos,p)

def probar_tres_emas_favorables(par,escala): 
    ind=Indicadores(par,log,globales,mercado)
    p = ind.tres_emas_favorables2(escala,9,20,55)
    print('tres_emas_ordenadas',par,escala,p)


def probar_rsi_mfi_vector(par,escala): 
    ind=Indicadores(par,log,globales,mercado)
    p = ind.rsi_vector(escala)
    print('rsi_vector',par,escala,p)   
    #p = ind.mfi_vector(escala)
    #print('mfi_vector',par,escala,p) 

def probar_rsi_minimo_y_pos(par,escala): 
    ind=Indicadores(par,log,globales,mercado)
    p = ind.rsi_minimo_y_pos(escala,2)
    print('rsi_minimo_y_pos',par,escala,p)   
    #p = ind.mfi_vector(escala)
    #print('mfi_vector',par,escala,p)    


def probar_sum(par):
    print(  ind.volumen_suma('1d',15))

def probar_max_vol(escala):
    maxv=ind.maximo_x_vol(escala,300,5) 
    px = ind.precio_mas_actualizado() 
    print (maxv,px)
    print(  px/maxv  )


def probar_detector(par): 
    ind=Indicadores(par,log,globales,mercado)
    
    print (par,'1h','min',ind.minimo_x_vol('15m',16,1) )
    print (par,'1m','min',ind.minimo_x_vol('1m',120,1) )

def probar_lista_maximos(par): 
    ind=Indicadores(par,log,globales,mercado)
    print (par,'3m','min',ind.lista_picos_maximos_ema('3m',9,20,'close',2,5) )
 


def probar_minimo_maximo_por_rango_velas_imporantes(par): 
    ind=Indicadores(par,log,globales,mercado)
    for es in ['1m','3m','5m','15m','1h','4h','1d','1w','1M']:
        minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(es,90 ) 
        delta = maximo - minimo
        max_delta =  maximo - delta * .3
        min_delta = minimo + delta *.3
        gan = calculo_ganancias(min_delta,max_delta)
        #velas = ind.velas_imporantes(es,90,3)

        print(f'{es} delta {delta} minimo {minimo} [{min_delta} {max_delta}]  {maximo} maximo  gan {gan}')
        
            
        
    print('-----------------------------------------')
    


def probar_cruce_de_emas(par): 
    ind=Indicadores(par,log,globales,mercado)
    print (par,'3m',ind.cruce_de_emas('3m',10,20,50) )


def probar_zona_volumen(par): 
    ind=Indicadores(par,log,globales,mercado)
    maximos=ind.lista_picos_maximos_ema('3m',9,100,'close',15,15) 
    fin = -maximos[0][0]
    print(fin)
    print(ind.hubo_zona_de_alto_volumen('3m',-1,fin)  )

def probar_porcentaje_recorrido_del_rango(par):
    ind=Indicadores(par,log,globales,mercado)
    print (par,'1m',ind.porcentaje_recorrido_del_rango('5m',120) )

def probar_minimo_maximo_por_rango_velas_imporantes(par,escala):
    ind=Indicadores(par,log,globales,mercado)
    minimo,maximo = ind.minimo_maximo_por_rango_velas_imporantes(escala,65 ) 
    print(minimo,maximo)

t = time.time()

moneda='BTC'
par = moneda+'USDT'

ind=Indicadores(par,log,globales,mercado)
while time.time() -t < 1200:
    probar_minimo_maximo_por_rango_velas_imporantes(par,'1m')
    time.sleep(15)

mercado.detener_sockets()


   