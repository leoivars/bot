# # -*- coding: UTF-8 -*-

from par_propiedades import Par_Propiedades


class Analizador:       

    def __init__(self, ind,log): #ind...>indicadores previamente instanciado y funcionando
        self.ind = ind
        self.log = log
        
        #self.propiedades_par=Par_Propiedades(ind.par,ind.client,ind.log) ### de momento no hace falta y en caso de que haga falta que se pase como parámetro
    
    def cargar_velas(self,escala):
        self.ind.actualizar_velas(escala)
        o = self.ind.get_vector_np_open(escala)
        h = self.ind.get_vector_np_high(escala)
        l = self.ind.get_vector_np_low(escala)
        c = self.ind.get_vector_np_close(escala)
        
        return o,h,l,c 
        
        
class Analizador_Patrones(Analizador):
    
    def detectar_patrones(self,escala):
        salida=[]
        velas_de_salida = 5
        for e in range(velas_de_salida):
            salida.append([])


        o,h,l,c = self.cargar_velas(escala)
        # recolecto todos los patrones que encuentro
        for f in talib.get_functions():
            if f.startswith('CDL'):
                func = getattr(talib, f)
                ret = func(o,h,l,c)
                j=0
                for i in ret[-velas_de_salida:]:
                    #print(j,salida)
                    if i !=0:
                        salida[j].append([f,i])
                        self.log.log(f,i)
                    j+=1    
        
        #print(salida)
        total=0
        patrones = []        
        for ss in salida:
            sumap = 0
            suman = 0
            #print('-----------------')
            for s in ss:
                #print(s[0],s[1])
                if s[1] >0:
                    sumap += s[1]
                else:
                    suman += s[1] 

            
            patrones.append([sumap,suman])       
                
            total += sumap+suman    
            if sumap > 0 and suman == 0:
                resaltar =' ++++++ '
            else:
                resaltar =''    
            #print('sums',sumap,suman,'---'+resaltar)

        
        #print('Total',total,'####################')
        return patrones  

            


         

   
    
