from  pws import Pws
import pymysql
from dbutils.pooled_db import PooledDB  #https://cito.github.io/DBUtils/UsersGuide.html
class Conexion_DB: 
    pool=None  

    def __init__(self,log):
        
        self.log=log
        self.conectar(Pws())
        

    
    def conectar(self,pws):#Conectar a la base de datos
        try:
            if Conexion_DB.pool==None:
                Conexion_DB.pool = PooledDB(pymysql,
                            mincached=0,  # At the time of initialization, at least an idle link is created in the link pool. 0 means no link is created.
                            maxcached=0,
                            maxshared=0,
                            maxconnections=50,
                            blocking=True, # 9/04/2020 para que espere cuando no hay conexiones disponibles? sino le caga la conexion al otro hilo
                            maxusage=0,
                            host= pws.db_host,
                            user= pws.db_user,
                            passwd= pws.db_pass,
                            db='bot',
                            port=3306,
                            #setsession=['SET AUTOCOMMIT = 1'] is used to set whether the thread pool opens the automatic update configuration, 0 is False, 1 is True.
                            setsession=['SET AUTOCOMMIT = 1'],
                            # ping the MySQL server to check if the service is available.
                            # :0 = None = never,
                            # 1 = default = whenever it is requested,
                            # 2 = when a cursor is created,
                            # 4 = when a query is executed,
                            # 7 = always
                            ping=2
                            
                            
                            ) 
                            
                                     
        except Exception as e:
            self.log.log( "Error al conectar:",e)


    def desconectar(self):
    	Conexion_DB.pool.close()
    	Conexion_DB.pool=None




