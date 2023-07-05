"""
Your module description
"""
import importlib
import json, logging
import os.path
from collections import namedtuple
from os import path, environ as env
from typing import Any
from environment.system.config import Config
from environment.system.transaction import Transaction
from environment.lib.event_messages import EventMessages
from neo4j import Session as Neo4jSession
from environment.lib.system_objects_bundle import ObjectsBundle
from neo4j_conn.filters import Filters
import inspect

SubscriptionEvent=namedtuple("SubscriptionEvent",["channel","event","payload","context"])

class EnvRunner:
    def __init__(self, *initial_data, **kwargs):
        super().__init__()
        self.neo_session:Neo4jSession = None    # Neo4j session object
        self.event = {}                         # event payload dictionary
        self.config = {}                        # child class json dictionaly
        self.transaction:Transaction = None     # transaction object
        self.event_bus:EventMessages = None     # Event bus messages
        self.logger = logging.getLogger(__name__)
        self.image_processor = None
        self.system_objects:ObjectsBundle = None

        self.source = None

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.app_class = {}         # Initialize class references dictionary
        self.field_class = {}       # Initialize field resolvers references dictionary
        self.response = {}
        self.response:dict[str,Any] = {           # Default error response
            "status": {
                "code": 0, "description": "Superseded",
                "errorType": None, "errorInfo": self.__class__.__name__, "message": None, "debug_info": None}
        }

        # Create a filters class object
        self.filters_obj = Filters(neo_session=self.neo_session)

        # Define the child json file if any
        __class_module = importlib.import_module(self.__module__)
        __json_file = __class_module.__file__.replace(".py", ".json")

        # Output log the child class name/path
        self.logger.debug("Class: %s %s", self.__class__.__name__, __class_module.__file__)

        # Load the child json file if any
        if path.exists(__json_file):
            __config = Config( config_file=__json_file)
            self.config.update(__config.data())

        # Crate a new transaction object
        self.__create_transaction()

    def run(self):
        __field_class = self.field_class.get(
            self.event['info']['fieldName'], self.other)
        return __field_class()

    def other(self):
        return self.__not_found(self.event['info'])


    # Standard error response that uses errors defined in the class json file
    def error(self, errorNumber, file=None, section="general"):

        __error_data = self.config.get('errors', {}).get(
            section, {}).get(errorNumber, None)

        if __error_data == None:
            __error_data = {'errorType': 'Manifest',
                            'errorInfo': self.__class__.__name__, 'message': 'Manifest:UnknownError'}

        self.response['status'] = __error_data
        self.logger.info(__error_data)

        __command_requirements = self.config.get(
            inspect.currentframe().f_back.f_code.co_name, {})
        if __command_requirements.get("transaction_enabled", False):
            # If transaction enabled then include the regular result in the transaction
            # and submit it.
            self.transaction['status'] = "__ERROR__"
            self.transaction['result'] = self.response.get(
                "status", {}).get("message", "Unknown error")
            # self.transaction.end_transaction()

        return self.back()

    # command not found error
    def __not_found(self, __info):

        self.logger.warning("Class or Method not found: %s", __info.get('fieldName', None))

        self.response['status']['errorType'] = "Manifest:400"
        self.response['status']['errorInfo'] = "{0}:{1}:{2}".format(
            __name__, __info.get('parentTypeName', None), __info.get('fieldName', None))
        self.response['status']['message'] = "Manifest:Unexpected object or method"

        return self.back()

    # Standard results output used by all child functions (Deprecated)
    def __back(self, resp: dict = None):
        if resp == None:
            resp = self.response

        return self.response

    # Standard results output used by all child functions
    def back(self, resp: dict = None):
        if resp == None:
            resp = self.response

        # Do a double check on the command configuration because we have 2 current frame situations: self.error() and self.back()
        __command_requirements = self.config.get(
            inspect.currentframe().f_back.f_code.co_name, {})
        if __command_requirements == {}:
            __command_requirements = self.config.get(
                inspect.currentframe().f_back.f_back.f_code.co_name, {})

        if __command_requirements.get("transaction_enabled", False):
            # If transaction enabled then include the regular result in the transaction
            # and submit it.
            del self.response['status']
            if self.transaction['result'] == "":
                self.transaction['result'] = self.response.get(
                    "result", json.dumps(self.response))
            self.transaction.end_transaction()

        if __command_requirements.get("transaction_output_enabled", False):
            # Also, if transaction output is enabled then use the transaction object as output
            if self.transaction['result'] == "":
                self.transaction['result'] = self.response.get(
                    "result", json.dumps(self.response))
            return self.transaction.to_dict()

        # Command its included in the response to enable nested field's source calls
        self.response['command'] = self.event['arguments'].get('command', '')
        # self.response.update( self.no_error )
        
        return self.response

    def __create_transaction(self):
        self.transaction = Transaction(
            neo_session=self.neo_session, event=self.event)
        self.transaction['context'] = self.__class__.__name__
        self.transaction['event'] = self.event['arguments'].get(
            'command', 'Unknown')
        self.transaction['arguments'] = json.dumps(self.event['arguments'])

    def context(self):
        return '{0}/{1}'.format(self.__class__.__name__, inspect.currentframe().f_back.f_code.co_name)
        
        
    def invoke_subscription_event(self, __channel:str, __event:str, __payload:str, __context:str):
        # Send message to host using passwordless message subscription
        __response = self.event_bus.send(
            message_body= {
                "service": "Subscriptions",
                "context" : {
                  "type" : "message",
                  "channel" : __channel,
                  "event" : __event,
                  "payload" : __payload,
                  "context": __context
                }
              },
            source = "core",
            detail_type = "Notifications")

        return __response

    def invoke_subscription_event_bulk(self, events:'list[SubscriptionEvent]'):
        # Send message to host using passwordless message subscription
        eventbridge_events=[]
        for event in events:
            eventbridge_events.append({"message_body": {
                    "service": "Subscriptions",
                    "context" : {
                      "type" : "message",
                      "channel" : event.channel,
                      "event" : event.event,
                      "payload" : event.payload,
                      "context": event.context
                    }
                  },
                "source":"core",
                "detail_type":"Notifications"})
        __response = self.event_bus.send_bulk(eventbridge_events)

        return __response

    def invoke_mvnifest_event(self, __channel:str, __event:str, __payload:str, __context:str):
        __response = self.event_bus.send(
            message_body= {
                  "channel" : __channel,
                  "event" : __event,
                  "payload" : __payload,
                  "context": __context
                },
            source = "core",
            detail_type = "Business.events")

        return __response
        
