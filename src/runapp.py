"""
Your module description
"""
import json, logging
from Apps.catalog.products_catalog import Catalog
from environment.system.apps import Apps
from Apps.field_resolvers.field_resolvers import FieldResolvers
from environment.runner import Runner as RNR

class RunApp(RNR):
    def __init__(self, *initial_data, **kwargs):
        super().__init__(*initial_data, **kwargs)
        self.logger=logging.getLogger(__name__)
        # app_class is the dictionary that has all the main class references (commands root members)
        self.app_class = {
                  "catalog" : Catalog,
                  "apps" : Apps,
        "__field_resolvers" : FieldResolvers
        }
        
    # Override run() function from runner abstract class
    def run(self, *initial_data, **kwargs):
        # Load *initial_data and **kwargs parameters
        self.load_parameters(self, initial_data, kwargs)
        
        return self.__appsync_event ()

    # Execute AppSync events payloads
    def __appsync_event(self):
        # event payload verification
        #if not self.event_payload_validation( self.event ): return self.error( "missingParameters")
        self.event['headers'] = self.event['request']['headers']
        
        # define a field resolver command (field) by default
        self.event['field'] = "__field_resolvers.{parent_schema}.__resolve".format(
                        parent_schema = self.event['info'].get("parentTypeName", "__other" )
                    )

        # if source is empty then it is a root function (not a field resolver)
        # so, take the command from the payload
        if self.event['source'] in [ None, 'None' ]:
            if "command" not in self.event['arguments']: 
                return self.error( "missingParameters", __file__)

            self.event['field'] = self.event['arguments']['command']

        # log output
        self.logger.debug("COMMAND: %s", self.event['field'] )
        self.logger.debug("HEADERS:\n%s", self.event['headers'] )
        self.logger.debug("IDENTITY:\n%s", self.event['identity'] )
        self.logger.debug("ARGUMENTS:\n%s", self.event['arguments'] )

        if not self.__access_check(): 
            return self.error( "accessDenied" )

        # return to runner (RNR) abstract class 
        return RNR.run(self)


    def other(self):
        return {}
    
    def __access_check(self):
        
        __role = json.loads( self.event.get('identity', {}).get('resolverContext', {}).get('access_role', "{}") or "{}" )

        self.logger.info('ACCESS ROLE: %s', __role.get('role', 'Unknown') )

        if any( item in ['__ALL__', self.event['field'] ] for item in __role.get('denied_functions', []) ):

            self.logger.info(' ** ACCESS_DENIED **' )
            return False


        if any( item in ['__ALL__', self.event['field'] ] for item in __role.get('allowed_functions', []) ):

            self.logger.info(' ** ACCESS_GRANTED **' )
            return True
        
        return True