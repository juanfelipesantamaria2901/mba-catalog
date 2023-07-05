"""
Your module description
"""
import json
from environment.runner import Runner
from environment.catalog.styles import Styles as styles_class
from environment.catalog.resources import Resources as resources_class
from environment.catalog.products import Products as products_class
from environment.catalog.measurements import Measurements as measurements_class

class Styles(Runner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.app_class = {
            "list" : self.list,
        "list_qry" : self.list,
       "__resolve" : self.resolve
        }

        self.field_class = {
              "default" : styles_class,
               "images" : resources_class,
                "count" : styles_class,
             "products" : products_class,
         "measurements" : measurements_class,
                 "meas" : measurements_class
        }

    # API conect list for styles
    def list(self):

        __filters = self.event['arguments'].get("input", [])

        __styles_obj = self.field_class['default'] (neo_session = self.neo_session, event = self.event)
        __styles_list = __styles_obj.list(__filters)

        self.response.update( __styles_list )

        return self.back()

