from environment.runner import Runner
from environment.catalog.products import Products as products_class
from environment.catalog.bundles import Bundles as bundles_class
from environment.catalog.resources import Resources as resources_class
from environment.catalog.styles import Styles as styles_class

from environment.system.groups import Groups as groups_class
from environment.system.metadata import Metadata as metadata_class

class Products(Runner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.app_class = {
            "list" : self.products_list,
        "sku_list" : self.sku_list,
       "__resolve" : self.resolve
        }

        self.field_class = {
             "default" : products_class,
            "products" : products_class,
              "styles" : styles_class,
       "base_products" : products_class,
              "images" : resources_class,
               "count" : products_class,
               "group" : groups_class,
      "groups_metadata": metadata_class,
             "metadata": metadata_class
        }
 
    # API for products lists
    def products_list(self):

        __filters = self.event['arguments'].get("input", [])

        __env_obj:products_class = self.field_class['default'] (neo_session = self.neo_session, event = self.event)
        __results_list = __env_obj.products_list(__filters)

        self.response.update( __results_list )

        return self.back()

    # API for SKU list
    def sku_list(self):

        __filters = self.event['arguments'].get("input", [])

        __env_obj:products_class = self.field_class['default'] (neo_session = self.neo_session, event = self.event)
        __results_list = __env_obj.sku_list(__filters)

        self.response.update( __results_list )

        return self.back()

