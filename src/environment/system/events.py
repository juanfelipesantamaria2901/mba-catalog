"""
Your module description
"""
import json, boto3, logging
from os import environ as env

class Events:
    def __init__(self, **kwargs):
        self.logger=logging.getLogger(__name__)
        self.event = {}
        self.lambda_client = boto3.client('lambda')
        
        self.lambda_function = env.get('GLOBAL_BUS')
        self.manifest_api_payload = { 
            "mvnifest" : { "object" : "", "event": "" },  
            "arguments": { "sync": True }
        }
        for key in kwargs: setattr(self, key, kwargs[key])

    def __api_call(self, __payload:dict):
        
        __payload_str = json.dumps(__payload)
        
        __api_response = self.lambda_client.invoke(
              FunctionName = self.lambda_function,
            InvocationType = "RequestResponse",
                   Payload = bytes(__payload_str, encoding='utf8')
        )
        
        return json.loads(__api_response['Payload'].read())
        

    def invoke_event(self, **__event):
        self.logger.debug("--Manifest Event Invoked: {object}->{event}".format(**__event) )
        #self.logger.info(__payload)

        __event_payload = self.manifest_api_payload
        __event_payload["mvnifest"] = {"object" : __event["object"], "event": __event["event"]}
        __event_payload['arguments'] = __event["payload"]
        
        return self.__api_call( __event_payload )
