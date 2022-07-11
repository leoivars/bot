escala_anterior ={'1m':'xx','3m':'1m','5m':'3m' ,'15m':'5m' ,'30m':'15m','1h':'30m','2h':'1h','4h':'2h','1d':'4h','1w':'1d','1M':'1w'}
escala_siguiente={'1m':'3m','3m':'5m','5m':'15m','15m':'30m','30m':'1h' ,'1h':'2h' ,'2h':'4h','4h':'1d','1d':'1w','1w':'1M','1M':'xx'}
escala_tiempo  = {'1m':60  ,'3m':180 ,'5m': 300 ,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,'1w':604800,'1M':2419200}

escala_ganancia ={'1m':.5  ,'3m':0.7  ,'5m': .9  ,'15m': 2   ,'30m':2.5 ,'1h':3 ,'2h':3.5, '4h':4  ,'1d':5  , '1w':15,'1M':30}
escala_entorno  ={'1m':.25 ,'3m':0.35 ,'5m': .45 ,'15m': 0.55,'30m':0.75,'1h':1 ,'2h':1.25,'4h':1.5,'1d':2.5, '1w':3 ,'1M':5 }


def zoom(escala,x=1):
    esc=escala
    for i in range(x):
        e=escala_anterior[esc]
        if e == 'xx':
            break
        else:
            esc=e
    return esc

def zoom_out(escala,x=1):
    esc=escala
    for _ in range(x):
        e=escala_siguiente[esc]
        if e == 'xx':
            break
        else:
            esc=e
    return esc    