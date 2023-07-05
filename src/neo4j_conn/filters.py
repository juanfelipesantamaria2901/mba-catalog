from abc import ABC, abstractmethod
import logging

class FilterMode(ABC):
    
    @abstractmethod
    def __init__(self, cypher_statement:str):
        self.cypher_statement = cypher_statement
        self.node=''
        self.filter_statement=[]
        self.filter_statement_num=[]

    def set_filter_payload(self, node:str, filter_statement:list, filter_statement_num:list):
        self.node=node
        self.filter_statement=filter_statement
        self.filter_statement_num=filter_statement_num

    def is_valid(self):
        return self.filter_statement is not None and len(self.filter_statement)>0

    @abstractmethod
    def generate_cypher(self) -> str:
        pass

class NodeNValueFilterMode(FilterMode):

    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

    def generate_cypher(self):
        return self.cypher_statement.format( m =self.node, *self.filter_statement)


class NodeNListFilterMode(FilterMode):

    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

    def generate_cypher(self):
        return self.cypher_statement.format( m = self.node, values = ".*|.*".join( self.filter_statement ) )


class InListStrFilterMode(FilterMode):

    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

    def generate_cypher(self):
        return self.cypher_statement.format( ", ".join( map(lambda e: f"\'{e}\'" ,self.filter_statement) ) )

class FieldFilterMode(FilterMode):
    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

    def generate_cypher(self):
        return self.cypher_statement.format( m = self.node, values = " and ".join( self.filter_statement ) )


class SessionFilterMode(NodeNValueFilterMode):
    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

class FromToFilterMode(FilterMode):
    def __init__(self, cypher_statement):
        super().__init__(cypher_statement)

    def is_valid(self):
        return (self.filter_statement is not None and len(self.filter_statement)>0 and 
        self.filter_statement_num is not None and len(self.filter_statement_num)>0)

    def generate_cypher(self):
        return self.cypher_statement.format( *self.filter_statement, *self.filter_statement_num)


class Filters:
    def __init__(self, *initial_data, **kwargs):
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.logger = logging.getLogger(__name__)

        self.modes:'dict[str,FilterMode]' = {
            "EXACT": NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i)^{}$' )"),
            "CONTAINS": NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{}.*' )"),
            "STARTS" : NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i)^{}.*' )"),
            "ENDS" : NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{}$' )"),
            
            "NOT_CONTAINS" : NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{}.*' ) is null"),
            "NOT_STARTS" : NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i)^{}.*' ) is null"),
            "NOT_ENDS" : NodeNValueFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{}$' ) is null"),
                        
            "IDENTIFIER" : NodeNValueFilterMode("( parent.`identifier` = {0!r} or parent.`object_identifier` = {0!r} )"),
            "LOCATION_MIXING" : NodeNValueFilterMode("child.`mixing` = toBoolean({0})"),
            "LOCATION_PICKABLE" : NodeNValueFilterMode("child.`pickable` = toBoolean({0})"),
            "PRODUCT" : NodeNValueFilterMode("product.`identifier` = {0!r}"),

            "IN" : NodeNListFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{values}.*' )"),
            "NOT_IN" : NodeNListFilterMode("any(prop in keys({m}) where {m}[prop] =~ '(?i).*{values}.*' ) is null"),
            "LOB_IN" : NodeNListFilterMode("any(prop in keys(lob) where lob[prop] =~ '(?i).*{values}.*' )"),
            "CHANNEL_IN" : NodeNListFilterMode("any(prop in keys(channel) where channel[prop] =~ '(?i).*{values}.*' )"),

            "LABEL" : NodeNListFilterMode("labels({m}) =~ '(?i).*{values}.*' "),
            "LABEL_NOT" : NodeNListFilterMode("NOT labels({m}) =~ '(?i).*{values}.*' "),

            "WAREHOUSE" : NodeNListFilterMode("warehouse.`identifier` =~ '(?i).*{values}.*' "),
            "WAREHOUSE_NAME" : NodeNListFilterMode("parent.`name` =~ '(?i).*{values}.*' "),
            "LOCATION" : NodeNListFilterMode("{m}.`location_identifier` =~ '(?i).*{values}.*' "),
            "LOCATION_TYPE" : NodeNListFilterMode("child.`type` =~ '(?i).*{values}.*' "),
            "LOCATION_ZONE" : NodeNListFilterMode("child.`zone` =~ '(?i).*{values}.*' "),
            "LOCATION_NAME" : NodeNListFilterMode("child.`name` =~ '(?i).*{values}.*' "),
            "STOCK_LOCATION" : NodeNListFilterMode("stock_item.`location_identifier` =~ '(?i).*{values}.*' "),

            "ASN_STATUS" : NodeNListFilterMode("child.`asn_status` =~ '(?i).*{values}.*' "),
            "ASN_TYPE" : NodeNListFilterMode("child.`asn_type` =~ '(?i).*{values}.*' "),
            "CARRIER_TYPE" : NodeNListFilterMode("child.`carrier_type` =~ '(?i).*{values}.*' "),

            "FIELDS" : FieldFilterMode(" {values} "),
            "FORMULA" : FieldFilterMode(" {values} "),

            "USER_AGENT" : SessionFilterMode("{m}.`user-agent` contains {!r}"),
            "APPID" : SessionFilterMode("{m}.`appid` = {!r}"),

            "BETWEEN" : FromToFilterMode("child.{0} >= {1} and child.{0} <= {2}")
        }
    

    def filter_statements(self, __node:str, __filters:'list[dict]'):
        
        __statements_list:'list[str]' = []
        for __filter in __filters:
            __filter_mode = __filter.get('mode', None)
            if __filter_mode is None:
                continue
            
            __filter_instance = self.modes.get(__filter_mode,None)
            if __filter_instance is None:
                continue

            __filter_statement = __filter.get('arguments', [])
            __filter_statement_num = __filter.get('arguments_num', [])

            __filter_statement = [n for n in __filter_statement if n != ""] #filter out empty filters

            __filter_instance.set_filter_payload(__node,__filter_statement,__filter_statement_num)
            
            if not __filter_instance.is_valid():
                continue
            try:
                __statements_list.append(__filter_instance.generate_cypher())
            except:
                self.logger.warning("filter_error:\n%s", __filter)
                
        self.logger.debug('___filters:\n%s', __statements_list)
        
        return ' AND '.join(__statements_list) if len(__statements_list) > 0 else 'True'
        
    def page_statements(self, __filters:list):
        '''
        This is a new function
        '''
        __modes = {
            "PAGE" : "SKIP {from_row} LIMIT {page_size}"
        }
        __statements_list = []
        for __filter in __filters:
            __filter_mode = __filter.get('mode', None)

            try:
                if __filter_mode == "PAGE":
                    __filter_statement = __filter.get('arguments_num', [])
                    __statements_list.append(
                        __modes.get(__filter_mode, '').format( from_row = int( (__filter_statement[0] - 1) * __filter_statement[1] ), 
                                                           page_size = int( __filter_statement[1] ) ) 
                    )
            except:
                self.logger.warn("page_filter_error:\n%s", __filter)
                True
        
        self.logger.debug('___page:\n%s', __statements_list)
        
        return ' '.join(__statements_list)    
        
    def sort_statements(self, __filters:list):
        '''
        This is a new function
        '''
        __modes = {
            "SORT" : "ORDER BY {values}"
        }
        __statements_list = []
        for __filter in __filters:
            __filter_mode = __filter.get('mode', None)
            __filter_statement = __filter.get('arguments', [])

            try:
                __statements_list.append(
                        __modes.get(__filter_mode, '').format( values = ", ".join( __filter_statement ).replace(', DESC', ' DESC') ) 
                    )
                    
            except:
                self.logger.warn("sort_filter_error:\n%s", __filter)
                True
        
        self.logger.debug('___sort:\n%s', __statements_list)
        
        return ' '.join(__statements_list)