from variables_globales import VariablesEstado
from logger import *

def log_pares_estado(e,estado,maximo_a_mostrar=999):
    lin=''
    tot=0
    maxlin=0
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            if maxlin < maximo_a_mostrar:
                lin+=k.ljust(9,' ') + ' ' +p.mostrar_microestado()
                maxlin += 1
            tot += 1

    lin= 'En Estado ' + str(estado) + ' total=' + str(tot) + '\n' + lin        
    return lin        
    #log.log(lin)

def log_cuenta_pares_estado(e,estado):
    lin='En Estado '+ str(estado) +'= '
    cuenta=0
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            cuenta+=1
    return lin        
    #log.log(lin)


def log_pares_estado_ordenado_por_ganancia(e,estado,cant=15):
    lin='En Estado '+ str(estado) +'\n'
    #obengo pares en estado 3 y sus ganancias
    pares_en_estado={}    
    
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            pares_en_estado[k]=p.ganancias()
    #recorro la lista obtenida en ordenada por su valor (ganancia)
    c = 0
    for k in sorted(pares_en_estado, key=pares_en_estado.get, reverse=True):
        p=e.pares[k][0]
        #if pares_en_estado[k] > -2: #filtro para mostrar solos los positivos o los que estan por ser positivos
        lin+=k.ljust(9,' ') + ' ' +p.mostrar_microestado()
        c = c +1
        if c > cant: #solo motrar los primeros cant
            break
    
    return lin        
    #log.log(lin)

def log_pares_senial_compra(e):
    e.cant_pares_con_senial_compra=0
    e.pares_con_senial_compra=[]
    #lin='Con Señal de Compra \n'
    try:    
        for k in e.pares_control.keys():
            p=e.pares[k]
            if p.senial_compra:
                e.cant_pares_con_senial_compra+=1
                e.pares_con_senial_compra.append(k)
        #log.log(lin)
        
        #27/08/19probando si esto pono lento a todo!#procesar_necesidades_de_liquidez()    
    except Exception as ex:
        log.log( "Error en log_pares_senial_compra:",ex )
        

def log_pares_estado7(e):
    estado=7
    lin='En Estado 7\n'
    #obengo pares en estado 7 y sus filtros superados
    pares_en_estado={}    
    for k in e.pares_control.keys():
        p=e.pares[k][0]
        if p.estado==estado:
            if p.e7_filtros_superados > 10:
                pares_en_estado[k]=p.e7_filtros_superados
    #recorro la lista obtenida en ordenada por su valor (ganancia)
    col=0
    for k in sorted(pares_en_estado, key=pares_en_estado.get, reverse=True):
        
        if pares_en_estado[k]>0:
            lin+=k.ljust(9,' ') + ' ' + str (pares_en_estado[k] )
            col+=1
        
            if col==4:
                lin+='\n'
                col=0
            else:
                lin+='|'    


    return lin        
    #log.log(lin)    

def log_trades_activo_contra(moneda_contra,hpdb,log):
    lin=''
    for r in hpdb.get_monedas_con_trades_activos(moneda_contra):
        lin+=' '+r['moneda'].lower()
    log.log('trades_activos_'+moneda_contra.lower(),lin)    
  
def log_trades_activos():
    log_trades_activo_contra('BTC')
    log_trades_activo_contra('USDT')
    log_trades_activo_contra('PAX')


def mostrar_informacion(e:VariablesEstado,   log:Logger):
    
    #log_pares_senial_compra() #este debe ir primero porque establece las necesidadas de liquidez
    #log_cuenta_pares_estado(2)


    log.log(  log_pares_estado_ordenado_por_ganancia(e,3)  )
    log.log(  log_pares_estado(e,2,100)  )
    log.log(  log_pares_estado(e,9,20)  )
    #log.log(  log_pares_estado7() )