# # -*- coding: UTF-8 -*-
#import pymysql

import time
from threading import Lock
from datetime import datetime
from dbutils.pooled_db import PooledDB
#import traceback


class Acceso_DB_Funciones:
    
    lock_cola= Lock()
    cola=[]

    def __init__(self,log,pool):

        self.pool:PooledDB =pool
        self.log=log
        self.conexion=None
        self.cursor=None

        
    def acceso_pedir(self,referencia='xx'):
        ticket_acceso = referencia + ' ' + str(time.time())
        self.lock_cola.acquire(True)
        self.cola.append(ticket_acceso)
        #l=str(len(Acceso_DB.cola))
        self.lock_cola.release()
        #print('Cola--------------------------->SQL----------------------------->' +  l   )
        return ticket_acceso

    def acceso_esperar_mi_turno(self,ticket_acceso):
        esperar = True
        primero=''
        tprimero = time.time()
        while esperar:
            self.lock_cola.acquire(True)   
            
            #el primero se está demorando mucho?
            if primero != self.cola[0]:
                primero = self.cola[0]
                tprimero = time.time()

            else:
                if time.time() - tprimero > 180:
                    self.log.err('DEMORA:',primero,'<-- borrado cola =',len(Acceso_DB.cola) )
                    self.cola.pop(0)

            if primero == ticket_acceso:
                esperar=False

            self.lock_cola.release() 
            
            if esperar:   
                time.sleep(0.25)

    def acceso_finalizar_turno(self,ticket_acceso):

        self.lock_cola.acquire(True)
        try:      
            i=self.cola.index(ticket_acceso)
            self.cola.pop(i)
        except:
            self.log.err('ERROR MUY FEO! acceso_finalizar_turno: ',ticket_acceso)    
        self.lock_cola.release() 

    def cursor_obtener(self):
        while True:
            try: 
                self.conexion=self.pool.connection()
                self.cursor=self.conexion.cursor()
                
                break     # tomo hermoso salimos del bucle

            except Exception as e:
                error = str(e) 
                self.log.err(  'error: cursor_obtener',error)
                if 'Error: Too many connections' in error:
                    #no hay mas cursores de momento, esperemos un poco y reintentamos
                    time.sleep(1)
                else:
                    time.sleep(5)
        return    

    def cursor_liberar(self): 
        try:           
            self.cursor.close()
            self.conexion.close()
        except Exception as e:
            self.log.err(  'error: cursor_liberar',e)
        self.conexion=None
        self.cursor=None

    def ejecutar_sql(self,sql,paramentros=None):
        ret=None
        self.cursor_obtener()
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
             
        
        self.cursor_liberar()  
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
        while True:
            self.cursor_obtener()
            try:
                if paramentros == None:
                    self.cursor.execute(sql)
                else:
                    self.cursor.execute(sql,paramentros)
                ret=self.cursor2dict(self.cursor)

                break
                
            except Exception as e:
                self.log.err(  'error: ejecutar_sql_ret_dict',str(e),sql,paramentros)
                #tb = traceback.format_exc()
                #self.log.err( tb )
                time.sleep(1)
                ret={}
            self.cursor_liberar()     
        
        return ret

    def ejecutar_sql_ret_cursor(self,sql,paramentros=None): #renombrar en el futuro como ret_all
        '''
        Retorna una lista con todos los registros recuperados, no es un cursor.
        '''
        self.cursor_obtener()
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
        self.cursor_liberar()     
        return ret


    def ejecutar_sql_ret_1_valor(self,sql,paramentros=None):
        while True:
            self.cursor_obtener()
            try:
                self.cursor.execute(sql,paramentros)
                row = self.cursor.fetchone()
                if row is None:
                    ret = None
                else:    
                    ret = row[0]
                break
            except Exception as e:
                self.log.err(  'error: ejecutar_sql_ret_1_valor',e,sql,paramentros)
                #tb = traceback.format_exc()
                #self.log.err( tb )
                ret = None
                time.sleep(1)
            self.cursor_liberar()  
        
        return ret

    
    def cursor2dict(self,cursor):
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]  
        return rows