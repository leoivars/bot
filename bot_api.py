from flask import Flask, request, jsonify
from flask_restful import Resource, Api

from acceso_db import Acceso_DB
from funciones_utiles import mes_anio_actuales

from variables_globales import Global_State 
from multiprocessing import Process

import time


class BotApi:
    db = None
    def __init__(self,log,pool_db,estado_general):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(TradesEjecutados, '/trades_ejecutados')  # Route_1
        self.api.add_resource(Trades, '/trades')  # Route_1
        BotApi.db = pool_db
        self.estado_general:Global_State = estado_general

    def run(self):

        self.server = Process( target=self.app.run, kwargs={'port':'5001'}  )   
        self.server.start()

        while self.estado_general.trabajando:
            time.sleep(1)
        
        self.server.terminate()
        self.server.join()


class TradesEjecutados(Resource):
    def get(self):
        mes,anio = mes_anio_actuales()
        print(mes,anio)
        result = BotApi.db.trades_ejecutados_y_ganancia(mes,anio)
        print (result)
        return jsonify ( {'trades':result} )

class Trades(Resource):
    def get(self):
        mes,anio = mes_anio_actuales()
        print(mes,anio)
        result = BotApi.db.trades_abiertos(mes,anio)
        print (result)
        return jsonify ( {'trades':result} )
            
    
