"""
Your module description
"""
import json
from environment.lib.unit_converter.converter import convert, converts
from environment.lib.units import dimensions
from decimal import Decimal
from environment.envrunner import EnvRunner

class Measurements(EnvRunner):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)

        from os import environ as env        
        #  VOLUMETRIC_WEIGHT_DIVISER: 5000

        self.VOLUMETRIC_WEIGHT_DIVISER = Decimal(5000)
        
        self.field_class = {
               "other" : self.other,
               "count" : self.count,
        "measurements" : self.measurements,
                "meas" : self.measurements
        }
        
    # Main Function in class 
    def measurements(self):

        __identifier = self.event['source'].get('identifier',
                            self.event['arguments'].get('identifier', '')
            )
        __weight_units = self.event['arguments'].get('weight_units', 'DEFAULT')
        __dimension_units = self.event['arguments'].get('dimension_units', 'DEFAULT')
        __filters = self.event['arguments'].get("input", [])

        __filters_conditions = self.filters_obj.filter_statements( 'dimension', __filters )
        __sort_conditions = self.filters_obj.sort_statements( __filters )
        
        __cypher = '''
                match (style:Style)-[:dimension]->(dimension)
                where style.identifier = $identifier 
                and 'Imperial' in labels(dimension) and {filters}
                return distinct labels(dimension), dimension.prod_type_id as prod_type_id, 
                    dimension.description as prod_description, dimension
                {sort}
                '''.format( filters = __filters_conditions, sort = __sort_conditions )
                
        __result = self.neo_session.run(__cypher, identifier = __identifier ).data()  
        
        __dimensions_childs = self.__build_dimensions_childs(__result)
        __dimensions_childs_with_units = self.__dimensions_units_conversion( __dimensions_childs, __weight_units, __dimension_units )
        __dimensions_childs_with_formulas = self.__dimensions_formula_fields( __dimensions_childs_with_units )
        
        self.response.update( { "root_result" : __dimensions_childs_with_formulas } )
        return self.response


    # Function for count by filters
    def count(self, __filters:list = []):
        return self.response


    # Function for build dimensions in childs products
    def __build_dimensions_childs(self, __result):
        
        __childs = []
        __childs_dict = {}
        
        for __item in __result:
            __dimension_child = {}
            __prod_type_id = __item['prod_type_id'] 
            __prod_description = __item['prod_description'] 
            __dimension = dict(__item['dimension'])
            __dimension_types = __item['labels(dimension)'] 
            
            if __prod_type_id not in __childs_dict: __childs_dict[__prod_type_id] = {}
            
            if "WEIGHT" in __dimension_types: __childs_dict[__prod_type_id].update( { "weight" : __dimension, "prod_type_id" : __prod_type_id } )
            if "DIM" in __dimension_types: __childs_dict[__prod_type_id].update( { "dimensions": __dimension, "prod_type_id" : __prod_type_id } )

            __childs_dict[__prod_type_id].update( { "prod_type_id" : __prod_type_id, "description" : __prod_description } )      
            
        for key in __childs_dict: 
            __childs.append( __childs_dict[key] )
        
        return __childs

    
    # Function for convert units of dimension 
    def __dimensions_units_conversion(self, __results_list, __weight_units_arg, __dimension_units_arg):
        
        for __item in __results_list: 
            
            if "weight" in __item:
                __weight_units = __item['weight'].get('preferred_units') if __weight_units_arg == 'DEFAULT' else __weight_units_arg
                
                if __weight_units != __item['weight'].get('units', __weight_units ):
                    #convert here
                    __item['weight']['weight'] = self.__convert(__item['weight']['weight'], __item['weight']['units'], __weight_units )
                    __item['weight']['units'] = __weight_units
                __item['weight']['weight'] = round( __item['weight']['weight'], 4)  
                
            if "dimensions" in __item:
                __dimension_units = __item['dimensions'].get('preferred_units') if __dimension_units_arg == 'DEFAULT' else __dimension_units_arg
                if __dimension_units != __item['dimensions'].get('units', __dimension_units ):
                    #convert here
                    __item['dimensions']['width'] =  self.__convert(__item['dimensions']['width'], __item['dimensions']['units'], __dimension_units ) 
                    __item['dimensions']['height'] = self.__convert(__item['dimensions']['height'], __item['dimensions']['units'], __dimension_units )
                    __item['dimensions']['depth'] = self.__convert(__item['dimensions']['depth'], __item['dimensions']['units'], __dimension_units )
                    __item['dimensions']['units'] = __dimension_units

                __item['dimensions']['width'] = round( __item['dimensions']['width'], 4)  
                __item['dimensions']['height'] = round( __item['dimensions']['height'], 4)  
                __item['dimensions']['depth'] = round( __item['dimensions']['depth'], 4)  
                
            __weight_units = ''
            __dimension_units = ''
        return __results_list


    # Function for dimensions 
    def __dimensions_formula_fields(self, __results_list):
        __output = []
        for __current_item in __results_list: 
            __item = __current_item.copy()
            if "dimensions" in __item:
                if None not in [ __item['dimensions'].get('width', None),
                                 __item['dimensions'].get('height', None),
                                 __item['dimensions'].get('depth', None) ]:

                    __item['volume'] = self.__calculate_volume (__item['dimensions'].copy())

                    __item['volume_units'] = "{value} ³".format( value=__item['dimensions']['units'] ) 

                    if __item['dimensions']['units'] in ['IN', 'FT']: 
                        __item['volumetric_weight'] = self.__calculate_volume (__item['dimensions'].copy(), "IN") / self.VOLUMETRIC_WEIGHT_DIVISER
                        __item['volumetric_weight_units'] = 'LB'

                    if __item['dimensions']['units'] in ['MM', 'CM', 'M']: 
                        __item['volumetric_weight'] = self.__calculate_volume (__item['dimensions'].copy(), "CM") / self.VOLUMETRIC_WEIGHT_DIVISER #305
                        __item['volumetric_weight_units'] = 'KG'
                        
                    __item['volume'] = float('{0:.4f}'. format(__item['volume']) )
                    __item['volumetric_weight'] = float('{0:.4f}'. format(__item['volumetric_weight']) )
                    
            if ( "volumetric_weight" in __item and "weight" in __item ):
                if __item['weight'].get('weight', None) is not None:
                    __weight_kg = self.__convert(__item['weight']['weight'], __item['weight']['units'], __item['volumetric_weight_units'] ) 
                    __item['preferred'] = __weight_kg if __weight_kg > __item['volumetric_weight'] else __item['volumetric_weight']
                    
                    __item['preferred'] = float('{0:.4f}'. format(__item['preferred']) )
                    __item['preferred_units'] = __item['volumetric_weight_units']
            __output.append(dict(__item))
        return __output
        

    # Function for calculate by volumen
    def __calculate_volume(self, __dimensions:dict, __units:str = None):

        __new_dims = {}
        if __units is not None:
            __new_dims['width'] =  self.__convert(__dimensions['width'], __dimensions['units'], __units ) 
            __new_dims['height'] = self.__convert(__dimensions['height'], __dimensions['units'], __units ) 
            __new_dims['depth'] = self.__convert(__dimensions['depth'], __dimensions['units'], __units ) 
    
            return  (__new_dims['width'] * __new_dims['height'] * __new_dims['depth'] )

        return  (__dimensions['width'] * __dimensions['height'] * __dimensions['depth'] )
                
                
    def __convert(self, __value, __unitsFrom, __unitsTo):
        
        return Decimal( convert( "{qty} {units}".format(qty = __value, 
                                                        units = dimensions[__unitsFrom] ),
                                                        dimensions[__unitsTo]  )  )
                                                        