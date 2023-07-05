"""
_To invoke the image_processor API_
"""
from os import environ as env
import json
import boto3

class ImageProcessorAPI:
    """
    General class to make a call to the Image Processor API
    """
    def __init__(self, **kwargs):
        """
        Initialization class
        """
        self.event = {}
        self.lambda_client = boto3.client('lambda')
        self.lambda_function = env.get('IMAGEPROCESSOR_ARN',
                "arn:aws:lambda:us-west-2:553506260656:function:Manifest_develop_ImageProcessor")

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.image_api_payload = {
            "service": "",
            "input" : ""
        }

    def __api_call(self, __payload:dict):
        """
        This function is responsible of doing the lambda invocation.

        Args:
            __payload (dict): The payload through the other lambda

        Returns:
            Dict : Response from the lambda call.
        """
        __payload_str = json.dumps(__payload)
        __api_response = self.lambda_client.invoke(
              FunctionName = self.lambda_function,
            InvocationType = "RequestResponse",
                   Payload = bytes(__payload_str, encoding='utf8')
        )
        return json.loads(__api_response['Payload'].read())

    def request(self, __service, __input) -> dict:
        """

        Args:
            __service (_type_): _Service call_
            __input (_type_): _The context of the service_

        Returns:
            _dict_: _Response of the API call_
        """

        __api_payload = self.image_api_payload
        __api_payload['service'] = __service
        __api_payload['input'] = __input
        return self.__api_call( __api_payload )
