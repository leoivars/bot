# # -*- coding: UTF-8 -*-

import os
import time
import datetime
import json

def cargar_config_json():
    with open('config.json','r') as f:
        try:
            config = json.load(f)
        except:
            config = None   
        f.close() 
    return config  


def cargar_trabajando_de_config_json():
    config = cargar_config_json()
    return  bool(config['trabajando'])


inicio_funcionamiento = datetime.datetime.now()
cuenta_de_reinicios=0


trabajando = True

while trabajando:
    print('Lanzador: Lanzando...')

    os.system("python3 bot_main.py "+str(cuenta_de_reinicios)+' "'+str(inicio_funcionamiento)+'"') 
    #test# os.system("python3 test_lanzado.py "+str(cuenta_de_reinicios)+' "'+str(inicio_funcionamiento)+'"') 
    print('Lanzador: fin.')

    trabajando = cargar_trabajando_de_config_json()
    if trabajando:
        print("Lanzador: espero 10 segundos y lanzo")
        time.sleep(10)
        cuenta_de_reinicios += 1
    else:
        print('LJ: Lo Juimos...')    

