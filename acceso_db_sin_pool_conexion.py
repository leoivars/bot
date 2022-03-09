from  pws import Pws
import pymysql
import pymysql.cursors

class Conexion_DB_Directa: 

    def __init__(self,log):
        
        self.log=log
        self.conexion = None
        self.conectar(Pws())

    def conectar(self,pws:Pws):#Conectar a la base de datos
        try:
            if self.conexion==None: 
                self.conexion= pymysql.connect(host=pws.db_host,
                             user=pws.db_user,
                             password=pws.db_pass,
                             database='bot',
                             cursorclass=pymysql.cursors.Cursor)
        except Exception as e:
            self.log.log( "Error al conectar:",e)

    def desconectar(self):
        self.conexion.close()
        self.conexion=None

if __name__=='__main__':
    from logger import Logger
    log = Logger('test_Conexion_DB.log')
    conn = Conexion_DB_Directa(log)
    print(type(conn.conexion))
    conn.desconectar()
