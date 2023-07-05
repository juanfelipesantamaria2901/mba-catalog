"""
Your module description
"""
from environment.envrunner import EnvRunner

class Groups(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        self.field_class = {
                   "other" : self.other,
                   "group" : self.group_fields
        }
        

    def group_fields(self):

        __identifier = self.event['source']['identifier']
        __source_labels = self.event['source'].get('labels', [])
        __group = self.event['arguments']['name']
        __keys = self.event['arguments'].get('items', [])

        __labels = "" if len(__source_labels)==0 else f":{':'.join(__source_labels)}"

        if __keys == None: __keys = []
        __key_list = '__all_keys' if len(__keys) == 0 else ','.join("__all_keys.`%s` as `%s`" % (s, s) for s in __keys )

        __cypher = '''
                match (parentNode{labels} {{identifier:$identifier}})
                optional match (parentNode)-[]->(__all_keys)
                    where {group!r} in labels(__all_keys) or __all_keys.name = {group!r} 

                return {keys}
                '''
                
        __cypher = __cypher.format( group = __group, keys=__key_list, labels = __labels )
        __result = self.neo_session.run( __cypher, identifier = __identifier ).data()  

        self.response.update( { "root_result" : self.__build_group_fields_list(__result) } )
        return self.response


    def __build_group_fields_list(self, __result) -> list:
        
        __system_keys = ['identifier', 'created', 'disabled_date', 'updated', 'name']
        __results_output = []
        if "__all_keys" in __result[0]: 
            for __item in __result:
                __item_dict = dict(__item['__all_keys'])
                list( map(__item_dict.__delitem__, filter(__item_dict.__contains__, __system_keys) ) )
                __results_output.extend( [ { "item": k, "value": v} for k,v in __item_dict.items() ] )
            
            return __results_output

        for __item in __result:
            __results_output.extend( [ { "item": k, "value": v} for k,v in dict(__item).items() ] )
        
        return __results_output

