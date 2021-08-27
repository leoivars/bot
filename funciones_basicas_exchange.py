import time
def esperar_correcto_funcionamiento(client,log):
    # esperamos el corremto funcionamiento del systema
    
    while True:
        try:
            if client.get_system_status() ['status']==0:
                print('Sistema OK. Comenzamos!')
                e.se_puede_operar = True
                break
            else:
                print('Sistema en mantenimiento...')
                e.se_puede_operar = False
        except:
            print('Sistema en mantenimiento, o no responde client.get_system_status()...')
            e.se_puede_operar = False

        time.sleep(300)
    e.se_puede_operar = True
    log.log( 'todo ok, se puede operar' )
    
    