# # -*- coding: UTF-8 -*-

from ..pws import  Pws

#imports universales
from flask import Flask,make_response,render_template
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure
import io
import random


#imports mios de la carpeta superior
import sys
#sys.path.append('..')

from logger import *
from acceso_db import Ac
from acceso_db_conexion import *



app = Flask(__name__)
@app.route('/')
def index():
    p=db.get_valores('COCOS','BTC')
    ultimo_hist=db.ind_historico_ultimo_registro(p['idpar'])
    

    return render_template('index.html',grafico=grafico())

@app.route('/plot/')
def plot():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]

    axis.plot(xs, ys)

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/temp')
def plot_temp():
	times, temps, hums = getHistData(numSamples)
	ys = temps
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Temperature [°C]")
	axis.set_xlabel("Samples")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'
	return response

def grafico():   
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]

    axis.plot(xs, ys)

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response
 




if __name__ == '__main__':
    log=Logger('server_flask.log') 
    pws=Pws()
    #apertura del pull de conexiones
    conn=Conexion_DB(log)
    #objeto de acceso a datos
    db=Acceso_DB(log,conn.pool)
    app.run(debug = True)


