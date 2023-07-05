"""
Your module description
"""
import json,logging
from environment.envrunner import EnvRunner

class Metadata(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.logger=logging.getLogger(__name__)
        self.field_class = {
                   "other" : self.other,
         "groups_metadata" : self.groups_metadata,
                "metadata" : self.metadata_lob
        }

    def metadata_lob(self, __filters:list = []):
        __groups = self.event['arguments'].get('groups', [])
        __filters = self.event['source']['filters']
        __filters_conditions = self.filters_obj.filter_statements( 'fields', __filters )

        __cypher = '''
                match (:LOBS)-[:lob]->(lob:LOB)-[*3]->(product:Product)
                match (product)-[*1]->(fields)
                match (lob)-[*2]->(products:Products)
                
                where {filters}
                return DISTINCT lob.lob_identifier as lob,  products.identifier as identifier, $groups as groups
                '''
        __cypher = __cypher.format( filters = __filters_conditions )

        __result = self.neo_session.run( __cypher, groups = __groups ).data()  

        __rslt = [ dict(__item) for __item in __result ]

        self.response.update( { "root_result" : __rslt } )
        return self.response

    def groups_metadata(self, __filters:list = []):

        __identifier = self.event['source']['identifier']
        __groups = self.event['arguments'].get('groups', 
                    self.event['source'].get('groups', 
                    self.event['info']['variables'].get('groups', []) ) )
        
        __keys = self.event['arguments'].get('items', [])

        if __keys == None: __keys = []
        if __groups == None: __groups = []
        __key_list = '__all_keys' if len(__keys) == 0 else ','.join("__all_keys.`%s` as `%s`" % (s, s) for s in __keys )

        __cypher = '''
                match (parentNode {{identifier:$identifier}})
                match (parentNode)-[:metadata]->(__all_keys:Metadata)
                    where __all_keys.name in $groups 
                return DISTINCT {keys}
                '''

        __cypher = __cypher.format( keys= __key_list )

        __result = self.neo_session.run( __cypher, identifier = __identifier, groups = __groups ).data()  

        self.response.update( { "root_result" : self.__build_metadata_list(__result) } )
        return self.response

    def __build_metadata_list(self, __result) -> list:
        self.logger.info("EMPTY METADATA GROUPS")
        if len(__result) == 0: return []
        
        __system_keys = ['identifier', 'created', 'disabled_date', 'updated']
        __results_output = []
        if "__all_keys" in __result[0]: 
            for __item in __result:
                __item_dict = dict(__item['__all_keys'])
                list( map(__item_dict.__delitem__, filter(__item_dict.__contains__, __system_keys) ) )
                
                __group = __item_dict['name']
                del __item_dict['name']
                __tmp_keys = [ json.loads(v) for k,v in __item_dict.items() ]
                __results_output.append( { "group": __group, "items": __tmp_keys  } )
            
            return __results_output

        for __item in __result:
            __results_output.extend( [ { "item": k, "value": v} for k,v in dict(__item).items() ] )
        
        return __results_output

