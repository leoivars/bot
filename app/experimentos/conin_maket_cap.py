#This example uses Python 2.7 and the python-request library.

from ast import Param
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'
parameters = {
  'symbol':'KEEP'
  #'limit':'5000',
  #'convert':'USD'
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': 'f89650f5-e629-4bf1-9077-9e3cedce6239',
}

session = Session()
session.headers.update(headers)

try:
  response = session.get(url, params=parameters)
  jresponse = json.loads(response.text)
  data=jresponse['data'][parameters['symbol']]
  for key,value in data.items():
      print (key,value)
except (ConnectionError, Timeout, TooManyRedirects) as e:
  print(e)