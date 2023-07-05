"""
Your module description
"""
import json
from environment.runner import Runner

class Bundles(Runner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.app_class = {
            "list" : self.list,
            "fun" : self.fun,
            "view" : self.view
        }
    
    def list(self):
        if not self.session.valid_sid()  : return self.error( "invalidSession")
        if not self.session.valid_auth() : return self.error( "invalidAuthorization")

        __param1 = self.event['arguments'].get("style", None)
        if __param1 == None: return self.error( "missingParameters")

        from environment.catalog.products import Products as sys_Products
        __products = sys_Products(neo_session = self.neo_session)
        __products_list = __products.list(__param1)

        self.response.update( {'products_catalog' : __products_list['products_catalog'] } )
        return self.back()

    def view(self):
        if not self.session.valid_sid()  : return self.error( "invalidSession")
        if not self.session.valid_auth() : return self.error( "invalidAuthorization")

        __param1 = self.event['arguments'].get("sku", None)
        if __param1 == None: return self.error( "missingParameters")

        from environment.catalog.products import Products as sys_Products
        __products = sys_Products(neo_session = self.neo_session)
        __products_list = __products.view(__param1)

        self.response.update( { 'products_catalog' : __products_list['products_catalog'] } )
        return self.back()

    def fun(self):
        self.response.update( {'data' : 'Have fun!' } )
        return self.back()
        
        
