class Btc_Analizador:

    def __init__(self, ibtc):
        self.ibtc=ibtc
        self.analizar_subiendo_sin_fuerza()

    def analizar_subiendo_sin_fuerza(self):    
        
        ema55=self.ibtc.ema('15m',55)
        ema9 =self.ibtc.ema('15m',9)
        adx  =self.ibtc.adx('15m')
        #self.log.log('Control BTC 15m  Ema9,Ema55',ema9,ema55)
        if ema9>ema55 and adx[0]<23:
            self.subiendo_sin_fuerza=True
            #self.log.log("BTC-------> Ema9,Ema55,adx OK!",ema9,ema55,adx[0])    
        else:
            #self.log.log("BTC-------> Ema9,Ema55,adx NO PASA!",ema9,ema55,adx[0])
            self.subiendo_sin_fuerza=False