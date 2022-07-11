def numero_humano(numero):
    ent=int(numero)
    dec=numero-ent
    if 0<ent<10:
        return str(round(numero,4))
    elif ent>=10:
        return str(round(numero,2))
    else:
        return '{0:.10f}'.format(numero) 
    



print numero_humano(1)              
print numero_humano(5)
print numero_humano(50)
print numero_humano(100)
print numero_humano(0.51)
print numero_humano(3.14)
print numero_humano(0.01)
print numero_humano(0.002)
print numero_humano(0.0003)
print numero_humano(0.00004)
print numero_humano(0.000005)
print numero_humano(0.0000006)
print numero_humano(0.00000007)
print numero_humano(0.000000008)
print numero_humano(0.0000000009)
