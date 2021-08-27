def encontrar_justo_el_menor(valor, lista):
    lista.sort(reverse=True)
    print(lista)
    ret = valor
    for v in lista:
        if v < valor:
            ret=v
            break

    return ret   


print (encontrar_justo_el_menor(30,[8,10,56,99,235,12,100]))        