from variables_globales import VariablesEstado
def calc_ganancia_minima(g:VariablesEstado,ganancia_inicial,escala,tiempo_trade):
    #proporcional a lo minimo ganado en un minuto
    ganancia= g.escala_ganancia[escala]

    #if tiempo_trade > g.escala_tiempo[escala] * 30  + 7200:    # ha pasado mucho tiempo, quiere decir que no subió lo que se pensaba
    #    ganancia = ganancia * .5                               # bajamos la ganancia para vender

    
    return ganancia 

