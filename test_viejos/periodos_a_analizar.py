from funciones_utiles import strtime_a_obj_fecha

class Periodos_a_analizar():
    def bueno_30k_66k(self):
        '''3 meses de subida julio 21 a agosto 21'''
        descripcion_periodo='periodo bueno de 30 a 66k'
        fecha_fin =  strtime_a_obj_fecha('2021-07-19 00:00:00') 
        fin_test  =  strtime_a_obj_fecha('2021-10-20 23:59:00')
        return descripcion_periodo,fecha_fin,fin_test

    def malo_inmenso_63k_21k(self):
        '''10 meses de bajada de abril 21 a julio 22'''
        descripcion_periodo='periodo inmenso 63k a 21k'
        fecha_fin =  strtime_a_obj_fecha('2021-04-15 00:00:00')
        fin_test  =  strtime_a_obj_fecha('2022-06-14 22:00:00')
        return descripcion_periodo,fecha_fin,fin_test
    
    def rango_mayo_22 (self):
        '''Rango ocurrido en mayo 22 con una pequeña bajada'''
        descripcion_periodo='Bajada Rango Mayo 22'
        fecha_fin =  strtime_a_obj_fecha('2022-05-04 09:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-14 22:00:00')
        return descripcion_periodo,fecha_fin,fin_test
    
    def rango_bajada_rango_junio_22 (self):
        '''Rango bajada y rango ocurrido ultima quincena junio 22'''
        descripcion_periodo='rango_bajada_rango_junio_22'
        fecha_fin =  strtime_a_obj_fecha('2022-06-04 09:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-07-02 16:00:00')
        return descripcion_periodo,fecha_fin,fin_test

    def rango_subida_julio22(self):
        '''dos dia, al principio rango y luego una subida en Julio 22'''
        descripcion_periodo='rango_subida_julio22'
        fecha_fin =  strtime_a_obj_fecha('2022-07-02 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-07-04 21:20:00')
        return descripcion_periodo,fecha_fin,fin_test

    def rango_mes_mayo_10_junio_09_22(self):
        '''Rango ocurrido entre  mayo 10 y junio 09 del 22 con una pequeña bajada
        Es un periodo malo '''
        descripcion_periodo='Rango Mayo 10 Junio 09'
        fecha_fin =  strtime_a_obj_fecha('2022-05-10 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-09 23:59:00')
        return descripcion_periodo,fecha_fin,fin_test
    
    def bajada_8_dias_mayo_22(self):
        '''Periodo de bajada de 8 dias durante mayo 2022'''
        descripcion_periodo='Mayo 22 8 días bajada'
        fecha_fin =  strtime_a_obj_fecha('2022-05-04 08:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-05-12 05:00:00')
        return descripcion_periodo,fecha_fin,fin_test

    def bajada_1_dia_Junio_22(self):
        '''Periodo de bajada de 1 dia durante junio 2022'''
        descripcion_periodo='Junio 22 un día bajada'
        fecha_fin =  strtime_a_obj_fecha('2022-06-10 03:22:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-11 19:15:00')
        return descripcion_periodo,fecha_fin,fin_test

    def bajada_trampa_20_horas_Junio_22(self):
        '''Periodo de bajada con trampa de 20 horas durante el 12 junio 2022'''
        descripcion_periodo='Junio 12 20 horas de bajada con trampa'
        fecha_fin =  strtime_a_obj_fecha('2022-06-12 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-12 20:00:00')
        return descripcion_periodo,fecha_fin,fin_test
        
    def bajada_12_dias_Junio_05_17_2022(self):
        '''Periodo de bajada del 30k a 20k durante junio 2022
         hay mucho miedo en el mercado'''
        descripcion_periodo='Bajada 30k 20k 12 dias'
        fecha_fin =  strtime_a_obj_fecha('2022-06-05 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-17 09:33:00')
        return descripcion_periodo,fecha_fin,fin_test

    def bajada_micro_18_junio_2022(self):
        '''Periodo rango, bajada 20k a 19k, rango producido en 10 horas de sábado'''
        descripcion_periodo='bajada_micro_18_junio_2022'
        fecha_fin =  strtime_a_obj_fecha('2022-06-18 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-06-18 10:44:00')
        return descripcion_periodo,fecha_fin,fin_test

    def junio_julio_22(self):
        '''Junio y Julio 2022'''
        descripcion_periodo='junio_julio_22'
        fecha_fin =  strtime_a_obj_fecha('2022-06-01 00:00:00')  
        fin_test  =  strtime_a_obj_fecha('2022-07-31 23:59:59')
        return descripcion_periodo,fecha_fin,fin_test    

