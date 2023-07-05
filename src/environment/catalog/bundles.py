"""
Your module description
"""
import json


class Bundles:
    def __init__(self, *initial_data, **kwargs):
        self.neo_session = None
        self.source = None
        self.event = {}
        
        for dictionary in initial_data:
            for key in dictionary: setattr(self, key, dictionary[key])
        for key in kwargs: setattr(self, key, kwargs[key])

        self.response = {
            "status" : { "context":__name__,
                        "code": 0, "description": "Superseded" }
                    }
    
        self.field_class = {
             "other" : self.other,
             "count" : self.other,
     "base_products" : self.other
        }

    # Function for init event    
    def run(self):  
        __field_class = self.field_class.get ( self.event['info']['fieldName'], self.other )
        return __field_class()

    # Function for uotdate response for other request
    def other(self):
        self.response.update( { "root_result" : None } )
        return self.response


    # Function for list by base product
    def list(self, __sku_list:list):
        # Imports 
        from os import environ as env
        # Declare variables
        parent_id = env['Products']
        # Cypher query for function
        __cypher = '''
                match (p:Products {identifier:$parent_id})
                match (p)-[:product]->(bundle:Product)-[base_product:base_product]->(product:Product)
                where bundle.SKU in $sku_list
                return product, bundle, base_product
                '''
        # Send cypher query to neo 
        __result = self.neo_session.run(__cypher, parent_id = parent_id, sku_list = __sku_list ).data()  
        # Set data in response
        if len(__result) == 0: 
            self.response.update( { "products_catalog" : None } )
            self.response['status'].update( {"code": 1, "description": "No records found" } )
            return self.response
        # Create catalog
        __products_catalog = self.__build_catalog(__result)
        # Set response with catalog of products
        self.response.update( { "products_catalog" : __products_catalog } )
        # Response of method
        return self.response


    # Function for view by SKU code 
    def view(self):
        # Imports 
        from os import environ as env
        # Set parent_id
        parent_id = env['Products']
        if self.source == None: 
            self.response.update( { "root_result" : [] } )
            return self.response
        # Set SKU code 
        __sku = self.source.get('SKU', None)
        if __sku is None: 
            self.response.update( { "root_result" : [] } )
            return self.response
        # Cypher query for fucttion
        __cypher = '''
                match (p:Products {identifier:$parent_id})
                match (p)-[:product]->(bundle:Product)-[base_product:base_product]->(product:Product)
                where bundle.SKU = $sku
                return product.SKU as SKU, base_product.count as count
                '''
        # Send cypher to neo
        __result = self.neo_session.run(__cypher, parent_id = parent_id, sku = __sku ).data()  
        # Set data with result of neo
        if len(__result) == 0: 
            self.response.update( { "root_result" : [] } )
            return self.response
        # Create catalog
        __base_products = self.__build_catalog(__result)
        # Update response 
        self.response.update( { "root_result" : __base_products } )
        # Response of the method
        return self.response

    
    def __build_catalog(self, __result):

        __products_catalog = []

        for __item in __result:
            __products_catalog.append( dict( __item ) )

        return __products_catalog
        