
import time

from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager

binance_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com",)
binance_websocket_api_manager.create_stream( ['kline_1m','kline_5m'], ['btcusdt'],'btcusdt',output="UnicornFy",) #0.00000597
#binance_websocket_api_manager.create_stream()


sid= binance_websocket_api_manager.get_stream_id_by_label('btcllusdt')
#print('print_summary', binance_websocket_api_manager.print_summary())
#print('print_summary', binance_websocket_api_manager.print_summary())
info = binance_websocket_api_manager.get_stream_info(sid) 

for i in info:
    print( i, info[i])



t0= time.time()


#proxima={'1m':60000,'5m':300000,'15m':900000,'30m':1800000,'1h':3600000,'2h':7200000,'4h':14400000,'1d':57600000,'1w':403200000,'1M':1728000000}}

def parse_velas(buffer):
    try:
        par=buffer['symbol']
        k = buffer['kline']
        escala=k['interval']
        open_time=int(k['kline_start_time'])
        is_closed = bool(k['is_closed'] )
        o = k['open_price']
        h = k['high_price']
        l = k['low_price']
        c = k['close_price']
        v = k['base_volume']
        #print(k['is_closed'],is_closed,type(is_closed))
        if is_closed:
            print( par,escala,open_time,is_closed ,o,h,l,c,v)
    except Exception as e: 
        pass
        print('err-->',str(e))



while True:
    oldest_stream_data_from_stream_buffer = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
    if oldest_stream_data_from_stream_buffer:
        parse_velas(oldest_stream_data_from_stream_buffer)
        # print(f'====>{oldest_stream_data_from_stream_buffer}<====')
        #for key in oldest_stream_data_from_stream_buffer:
        #    print(f'--->{oldest_stream_data_from_stream_buffer[key]}<---')
    time.sleep(1)    

   