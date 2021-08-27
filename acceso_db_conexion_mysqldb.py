from  pws import Pws
import MySQLdb
class Conexion_DB: 
    pool=None  

    def __init__(self,log):
        
        self.log=log
        self.conectar(Pws())
        

    def conectar(self,pws):#Conectar a la base de datos
        try:
            if self.pool==None:
                self.pool= MySQLdb.connect(pws.db_host, pws.db_user,pws.db_pass,'bot')
        except Exception as e:
            self.log.log( "Error al conectar:",e)


    def desconectar(self):
    	self.pool.close()
    	self.pool=None



if __name__=='__main__':
    from logger import Logger
    log = Logger('test_Conexion_DB.log')
    conn = Conexion_DB(log)
    print(type(conn.pool))
    conn.desconectar()
