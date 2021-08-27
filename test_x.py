class Fx:
    
    def __init__(self): 
        self.ultima=self.f2

    def f1(self,par):
        print('f1...',par)
        return 1

    def f2(self,par1,par2):
        print('f2...',par1,par2)
        return 2
    
    def f3(self):
        print('f3...')    
        return 3


    def test(self):
        funciones=[ [self.f1, ('parametorf1',)],   
                    [self.f2, ('par 1','par 2')],
                    [self.f3, None   ]    ]
        
        for f in funciones:
            if f[0] == self.ultima:
                self.ejecutar(f[0],f[1])

        for f in funciones:
            if f[0] != self.ultima:
                self.ejecutar(f[0],f[1])


           
    
    def ejecutar(self,fxfiltro,parametros=None):
        
        ret=None
        if parametros==None:
            l=0
        else:
            l = len ( parametros )    

        if l==0:
            ret = fxfiltro()
        elif l==1:
            ret =fxfiltro(parametros[0])    
        elif l==2:
            ret = fxfiltro(parametros[0],parametros[1])  
        elif l==3:
            ret = fxfiltro(parametros[0],parametros[1],parametros[1])      
        else:
            print ('no se ejecuta la funcion')      
        
        return ret


       


fx =  Fx()

fx.test()