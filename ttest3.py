import json
def cargar_parametros_json():
    with open('config.json','r') as f:
        config = json.load(f)
        #log_level= config             
        print (config[0]['log_level'],type(config[0]['log_level'])  )
        f.close()   

cargar_parametros_json()        