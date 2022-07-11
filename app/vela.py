
import datetime
class Vela:
    
    def __init__(self,df=None,open_time=None): 

        #print('------>df----->',df)
        if df is None:
            self.open_time=0
            self.open=0
            self.high=0
            self.low=0
            self.close=0
            self.volume=0
            self.close_time=0
            self.closed = 0
        else:
            self.open_time=open_time
            self.open=df.get('open')
            self.high=df.get('high')
            self.low=df.get('low')
            self.close=df.get('close')
            self.volume=df.get('volume')
            self.close_time=df.get('close_time')
            self.closed = df.get('closed')
        
        self.set_signo()


    def set_signo(self):
        if self.close>self.open:
            self.signo=1
        else: 
            self.signo=-1    

    def __del__(self):
        #del self.open_time
        del self.open
        del self.high
        del self.low
        del self.close
        del self.volume
        #del self.close_time  


    
    # def hayvariaciones(self,pvela): #sin no es la misma vela o si no hay variaciones, retorma false. Caso contrario true
    #     ret=False
    #     if (self.open_time != pvela.open_time): #los datos corresponden a la misma vela, seguimos revisando
    #         ret=(self.volume    != pvela.volume or #pongo a volumen primero porque entiendo que es lo que seguro cambia en caso de ser una vela mas actual
    #              self.open      != pvela.open or
    #              self.high      != pvela.high or
    #              self.low       != pvela.low or
    #              self.close     != pvela.close)
    #     return ret #    
           
    def cuerpo(self):
        #print(self.open,self.close,abs(self.close-self.open),self.close-self.open)
        return abs(self.close-self.open)    

    def sombra_sup(self):
        if self.open<=self.close:
            return self.high-self.close
        else:
            return self.high-self.open

    def sombra_inf(self):
        if self.open<=self.close:
            return self.open-self.low
        else:
            return self.close-self.low

    def sentido(self):
        if self.open <= self.close:
            return 1 # alcista
        else:
            return -1 #bajista

    def martillo(self):
        cc = self.cuerpo()
        ss = self.sombra_sup()
        ii = self.sombra_inf()
        infinito = 99999999
        
        if cc != 0:
            ii_cc = round( ii / cc ,2)
        else:
            ii_cc = infinito

        if ss !=0:
            ii_ss = round( ii / ss ,2)
        else:
            ii_ss = infinito        

        if ii_cc > 2 and ii_ss > 2:
            martillo = 1
        else:
            martillo = 0    

        return martillo 


    def __str__(self):
        nombre='vela'
        if self.martillo():
            nombre='martillo'
        
        return f'{nombre} {self.close}'
    
    def __repr__(self):
        return self.__str__()    
        
    def imprimir(self):
        print( '------------------------------------' )
        print( 'open_time' , datetime.datetime.fromtimestamp(self.open_time/1000 ).strftime('%Y-%m-%d %H:%M:%S'))
        print( 'open' , self.open )
        print( 'high', self.high )
        print( 'low' , self.low )
        print( 'close' , self.close )
        print( 'volume' , self.volume )
        print( 'close_time' ,datetime.datetime.fromtimestamp(self.close_time/1000 ).strftime('%Y-%m-%d %H:%M:%S')    )
        print( '------------------------------------' )



    # 	[
#     [
#         1499040000000,      # Open time
#         "0.01634790",       # Open
#         "0.80000000",       # High
#         "0.01575800",       # Low
#         "0.01577100",       # Close
#         "148976.11427815",  # Volume
#         1499644799999,      # Close time
#         "2434.19055334",    # Quote asset volume
#         308,                # Number of trades
#         "1756.87402397",    # Taker buy base asset volume
#         "28.46694368",      # Taker buy quote asset volume
#         "17928899.62484339" # Can be ignored
#     ]
# ]
