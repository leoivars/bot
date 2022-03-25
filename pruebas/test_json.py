import json

#codigo para tomar argumentos de linea de comando
#hay que mejorarlo para tomar varios argumentos
#mirar https://www.tutorialspoint.com/python/python_command_line_arguments.htm





class X:


    def cargar_par_json(self):

        with open('par.json','r') as f:
            parconfig = json.load(f)
            
        print (parconfig)
        print ("------------------------------------------------------")

        print ( parconfig[0]['reserva_btc_en_usd'] )




x=X()

x.cargar_par_json()


