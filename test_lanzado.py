import sys
import datetime


print( sys.argv)

c=int(sys.argv[1])
f=datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S.%f')

print (c,f)