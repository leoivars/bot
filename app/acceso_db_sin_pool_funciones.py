# # -*- coding: UTF-8 -*-
#import pymysql

import time
from threading import Lock
from datetime import datetime

import pymysql
#import traceback

class Acceso_DB_Funciones:
   
    def __init__(self,log,conn):

        self.log=log
        self.conexion=conn.conexion
        self.cursor = self.conexion.cursor()

    def commit(self):
        self.conexion.commit()


###---------------------FIN-REPORTES-------------------------------###
    def ejecutar_sql(self,sql,paramentros=None):
        ret=None
        
        try:
            if paramentros ==None:
                ret=self.cursor.execute(sql)
            else:    
                ret=self.cursor.execute(sql,paramentros)
        except Exception as e:
            if 'uplicate entry' in str(e):
                ret=-1 
            else:
                self.log.err(  'error: ejecutar_sql',e,sql,paramentros)
            time.sleep(1)
        
        return ret


    def ejecutar_sql_sin_cursor(self,sql,paramentros=None):
        ret=None
        
        try:
            if paramentros ==None:
                ret=self.cursor.execute(sql)
            else:    
                ret=self.cursor.execute(sql,paramentros)
        except Exception as e:
            if 'uplicate entry' in str(e):
                ret=-1 
            else:
                self.log.err(  'error: ejecutar_sql',e,sql,paramentros)
            time.sleep(1)
         
        return ret    

    def ejecutar_sql_ret_dict(self,sql,paramentros=None):
        
        try:
            if paramentros == None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql,paramentros)
                
            ret=self.cursor2dict(self.cursor)
            
        except Exception as e:
            self.log.err(  'error: ejecutar_sql_ret_dict',str(e),sql,paramentros)
            #tb = traceback.format_exc()
            #self.log.err( tb )
            time.sleep(1)
            ret={}
             
        return ret

    def ejecutar_sql_ret_cursor(self,sql,paramentros=None): #renombrar en el futuro como ret_all
        '''
        Retorna una lista con todos los registros recuperados, no es un cursor.
        '''
        
        ret=[]
        try:
            if paramentros == None:
               
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql,paramentros)
            ret=self.cursor.fetchall()
        except Exception as e:
            self.log.err(  'error: ejecutar_sql_ret_ejecutar_sql_ret_cursor',e,sql,paramentros)
            #tb = traceback.format_exc()
            #self.log.err( tb )
            time.sleep(1)
             
        return ret


    def ejecutar_sql_ret_1_valor(self,sql,paramentros=None):
        
        try:
            self.cursor.execute(sql,paramentros)
            row = self.cursor.fetchone()
            if row is None:
                ret = None
            else:    
                ret = row[0]
        except Exception as e:
            self.log.err(  'error: ejecutar_sql_ret_1_valor',e,sql,paramentros)
            #tb = traceback.format_exc()
            #self.log.err( tb )
            ret = None
            time.sleep(1)

        return ret
    
    def cursor2dict(self,cursor):
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]  
        return rows

if __name__=='__main__':
    from logger import Logger
    from acceso_db_sin_pool_conexion import Conexion_DB_Directa
    from acceso_db_sin_pool_funciones import Acceso_DB_Funciones
    log = Logger('test_acceso_db_sin_pool.log')
    conn = Conexion_DB_Directa(log)
    log.log(type(conn.conexion))

    fxdb = Acceso_DB_Funciones(log,conn)
    log.log( fxdb.ejecutar_sql_ret_1_valor( 'select count(1) as cuenta from pares')   )
  


    
    
    
    
    
    conn.desconectar()