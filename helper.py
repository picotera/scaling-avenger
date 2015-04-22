import logging
import sys
from ConfigParser import SafeConfigParser

def getLogger(level, name='lexis'):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    file_handler = logging.FileHandler('%s.log' %name)
    file_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
        

class Config(object):
    '''Read a user configuration file, store values in instance variables'''

    def __init__(self,f='settings.ini'):
        self.file = f
        self.parser = SafeConfigParser()
        self.updateAll()
        
    def updateAll(self):
        '''Update and store all user settings'''
        self.parser.read(self.file)
        
        self.username = self.parser.get('LEXIS', 'username')
        self.password = self.parser.get('LEXIS', 'password')
        
        self.output_dir = self.parser.get('LEXIS', 'output_dir')
        
        self.result_count = self.parser.getint('LEXIS', 'result_count') + 1
        