"""
Your module description
"""
import json
from environment.envrunner import EnvRunner

class Styles(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.field_class = {
               "other" : self.other,
               "count" : self.count,
               "styles": self.list_resolver
        }
        
        
    def list(self, __filters:list = []):

        __filters_conditions = self.filters_obj.filter_statements( 'style', __filters )
        __page_conditions = self.filters_obj.page_statements( __filters )
        __sort_conditions = self.filters_obj.sort_statements( __filters )

        __cypher = '''
                match (:LOBS)-[:lob]->(lob:LOB)-[*3]->(style:Style)-[:locale]->(locale:Locale)
                where {filters}
                return lob, style, locale, labels(style), labels(locale)
                {sort}
                {page}
                '''
                
        __cypher = __cypher.format( filters = __filters_conditions, sort = __sort_conditions, page = __page_conditions )

        __result = self.neo_session.run( __cypher ).data()  
        __styles_catalog = self.__build_catalog_qry(__result)
        
        self.response.update( { "style" : __styles_catalog, "filters": __filters } )
        return self.response


    def count(self, __filters:list = []):
        __filters = self.event['source']['filters']
        __filters_conditions = self.filters_obj.filter_statements( 'style', __filters )

        __cypher = '''
                match (:LOBS)-[:lob]->(lob:LOB)-[*3]->(style:Style)-[:locale]->(locale:Locale)
                where {filters}
                return count(style)
                {page}
                '''
                
        __cypher = __cypher.format( filters = __filters_conditions, page = '' )

        __result = self.neo_session.run( __cypher ).data()  

        self.response.update( { "root_result" : __result[0]['count(style)'] } )
        return self.response


    def list_resolver(self, __filters:list = []):

        __identifier = self.event['source']['identifier']

        __cypher = '''
                match (product:Product)-[:style]->(style:Style)-[:locale]->(locale:Locale)
                where product.identifier = $identifier
                return style, locale, labels(style), labels(locale)
                '''
                
        __result = self.neo_session.run( __cypher, identifier = __identifier  ).data()  
        __styles_catalog = self.__build_catalog_qry(__result)
        
        self.response.update( { "root_result" : __styles_catalog } )
        return self.response


    def __build_catalog_qry(self, __result):
        __styles = []
        
        for __item in __result:
            __record = dict(__item['style'])
            __record.update( {'locale' : dict(__item['locale']) } )
            __record.update( {'labels' : __item['labels(style)'] } )
            __record.update( {'lob' : dict(__item.get('lob', {}) ) } )

            __styles.append( __record )

        return __styles

