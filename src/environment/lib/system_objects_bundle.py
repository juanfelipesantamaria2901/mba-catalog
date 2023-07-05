"""
Your module description
"""
from dataclasses import field, asdict, dataclass
from event_messages import EventMessages, EventMessagesV2, DirectLambdaInvoke
from ImageProcessorApi import ImageProcessorAPI

@dataclass
class ObjectsBundle:
    """This is an objects bundle class. It contains the objects that 
    were created during the lambda init phase

    Attributes:
        event_bus (EventMessages): This is the old event_bus object (To be reomved soon...)
        image_processor (ImageProcessorAPI): This is the image processor inteface (To be removed soon...)
        events_global_bus (EventMessagesV2): This is the new eventbridge gobal bus object. It will replace event_bus
        scripts_dispatcher (DirectLambdaInvoke): This is a class to make direct invokations to the scripts dispatcher as a service (Synchronous)

    """

    event_bus: EventMessages = None

    image_processor:ImageProcessorAPI = None

    events_global_bus:EventMessagesV2 = None

    scripts_dispatcher:DirectLambdaInvoke = None
