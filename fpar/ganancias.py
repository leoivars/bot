from variables_globales import VariablesEstado
def calc_ganancia_minima(g:VariablesEstado,ganancia_inicial,escala,tiempo_trade):
    #proporcional a lo minimo ganado en un minuto
    ganancia= g.escala_ganancia[escala]
    #ganancia_por_tiempo =  g.escala_ganancia['1M'] / g.escala_tiempo)                  * tiempo_trade
    #ganancia_minima=max(ganancia,ganancia_por_tiempo)
    #?
    return ganancia 

