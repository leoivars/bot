from flask import Flask,make_response,render_template


class Web_serber:
    def __init__(self):
        self.app = Flask(__name__)
            
    @app.route('/')
    def index(self):
        return "HOLA"


    def web_server(self):
        app.run(debug = True)
