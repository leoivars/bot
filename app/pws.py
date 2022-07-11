import os

class Pws:
    def __init__(self):
        self.api_key = os.getenv('API_KEY', '?')
        self.api_secret = os.getenv('API_SECRET', '?')
        self.mail_user=os.getenv('MAIL_USER', '?')
        self.mail_pass=os.getenv('MAIL_PASS', '?')
        self.mail_to=os.getenv('MAIL_TO', '?')
        self.db_user= os.getenv('DB_USER', '?')
        self.db_pass= os.getenv('DB_PASS', '?' )
        self.db_host= os.getenv('DB_HOST', '?')
        
        
       

