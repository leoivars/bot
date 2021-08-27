""" 

#hacer un reporte de situacion

#con el id de una trade obtener el mes y año del trade

#con mes y año

1) cantidad de trades y ganancia agrupado or moneda contra

**********************************************************
select 
moneda_contra,
count(1) as cantidad,
sum(
round(ejec_precio*ejecutado - precio*cantidad - ejec_precio*ejecutado*0.001 - precio*cantidad*0.001 ,8)  

)  as resultado

from trades 
where 
 ejecutado = cantidad and
 month(fecha) = 2 and 
 year(fecha) =2020 
 
 group by moneda_contra 
 **********************************************************

 2) 
 con este select
 select * from trades where ejecutado< cantidad and year(fecha)=  2020 and month(fecha) =2

 y los precios del monitor_precio calcular perdidas / ganancias de los trades no cerrados

se podria crear una tabla temporal, suponer los precios cerrados al precio del monitor_precio
y luego podemos tirar el mismo select de 1) """

from reportes_db import ReportesDB
class ReporteEstado(ReportesDB):
    def reporte(self,mes,anio):
        cerrados = str( self.db.trades_ejecutados_y_ganancia(mes,anio) )
        
        ab = self.db.trades_abiertos(mes,anio)
        abiertos=''
        for a in ab:
            par=a['moneda']+a['moneda_contra']
            #px_actual=self.mo_pre.precio(par)
        
            linea  = self.campos(a,'idtrade fecha') + ' ' + par + ' '
            linea += self.campos(a,'senial_entrada cantidad precio ganancia_infima ganancia_segura tomar_perdidas') 
            # linea += str( px_actual) + ' '
            # linea += str( self.ve.calculo_ganancia_porcentual(a['precio'],px_actual) ) + ' '
            # linea += str( self.ve.calculo_ganancia_total(a['precio'],px_actual,a['cantidad']) ) 
            
            abiertos += linea  +'\n'   

        return cerrados + '\n' + abiertos
        


