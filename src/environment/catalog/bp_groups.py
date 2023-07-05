"""
Your module description
"""
import json

class BPGroups:
    def __init__(self, *initial_data, **kwargs):

        self.neo_session = None
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.response = {
            "status" : { "context":__name__,
                        "code": 0, "description": "Superseded" }
                    }
    
    # Function for list products 
    def list(self, __style:list):

        # Imports that function need for execute the operations
        from environment.catalog.styles import Styles as sys_Styles
        from os import environ as env

        # Declaration for neo and parent 
        __styles_obj = sys_Styles(neo_session = self.neo_session)
        parent_id = env['Products']

        # Cypher for this fuction, using identifier
        __cypher = '''
                match (:Products {identifier:$parent_id})-[:product]->(p:Product)-[:style]->(s:Style)
                where s.`SKU Leader` in $style
                return s, p order by s.`SKU Leader` 
                '''
        # Send Cypher query to neo session
        __result = self.neo_session.run(__cypher, parent_id = parent_id, style = __style ).data()  
        
        # Update the response with result of cypher query
        if len(__result) == 0: 
            self.response.update( { "products_catalog" : None } )
            self.response['status'].update( {"code": 1, "description": "No records found" } )
            return self.response
        
        # Create catalog list 
        __products_catalog = self.__build_catalog(__result)
         
        # Update response 
        self.response.update( { "products_catalog" : __products_catalog } )
        # Response of method
        return self.response

    # Function for view SKU list 
    def view(self, __sku:list):

        from environment.catalog.styles import Styles as sys_Styles
        __styles_obj = sys_Styles(neo_session = self.neo_session)

        from os import environ as env
        parent_id = env['Products']

        __cypher = '''
                match (:Products {identifier:$parent_id})-[:product]->(p:Product)-[:style]->(s:Style)
                where p.SKU in $sku
                return s, p order by s.`SKU Leader` 
                '''
        
        __result = self.neo_session.run(__cypher, parent_id = parent_id, sku = __sku ).data()  
        
        if len(__result) == 0: 
            self.response.update( { "products_catalog" : None } )
            self.response['status'].update( {"code": 1, "description": "No records found" } )
            return self.response
        
        __products_catalog = self.__build_catalog(__result)

        self.response.update( { "products_catalog" : __products_catalog } )
        return self.response

    # Function for create arrays with information of products
    def __build_catalog(self, __result):
        
        # Init arrays for build catalog
        __products = []
        __style = {}
        __products_catalog = []
        __tmp = {}
        
        # Create structure for catalog 
        for __item in __result:
            __prod = dict( __item['p'])
            __style = dict( __item['s'])

            # Validate if style propiety is diferente to propiety tmp
            if __style != __tmp:
                if __tmp != {}: 
                    __products_catalog.append( { 'products': __products, 'style': __tmp   }  )
                    __products = []  
                __tmp = __style        
            __products.append(__prod)

        # Get the final result
        __products_catalog.append( { 'products': __products, 'style': __style   }  )

        # Response of the method
        return __products_catalog
        