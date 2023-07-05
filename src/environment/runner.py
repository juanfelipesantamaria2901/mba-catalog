"""
Your module description
"""
import importlib, inspect, logging
from os import path
from environment.system.config import Config
from environment.system.events import Events
from environment.lib.system_objects_bundle import ObjectsBundle

class Runner:
    def __init__(self, *initial_data, **kwargs):
        self.neo_session = None     # Neo4j session object
        self.event = {}             # event payload dictionary
        self.config = {}            # child class json dictionaly
        self.event_bus = None
        self.logger = logging.getLogger(__name__)
        self.image_processor = None
        self.system_objects:ObjectsBundle = None

        for dictionary in initial_data:
            for key in dictionary: setattr(self, key, dictionary[key])
        for key in kwargs: setattr(self, key, kwargs[key])
        
        self.app_class = {}         # Initialize class references dictionary 
        self.field_class = {}       # Initialize field resolvers references dictionary 
        self.response = {}
        self.response:dict[str,Any] = {            # Default error response
            "status" : {
                "statusCode": 200, "code": 0, "description": "Superseded",
                "errorType": None, "errorInfo": self.__class__.__name__, "message": None, "debug_info": None}
        }
        
        # Define the child json file if any
        __class_module = importlib.import_module(self.__module__)
        __json_file = __class_module.__file__.replace(".py", ".json")
        
        # Output log the child class name/path
        self.logger.debug("loading: %s %s", self.__class__.__name__, __class_module.__file__ )
    
        # Load the child json file if any
        if path.exists(__json_file):
            __config = Config(config_file = __json_file )
            self.config.update( __config.data() )

        # API Events Object            
        self.api_events = Events()

    def load(self, query:dict, labels:list = None):
        
        return self.back()
        
    def run(self, event:dict = {}):
        
        __field = self.event.get("field", None)                 # Get the field (Command)
        __class_name = __field.split(".", 1)                    # Split it and convery to a list
        __class_obj = self.app_class.get(__class_name[0], None) # Use the first list member to get the object reference 
                                                                # from the app_class dictionary
        
        if __class_obj == None : return self.__not_found( __class_obj )   # if any then return error

        self.event['field'] = __class_name[1] if len( __class_name ) == 2 else ''   # Remove the first memeber from the command list
                                                                                    # and define a new field (command)
        if str(type(__class_obj)) == "<class 'method'>" :       # if the object definition its a function then run it
            # return __class_obj ()
            return self.execute_command( __class_obj )
            
        if type(__class_obj) == type :                          # if the object definition its a class the load it and call run() again.
            __obj = __class_obj (neo_session = self.neo_session,                          # Neo4J session 
                                event = self.event,                     # Event Payload
                                event_bus = self.event_bus,             # event_bus config
                                image_processor = self.image_processor,
                                system_objects = self.system_objects ) # System objects bundle
            return __obj.run()
            
    # command not found error
    def __not_found(self, obj):

        self.logger.critical("Class or Method not found: %s", obj)
        
        self.response['status']['errorType'] = "Manifest:400"
        self.response['status']['errorInfo'] = __name__ #self.event['field']
        self.response['status']['message'] = "Manifest:Unexpected object or method"
        
        return self.back()
        
    # Standard results output used by all child functions
    def back(self, resp:dict = None):
        if resp == None: resp = self.response
        
        # Command its included in the response to enable nested field's source calls
        self.response['command'] = self.event['arguments'].get('command', '')
        
        return self.response

    # Child class function runner (usually referenced by the last command member)
    def execute_command(self, __obj):
        # Perform client credentials verifications required by the function 
        # and do function required paramerters validation as well
        __command_requirements = self.config.get(__obj.__name__, {})
        if __command_requirements == {}: return __obj ()

        # If required, the function must match the parent GraphQL type
        if not __command_requirements.get("required_function_type", None) in ['', None, self.event['info'].get('parentTypeName', 'Unknown') ]: 
            return self.__not_found( __obj )
        self.logger.debug("Runner: Validating command requirements...")
        
        '''
        if __command_requirements.get("required_valid_sid", True): 
            if not self.session.valid_sid(): return self.error( "invalidSession")
        if __command_requirements.get("required_valid_auth", True): 
            if not self.session.valid_auth() : return self.error( "invalidAuthorization")
        '''
        
        if __command_requirements.get("required_valid_auth", True): 
            if not self.authorized() : return self.error( "invalidAuthorization")


        return self.__execute_with_events(__obj, __command_requirements )

    # Child class function runner considering API invokation events
    def __execute_with_events(self, __obj, __command_requirements):
        __api_output = {}
        # Verify the before_api flag to invoke event script
        if __command_requirements.get("before_api_event", False): 
            self.event = self.api_events.invoke_event( object = self.event["arguments"]["command"], event = "before_api", payload = self.event)

        if "__result" in self.event: return self.event['__result'] # API result override directive, skip api funcion call and return.
        if "__error" in self.event: return self.event['__error']  # API result with error override directive, skip api funcion call and return.
        
        __api_output =  __obj ()

        # Verify the after_api flag to invoke event script
        if __command_requirements.get("after_api_event", False): 
            __api_output = self.api_events.invoke_event( object = self.event["arguments"]["command"], event = "after_api", payload = __api_output)

        return __api_output
    
    # Invoke a class that conains a field resolver referenced in the self.field_class dictionary
    def resolve(self):
        __field_obj = self.field_class[ self.event['info']['fieldName'] ] (neo_session = self.neo_session, event = self.event )
        return __field_obj.run()
        
    # Detect empty parameters
    def validate_parameters(self,*dictargs, **kwargs) -> bool:
        for dictionary in dictargs:
           for key in dictionary:
              if not isinstance(dictionary[key], str) or not bool(dictionary[key].strip()):
                return False
                
        for key in kwargs:
          if not isinstance(kwargs[key], str) or not bool(kwargs[key].strip()):
            return False
    
        return True
        
    # Standard error response that uses errors defined in the child json file
    def error(self, errorNumber, file= None, section = "general"):
        
        __error_data =  self.config.get('errors', {}).get(section, {}).get(errorNumber, None)
        
        if __error_data  == None:
            self.response.update( { 'message' : 'Unknown error' } )
            self.response['status'].update({'errorType': 'Manifest', 'errorInfo': self.__class__.__name__, 'message': 'Manifest:Unknown error', "statusCode": 400 })
            return self.back()        
        
        self.response.update( {'message' : __error_data.get('message', 'Unknown error') } )
        self.response['status'] = __error_data
        
        return self.back()
        
    # dictionary and variable referenced parameters processor 
    def load_parameters(self, __object, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary: setattr(__object, key, dictionary[key])
        for key in kwargs: setattr(__object, key, kwargs[key])
        return        
    

    def authorized(self):

        __resolverContext = self.event['identity'].get('resolverContext', {}) or {}
        
        if type(__resolverContext) is not dict: return False
        
        if self.event['identity'].get('resolverContext', {}).keys() >= {'email', 'sid', 'appid'}: 
            return True
        
        return False
        

    # event payload validation
    def event_payload_validation(self, event:dict):
        # events parameter verification
        self.logger.info(event)
        if not event.keys() >= {"request", "arguments", "identity", "source", "prev", "info", "stash" }:
            return False
    
        if "headers" not in event['request']: False
        event['headers'] = event['request']['headers']
    
        return True

    def context(self):
        return '{0}/{1}'.format( self.__class__.__name__, inspect.currentframe().f_back.f_code.co_name)