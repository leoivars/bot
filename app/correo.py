import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pws import Pws

#from logger import *

class Correo:
    def __init__(self,log):
        
        pws=Pws()
        self.fromaddr = pws.mail_user
        self.toaddrs  = pws.mail_to
        self.username = pws.mail_user
        self.password = pws.mail_pass
        self.log = log
        self.send_mails = 'YES' == os.getenv('BOT_SEND_MAILS', 'YES') 

    def enviar_correo(self,titulo,mensaje):
        if not self.send_mails:
            return
    
        msg = MIMEMultipart()
        msg['From'] = self.fromaddr
        msg['To'] = self.toaddrs
        msg['Subject'] = titulo
        msg.attach(MIMEText(mensaje, 'plain'))

        try:
            # Enviando el correo
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.ehlo()
            server.login(self.username,self.password)
            text=msg.as_string()
            problems = server.sendmail(self.fromaddr, self.toaddrs, text)
            server.quit()
            #self.log.log("Correo: "+ problems)
        except Exception as e:
                self.log.log( "Error al enviar Correo",str(e) )
                print( "Error en Correo:",titulo,mensaje)
                print(e)
                