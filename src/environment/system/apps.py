"""
Your module description
"""
import json

class Apps:
    def __init__(self, *initial_data, **kwargs):

        self.neo_session = None
        self.apps_list = []
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.response = {
            "status" : { "context":__name__,
                        "code": 0, "description": "Superseded" }
                    }

    def list(self):

        __cypher = '''
                match (apps :Apps)-[:app]->(app:App)
                where app.disabled_date = 0
                return app
                '''
        
        __result = self.neo_session.run(__cypher).data()  
        __apps_list = self.__build_catalog(__result)
        
        self.response.update( { "Apps" : __apps_list } )
        return self.response
    
    def view(self, __apps:list):

        __cypher = '''
                match (apps :Apps)-[:app]->(app:App)
                where app.disabled_date = 0 and app.appid in $apps
                return app
                '''
        
        __result = self.neo_session.run(__cypher, apps = __apps ).data()  

        if len(__result) == 0:
            self.response['status'].update( {"code": 1, "description": "Record not found"} )
            self.response.update( {"Apps" : None } )
            return self.response
        
        __apps_catalog = self.__build_catalog(__result)
        
        self.response.update( { "Apps" : __apps_catalog } )
        return self.response

    def valid_app(self, __appid:str):
        __apps_list = self.list()['Apps']
        for i in __apps_list:
            if i['appid'] == __appid: return True 
        
        return False

    def __build_catalog(self, __result):
        __items = []
        
        for __item in __result:
            __record = dict(__item['app'])
            __items.append( __record )

        return __items
