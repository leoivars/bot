from vela import Vela
def fucionar_velas(a:Vela,b:Vela):
    r = Vela()
    r.high=max(a.high,b.high)
    r.low = min(a.low,b.low)
    r.open = a.open
    r.close = b.close
    r.volume= a.volume + b.volume
    r.set_signo()
    return r

def describir_vela(v:Vela):
    ''' analiza vela y retorna -1 para vela bajista 1 vela alcista 0 vela neutra'''
    c = v.cuerpo()
    s = v.sombra_sup()
    i = v.sombra_inf()
    ret =0

    if s > c * 2 and  s > i * 2: #sombre superior grande con respecto al cuerpo la sombre inferior
        ret = -1
    elif i > c * 2 and  i > s * 2: #sombre inferior grande con respecto al cuerpo y la sombre inferior
        ret = 1

    return ret        


    


    



    