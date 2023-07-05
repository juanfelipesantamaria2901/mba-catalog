"""
Bug for name apps to Apps
"""
import json
from environment.runner import Runner
from Apps.catalog.products_catalog import Catalog


class FieldResolvers(Runner):
    def __init__(self, *initial_data, **kwargs):
        Runner.__init__(self, initial_data, kwargs)

        self.app_class = {
       "Catalog_type" : Catalog,
    }
