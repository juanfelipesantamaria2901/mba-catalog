import json
from string import Template
from environment.envrunner import EnvRunner

class Products(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.field_class = {
                   "other" : self.other,
                "products" : self.products,
                 "product" : self.product,
           "base_products" : self.base_prodcts,
                   "count" : self.count
        }
        
    def product(self):

        __identifier = self.event['source'].get('product_identifier', None)
        if __identifier is None: 
            self.response.update( { "root_result" : None } )
            return self.response
            
        __cypher = '''
                match (product:Product {identifier: $identifier})
                optional match (product)-[rel]->(child)
                where type(rel) in ['group', 'locale']
                
                return product, child, labels(product)
                '''
        __result = self.neo_session.run(__cypher, identifier = __identifier ).data()  
        
        __product_data = self.__build_product_data(__result)

        self.response.update( { "root_result" : __product_data } )
        return self.response


    def products(self):

        __identifier = self.event['source']['identifier']
        __cypher = '''
                match (product:Product)-[:style]->(style:Style)
                where style.identifier = $identifier
                return product, labels(product)
                '''
        __result = self.neo_session.run(__cypher, identifier = __identifier ).data()  
        
        __base_products = self.__build_base_products_catalog(__result)

        self.response.update( { "root_result" : __base_products } )
        return self.response

    def base_prodcts(self):

        __identifier = self.event['source']['identifier']
        __cypher = '''
                match (bundle:Product)-[base_product:base_product]->(product:Product)
                where bundle.identifier = $identifier
                return product, labels(product), base_product
                '''
        __result = self.neo_session.run(__cypher, identifier = __identifier ).data()  
        
        __base_products = self.__build_base_products_catalog(__result)

        self.response.update( { "root_result" : __base_products } )
        return self.response


    def products_list(self, __filters:list = []):

        __filters_conditions = self.filters_obj.filter_statements( 'fields', __filters )
        __page_conditions = self.filters_obj.page_statements( __filters )
        __sort_conditions = self.filters_obj.sort_statements( __filters )

        __cypher = '''
                match (lob:LOB)-[:product_catalog]->()-[:products]->()-[:product]->(parent:Product)
                match (parent)-[:locale|group]->(fields)
                
                where {filters}

                return distinct lob, parent, labels(parent)
                {sort}
                {page}
                '''
        __cypher = __cypher.format( filters = __filters_conditions, sort = __sort_conditions, page = __page_conditions )

        __result = self.neo_session.run( __cypher ).data()  
        __products_catalog = self.__build_catalog_qry(__result)

        self.response.update( { "products" : __products_catalog, "filters": __filters } )
        return self.response

    def sku_list(self, __filters:list = []):

        __filters_conditions = self.filters_obj.filter_statements( 'fields', __filters )
        __page_conditions = self.filters_obj.page_statements( __filters )
        __sort_conditions = self.filters_obj.sort_statements( __filters )

        __filter_modes_cypher = {
            "EMPTY_LIST" : '''
                with [] as prod_ids
            ''',
            "NOT_IN_ASN": '''
                match (:ASN { identifier: '$identifier' })-[:line_item]->(li:LineItem)
                with collect(li.product_identifier) as prod_ids
            ''',
            "NOT_IN_ORDER": '''
                match (:Order {identifier: '$identifier'})-[:line_item]->(li:LineItem)
                with collect(li.product_identifier) as prod_ids
            '''
        }

        __prod_ids = __filter_modes_cypher['EMPTY_LIST']
        for __filter in __filters:
            if ( __filter['mode'] in ["NOT_IN_ASN", "NOT_IN_ORDER"] and len(__filter['arguments']) == 1 ): 
                __prod_ids = Template( __filter_modes_cypher[ __filter['mode'] ] ).safe_substitute( identifier = __filter['arguments'][0] )

        __cypher = '''
            {prod_ids}
            
            match (lob:LOB)-[:product_catalog]->()-[:products]->()-[:product]->(parent:Product)
            match (parent)-[:locale|group]->(fields)
            
            match (parent)-[:locale]->(locale)
            match (parent)-[:group]->(group)
            
            where {filters} and not parent.identifier in prod_ids

            optional match (parent)-[:product_stock]->(stock:InStock)
            
            with group.SKU as title, parent.identifier as value, locale.item_description as description, false as isSelected, sum(stock.quantity) as stock_available
            with *, apoc.convert.toJson({{description:description, available:stock_available}}) as description
            return distinct *
            {sort}
            {page}
        '''
        __cypher = __cypher.format( filters = __filters_conditions, sort = __sort_conditions, page = __page_conditions, prod_ids = __prod_ids )

        __result = self.neo_session.run( __cypher ).data()  

        self.response.update( { "root_result" : [ dict(__item) for __item in __result ] } )
        return self.response


    def count(self, __filters:list = []):
        __filters = self.event['source']['filters']
        __filters_conditions = self.filters_obj.filter_statements( 'fields', __filters )

        __cypher = '''
                match (lob:LOB)-[:product_catalog]->()-[:products]->()-[:product]->(parent:Product)
                match (parent)-[:locale|group]->(fields)

                where {filters}
                with distinct parent
                return count(parent)
                '''
        __cypher = __cypher.format( filters = __filters_conditions )

        __result = self.neo_session.run( __cypher ).data()  

        self.response.update( { "root_result" : __result[0]['count(parent)'] } )
        return self.response


    def __build_base_products_catalog(self, __result):
        
        __products = []

        for __item in __result:
            __record = dict(__item['product'])
            __record.update( {'labels' : __item['labels(product)'] } )

            __products.append( __record )

        return __products

    def __build_product_data(self, __result):
        
        __product = {}

        for __item in __result:
            __product.update(dict(__item['child']) )
            __product.update( {'labels' : __item['labels(product)'] } )
            __product.update(dict(__item['product']) )

        return __product


    def __build_catalog_qry(self, __result):
        __products = []
        
        for __item in __result:
            __record = dict(__item['parent'])
            __record.update( {'labels' : __item['labels(parent)'] } )
            __record.update( {'lob' : dict(__item['lob']) } )

            __products.append( __record )

        return __products

    