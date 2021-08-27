from pandas_datareader import data
#from IPython.display import display, HTML
import pandas as pd
import datetime
import pandas_ta as ta

start = datetime.datetime(2020, 1, 1)
end = datetime.datetime.now()
ticker = "SPY"
df = data.DataReader(ticker, 
                       start=start, 
                       end=end, 
                       data_source='yahoo')
print(df)
df.ta.psar(append=True)
print(df)



#display(HTML(df.sort_index(ascending=False).to_html()))