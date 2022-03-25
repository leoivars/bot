from acceso_db_modelo import Acceso_DB #acceso a la base de datos
#from Monitor_precios_ws import MonitorPreciosWs
from variables_globales import Global_State
class ReportesDB():
    def __init__(self,log,db,variables_estado):
        self.log = log
        self.db  = db   #Acceso_DB(log,conn.pool)
        self.g: Global_State = variables_estado
    
    def campos(self,dict,str_keys):
        cam=''
        for k in str_keys.split():
            cam += str(dict[k]) + ' '
        
        return cam.lstrip()    

