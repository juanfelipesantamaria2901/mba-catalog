"""
Your module description
"""

from os import environ as env
import json, logging

class Config:
    def __init__(self, *initial_data, **kwargs):
        self.logger=logging.getLogger(__name__)
        self.config_file = "config.json"
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def load(self, config_file = None):
        api_json_file = config_file
        with open(api_json_file) as json_file:
            api_env_data = json.load(json_file)
            self.logger.debug(api_env_data)
            
            env.update(api_env_data)

        return True
        
    def data(self, config_file = None):
        if config_file == None: config_file = self.config_file
        if config_file == None: return None

#        try:
        with open(config_file) as json_file:
            api_env_data = json.load(json_file)
            #self.logger.debug(api_env_data)
            return api_env_data
#        except:
#            return None
            
        return None
        