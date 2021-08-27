# # -*- coding: UTF-8 -*-
import sys
import time
from par import *
from LectorPrecios import *
from binance.client import Client #para el cliente
from binance.enums import * #para  create_order
import json



api_key = "AJ3CQ6LAJtpzAgG1wgnohjt5nVHk8VftntMGQrk1Rb2UcYkj5Z5TtxELMPv8elIh"
api_secret = "EGxRazPrqsw8wyWJcM2aC0dqkPgGXqcZLCxipA5DG5uchuVjg2Jw9XKO31LIhD2W"
client = Client(api_key, api_secret)

## variables globales
class VariablesEstado:
    estado=0
    fee = 0.0005
    par = 0
    cantidad_inicial=0
    moneda_contra=0
    stoploss=0
    preciobuscado=0
    pares=[]
e=VariablesEstado()

## toma de parámetros
# codigo para tomar argumentos de linea de comando
# hay que mejorarlo para tomar varios argumentos
# mirar https://www.tutorialspoint.com/python/python_command_line_arguments.htm
#parametros; 
# par
# cantidad de resguardar
#   % p_stoploss: porcentaje de para fijar el stop loss
# if len(sys.argv)<4:
#     print 'Argumentos: <Moneda> <Moneda_Contra> <Cantidad_a_Resguardar> <stoploss>'
#     sys.exit()
# else:
#     arg_moneda=sys.argv[1].upper()
#     arg_moneda_contra=sys.argv[2].upper()
#     arg_resguardar=float(sys.argv[3])
#     arg_stoploss=float(sys.argv[4])
# print  arg_moneda, arg_moneda_contra, arg_resguardar, arg_stoploss

lp=LectorPrecios(client)

with open("monedas_a_protejer.json") as f:
    data = json.load(f)


print "----------------------INICIO----------------------------"    
#primer toma de precio para creación de objetos
precios = lp.leerprecios()


for p in (data):
    print p['moneda'], p['moneda_contra'], p['cantidad'], p['pstoploss'],p['stoploss'],
    
    # creo el objeto
    e.par=Par(client,e.fee,float(p['pstoploss']),float(p['stoploss']),p['moneda'].upper(),p['moneda_contra'].upper())
    e.par.tomar_precio(precios)
    e.par.set_cant_moneda_stoploss( float(p['cantidad']) )
    e.par.estado_1_inicio()
    e.pares.append(e.par)
print "--------------------------------------------------"    

##-----bucle principal------##

while True:
    print "Esperando..."
    time.sleep(55)  
    precios = lp.leerprecios()
    for p in (e.pares):
        p.tomar_precio(precios)
        p.accion()
    print "--------------------------------------------------"    
           #ELFBTC Estado: 1 0.00008680 0.00008687 0.000084470

    
## ----------FIN--------------##
    
  