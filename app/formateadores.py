def format_valor_truncando(valor,digitos_decimales):
    if digitos_decimales>0:
        svalor='{0:.9f}'.format(valor)
        punto=svalor.find('.')
        dec=len(svalor[ punto+1:])
        if dec>digitos_decimales: 
            dec=digitos_decimales
        return svalor[0:punto+1+dec]+"0"*(digitos_decimales-dec)
    else:
        return str(int(valor))