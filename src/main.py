import json, signal, sys
from init import runapp, neo4j_driver, logger,neo4j_table_name


def exit_gracefully(signum, frame): 
    logger.info("[runtime] SIGTERM received")

    # perform actual clean up work here. 
    neo4j_driver.close()

    logger.info("[runtime] exiting")
    sys.exit(0)

signal.signal(signal.SIGTERM, exit_gracefully)

def main_fun(event, context):

    logger.info("Event:\n%s", json.dumps(event, indent=4, sort_keys=True) )
    # Include the lambda context in the invoke event payload
    event['lambda_context'] = {
        "function_name": context.function_name,
        "function_version": context.function_version,
        "invoked_function_arn": context.invoked_function_arn,
        "aws_request_id": context.aws_request_id
    }
    logger.info("Invoke context:\n%s", json.dumps(event['lambda_context'], indent=4, sort_keys=True) )
    
    __result = {}
    # AWS AppSync events
    if event.keys() >= {"request", "arguments", "identity", "source", "prev", "info", "stash"}:
        with neo4j_driver.session(database=neo4j_table_name) as session:
            __result = runapp.run( event=event, neo_session=session )
            session.close()
    #logger.info( json.dumps(__result, indent=4, sort_keys=True) )

    if __result is not None and "root_result" in __result:
        return __result["root_result"]
    
    return __result
