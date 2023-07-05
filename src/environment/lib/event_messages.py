"""
Boto3 libraries adapted to the software requirements.
"""
import json, logging
from typing import Literal
from os import environ as env

import boto3


class EventMessages:
    """
    _General class to invoke the Mvnifest event bus._
    """
    def __init__(self, *initial_data, **kwargs):
        self.bus_arn = env.get('GLOBAL_BUS')
        self.logger = logging.getLogger(__name__)
        for key, value in kwargs.items():
            setattr(self, key, value)
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        # Get the service client
        self.event_bus = boto3.client("events")
        
    def send(self, message_body:dict, detail_type:str="Notifications",
                source:str="core", resources:str=None):
        """_Sends the event message to the bus according to the rule._

        Args:
            message_body (dict): _Payload to transmit to the bus._
            detail_type (str, optional): _Must match with the event pattern._. Defaults to "Notifications".
            source (str, optional): _Must match with the event pattern_. Defaults to "mvnifest.notifications".
            resources (str, optional): _If there exists any AWS resource._. Defaults to None.

        Returns:
            PutEventsResponseTypeDef
        """
        response = self.event_bus.put_events(
            Entries=[
                {
                    "Source" : source,
                    "Resources" : [] if resources is None else resources ,
                    "DetailType" : detail_type,
                    "Detail": json.dumps(message_body),
                    "EventBusName": self.bus_arn,
                }
            ]
        )
        return response

    def send_bulk(self, eventbridge_events:'list[dict]'):
        """_Sends the event message to the bus according to the rule._

        Args:
            message_body (dict): _Payload to transmit to the bus._
            detail_type (str, optional): _Must match with the event pattern._. Defaults to "Notifications".
            source (str, optional): _Must match with the event pattern_. Defaults to "mvnifest.notifications".
            resources (str, optional): _If there exists any AWS resource._. Defaults to None.

        Returns:
            True
        """
        EVENTBRIDGE_MAX_ITEMS = 10

        for i in range(0, len(eventbridge_events), EVENTBRIDGE_MAX_ITEMS):
            event_group = eventbridge_events[i : i + EVENTBRIDGE_MAX_ITEMS]
            entries=[{
                    "Source" : event.get("source", "core"),
                    "Resources" : [] if event.get("resources") is None else event.get("resources") ,
                    "DetailType" : event.get("detail_type", "Notifications"),
                    "Detail": json.dumps(event.get("message_body")),
                    "EventBusName": self.bus_arn,
                } for event in event_group]
            response = self.event_bus.put_events(Entries=entries)
            if response["FailedEntryCount"] != 0:
                self.logger.warning("PUT EVENTS FAILED:\n%s",json.dumps([entry for entry in response["Entries"] if entry.get("ErrorMessage") is not None],indent=4))

        
        return True
        

class EventMessagesV2:
    """
    _General class to invoke events thru the EventBridge bus
    """
    def __init__(self, EventBusName:str, EventBusSource:str, EventDetailType:str, EventBusResources:'list[str]' = None ):
        if EventBusResources is None:
            EventBusResources = []
        self.logger = logging.getLogger(__name__)
        self.EventBusName = EventBusName
        self.EventBusSource = EventBusSource
        self.EventBusResources = EventBusResources
        self.EventDetailType = EventDetailType

        # Get the service client
        self.event_bus = boto3.client("events")
        self.logger.info("Bus ARN: %s" % self.EventBusName )
        
    def send( self, message_body:dict ):
                          
        """_Sends the event message to the bus according to the rule._

        Args:
            message_body (dict): _Payload to transmit to the bus._

        Returns:
            PutEventsResponseTypeDef
        """
        
        if None in [message_body, self.EventDetailType, self.EventBusName, self.EventBusSource, self.EventBusResources]: return None
        
        response = self.event_bus.put_events(
            Entries=[
                {
                    "DetailType" : self.EventDetailType,
                    "Detail": json.dumps(message_body),
                    
                    "EventBusName": self.EventBusName,
                    "Source" : self.EventBusSource,
                    "Resources" : self.EventBusResources
                }
            ]
        )
        return response

    def send_bulk(self, eventbridge_events:'list[dict]'):
        """_Sends the event message to the bus according to the rule._

        Args:
            eventbridge_events list[dict]: _Payload to transmit to the bus._

        Returns:
            True
        """
        if None in [self.EventDetailType, self.EventBusName, self.EventBusSource, self.EventBusResources]: return None
        if any((True for e in eventbridge_events if e.get("message_body") is None)): return None
        EVENTBRIDGE_MAX_ITEMS = 10

        for i in range(0, len(eventbridge_events), EVENTBRIDGE_MAX_ITEMS):
            event_group = eventbridge_events[i : i + EVENTBRIDGE_MAX_ITEMS]
            entries=[{
                    "Source" : self.EventBusSource,
                    "Resources" : self.EventBusResources,
                    "DetailType" : self.EventDetailType,
                    "Detail": json.dumps(event.get("message_body")),
                    "EventBusName": self.EventBusName,
                } for event in event_group]
            response = self.event_bus.put_events(Entries=entries)
            if response["FailedEntryCount"] != 0:
                self.logger.warning("PUT EVENTS FAILED:\n%s",json.dumps([entry for entry in response["Entries"] if entry.get("ErrorMessage") is not None],indent=4))

        
        return True
    

class DirectLambdaInvoke:
    """
    _General class for direct lambda function invoke
    """
    def __init__(self, EventBusName:str, InvocationType:'Literal["DryRun", "Event", "RequestResponse"]' ):
        self.logger = logging.getLogger(__name__)
        self.EventBusName = EventBusName
        self.InvocationType:'Literal["DryRun", "Event", "RequestResponse"]' = InvocationType

        # Get the service client
        self.event_bus = boto3.client("events")
        self.logger.info("Bus ARN: %s" % self.EventBusName )
        
        self.response_types = {
            "RequestResponse" : self.__request_response,
                      "Event" : self.__event_response,
                     "DryRun" : self.__dryrun_response
        }
        
    def invoke(self, __payload:dict) -> dict:

        if None in [ __payload, self.EventBusName, self.InvocationType ]: return None

        __lambda_client = boto3.client('lambda')

        __payload_str = json.dumps(__payload)
        
        __api_response = __lambda_client.invoke(
              FunctionName = self.EventBusName,
            InvocationType = self.InvocationType,   # 'Event'|'RequestResponse'|'DryRun'
                   Payload = bytes(__payload_str, encoding='utf8')
        )
        
        return self.response_types.get(self.InvocationType, self.__event_response ) ( __api_response ) 
    
    def __request_response(self, __payload):
        
        if __payload.get('StatusCode', 0) != 200: return None
        
        return __payload['Payload'].read().decode()
        
    def __event_response(self, __payload):
        
        return __payload

    def __dryrun_response(self, __payload):
        
        if __payload.get('StatusCode', 0) != 204: return None
        
        return __payload['Payload'].read().decode()
