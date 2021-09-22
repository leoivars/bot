
from logger import Logger
from binance.client import Client
from mercado import Mercado
from variables_globales import VariablesEstado
from indicadores2 import Indicadores


def main():
    log=Logger('buscar_pares_contra_usdt.log') 
    client = Client()
    e = VariablesEstado
    mercado =Mercado(log,e,client)
    prices = client.get_orderbook_tickers()
    monedas_contra=['USDT']
    for m in monedas_contra:
        lm=len(m)
        for p in (prices):
            s=p['symbol']
            if s.endswith(m):
                moneda=str(s[:len(s)-lm])
                ind=Indicadores(s,log,e,mercado)
                atr = ind.variacion_atr_mm('1d',30)
                log.log(f'{s},variacion_atr_mm {atr} ')
                del ind
                mercado.desuscribir_todas_las_escalas(s)


if __name__=="__main__":
    main()