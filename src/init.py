"""
Lambda Initalizer (init phase)
"""
print("*** BEGIN INITIALIZATION STATEMENTS ***")
import json, boto3, logging
from os import environ as env
from neo4j_conn.neo4j_conn import Neo
from importlib.metadata import metadata
from environment.lib.event_messages import EventMessages, EventMessagesV2, DirectLambdaInvoke
from environment.lib.system_objects_bundle import ObjectsBundle
from runapp import RunApp

# Configuring logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if not logging.getLogger().hasHandlers():
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - \033[33m\u001b[7m%(levelname)s\033[0m - \033[32m%(message)s\033[0m')
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False

logger.info("INIT CODE STARTS HERE!")

if env.get('SYSTEM_VERBOSE', "False").lower() not in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup']:
    logging.disable(logging.DEBUG)


def load_module_configurations():
        secretsmanager_client = boto3.client('secretsmanager')
        ssm_client = boto3.client("ssm")
        
        __result = {}        
        
        
        # Neo4j server parameters
        neo4j_credentials_key  = env.get('NEO4J_CREDENTIALS')
        neo4j_private_ip_key   = env.get('NEO4J_PRIVATE_IP')
        neo4j_private_port_key = env.get('NEO4J_PRIVATE_PORT')

        output_ssm = ssm_client.get_parameters( Names=[neo4j_credentials_key,neo4j_private_port_key,neo4j_private_ip_key])

        transformed_dict = dict((item['Name'], item) for item in output_ssm['Parameters'])

        neo4j_credentials = secretsmanager_client.get_secret_value(SecretId=transformed_dict.get(neo4j_credentials_key, {}).get('Value', ''))

        __result['neo4j'] = {
                "neo4j_credentials" : json.loads(neo4j_credentials['SecretString']),
                "neo4j_server" : "bolt://%s:%s" % ( transformed_dict.get(neo4j_private_ip_key, {}).get('Value', ''), transformed_dict.get(neo4j_private_port_key, {}).get('Value', ''))
        }

        # Eventbridge Global Bus ARN
        __global_bus_arn  = env.get('GLOBAL_BUS')
        __result['global_bus'] = {
                "arn" : __global_bus_arn
        }

        # Scripts Dispatcher ARN for Direct lambda invoke
        __scripts_dispatcher_arn  = env.get('SCRIPT_DISPATCHER_ARN')
        __result['scripts_dispatcher'] = {
                "arn" : __scripts_dispatcher_arn
        }
        
        return __result

logger.info("Connecting to Neo4j...")
logger.info("Using: %(summary)s, version: %(version)s" % metadata('neo4j') )

## NEO
__module_configurations = load_module_configurations()

__neo4j_connection = Neo()
__neo4j_connection.connect( __module_configurations['neo4j'] )
neo4j_driver = __neo4j_connection.driver()
neo4j_table_name = __module_configurations['neo4j']['neo4j_credentials']['table']

logger.info("Creating events bus object...")
__event_bus_obj = EventMessages(EventBusName = __module_configurations['global_bus']['arn'])

logger.info("Creating events global bus object...")
__events_global_bus_obj = EventMessagesV2( EventBusName = __module_configurations['global_bus']['arn'], 
                                  EventBusSource = "Business.core", 
                                  EventDetailType = "Business.events",
                                EventBusResources = [] )
__scripts_dispatcher_obj = DirectLambdaInvoke( EventBusName = __module_configurations['scripts_dispatcher']['arn'], 
                                             InvocationType = "RequestResponse" )
# This is an objects bundle containing the references of all the system objects 
__system_objects = ObjectsBundle( event_bus = __event_bus_obj,
                        events_global_bus = __events_global_bus_obj)

logger.info("Creating RunApp object...")
runapp = RunApp(event_bus = __event_bus_obj, system_objects = __system_objects)
logger.info("INIT CODE ENDS HERE!")

# This is an objects bundle containing the references of all the system objects 
__system_obj = {
        'verbose' : env.get("SYSTEM_VERBOSE", False),
        # More objects to be added here
}

