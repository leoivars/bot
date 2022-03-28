import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

def inicio():
    print "inicio"
    enviar_correo("Test","Esto es una Prueba")

def enviar_correo(titulo,mensaje):
    
    fromaddr = 'jcgonzales1981@gmail.com'
    toaddrs  = 'leoivars@gmail.com'
    
    # Datos
    username = 'jcgonzales1981@gmail.com'
    password = '1qazXSW"'
 
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddrs
    msg['Subject'] = titulo
    msg.attach(MIMEText(mensaje, 'plain'))

    # Enviando el correo
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.ehlo()
    server.login(username,password)
    text=msg.as_string()
    problems = server.sendmail(fromaddr, toaddrs, text)
    server.quit()
    print problems
    

inicio()