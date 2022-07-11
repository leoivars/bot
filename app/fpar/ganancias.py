from variables_globales import Global_State
def calc_ganancia_minima(g:Global_State,ganancia_inicial,escala,tiempo_trade):
    #proporcional a lo minimo ganado en un minuto
    ganancia= g.escala_ganancia[escala]

    #if tiempo_trade > g.escala_tiempo[escala] * 30  + 7200:    # ha pasado mucho tiempo, quiere decir que no subió lo que se pensaba
    #    ganancia = ganancia * .5                               # bajamos la ganancia para vender

    
    return ganancia 

def calculo_ganancias(g:Global_State,pxcompra,pxventa):  #esta es la funcion definitiva a la que se tienen que remitir el resto.
    comision  = pxcompra * g.fee
    comision += pxventa * g.fee
    gan=pxventa - pxcompra - comision #- self.tickSize
    return round(gan/pxcompra*100,3)   

def precio_de_venta_minimo(g:Global_State,pganancia,pxcompra):
        coef=(1+g.fee)/(1-g.fee)
        ret=pxcompra*coef*(1+pganancia/100) 
        return  ret