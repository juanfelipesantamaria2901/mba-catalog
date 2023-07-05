"""
Your module description
"""
import json
from environment.runner import Runner

from Apps.catalog.products import Products
from Apps.catalog.styles import Styles
from Apps.catalog.composites import Composites
from Apps.catalog.bundles import Bundles

class Catalog(Runner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.app_class = {
            "products" : Products,
            "composites" : Composites,
            "bundles" : Bundles,
            "styles" : Styles
        }
    


