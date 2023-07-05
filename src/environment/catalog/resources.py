"""
Your module description
"""
import json
from environment.envrunner import EnvRunner

class Resources(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.field_class = {
            "other" : self.other,
            "style_type" : self.style_type,
            "product_type" : self.product_type,
            "user_type" : self.user_type,
            "lob_type" : self.lob_type,
            "distchann_type" : self.distchann_type,
            "locations_type" : self.locations_type
        }
        from os import environ as env
        self.cdn_base_url = env['CDN_BASE_URL']

    def run(self):
        __field_class = self.field_class.get ( self.event['info']['parentTypeName'], self.other )
        return __field_class()
    

    def style_type(self):

        __url = "{base_url}/resource/{group}/{lob}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                lob = self.event['source']['lob']['lob_identifier'],
                                item = self.event['source']['sku_leader'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response


    def product_type(self):
        
        __url = "{base_url}/resource/{group}/{lob}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                lob = 'gir', #self.event['source']['lob']['lob_identifier'],
                                item = self.event['source']['SKU'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response
        

    def user_type(self):
        
        __url = "{base_url}/resource/{group}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                item = self.event['source']['identifier'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response


    def lob_type(self):
        
        __url = "{base_url}/resource/{group}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                item = self.event['source']['name'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response


    def distchann_type(self):
        
        __url = "{base_url}/resource/{group}/{lob}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                lob = self.event['source']['lob']['lob_identifier'],
                                item = self.event['source']['identifier'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response


    def locations_type(self):
        
        __url = "{base_url}/resource/{group}/{warehouse}/{item}?{param}".format(
                                base_url = self.cdn_base_url,
                                group = self.event['info']['parentTypeName'],
                                warehouse = self.event['source']['warehouse']['warehouse_identifier'],
                                item = self.event['source']['identifier'],
                                param = self.event['arguments']['preset']
                                )
        
        self.response.update( { "root_result" : [ __url ] } )
        return self.response
