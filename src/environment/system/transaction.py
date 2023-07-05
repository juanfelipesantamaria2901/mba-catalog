"""
Your module description
"""
import json, time, uuid,logging

class Transaction:
    def __init__(self, *initial_data, **kwargs):
        self.neo_session = None
        self.logger=logging.getLogger(__name__)
        self.event = {}
        for dictionary in initial_data:
            for key in dictionary: setattr(self, key, dictionary[key])
        for key in kwargs: setattr(self, key, kwargs[key])

        self.__transaction = {
            "identifier": str( uuid.uuid4() ),
            "startdatetime": int(time.time() * 1000),
            "user_identifier": self.event.get('identity', {}).get('resolverContext', {}).get('user_identifier', None),
            "sid": self.event.get('identity', {}).get('resolverContext', {}).get('sid', None),
            "context" : "self",
            "event": "Generic transaction",
            "arguments": "",
            "event_log": [],
            "related_transactions": [],
            "enddatetime": 0,
            "result": "",
            "status": "__COMPLETE__"
        }
    
    def to_dict(self):
        return self.__transaction
        
    def __setitem__(self, key, value):
        self.__transaction[key] = value
            
    def __getitem__(self, key):
        return self.__transaction.get(key, None)

    def add_event(self, __transaction_event:str):
        self.__transaction['event_log'].append(__transaction_event)
        self.logger.info(__transaction_event)
        return

    def add_related_transaction(self, __transaction:str):
        self.__transaction['related_transactions'].append(__transaction)
        return

    def update(self, **kwargs):
        for key in kwargs: self.__transaction[key]= kwargs[key]
        return 
    
    def end_transaction(self):
        self.__transaction['enddatetime'] = int(time.time() * 1000)

        __cypher = '''
                match (:System)-[:transactions]->(transactions:Transactions)
                call apoc.lock.nodes([transactions])
                optional match (transactions)-[rel:transaction]->(last_transaction:Transaction)

                create (transactions)-[:transaction]->(new_transaction:Transaction)
                    set new_transaction.created = timestamp(), 
                    new_transaction.disabled_date =0, new_transaction.updated=0, 
                    new_transaction.name='Transaction', new_transaction.identifier = randomUUID(),
                    new_transaction += $props
                    
                with new_transaction, last_transaction, rel
                
                FOREACH (ignoreMe in CASE WHEN last_transaction is not null THEN [1] ELSE [] END |
                    delete rel
                    merge (new_transaction)-[:prev]->(last_transaction)
                )
                with new_transaction
                return new_transaction
                '''
                
        __result = self.neo_session.run( __cypher, props = self.__transaction ).data()  
        
        if len(__result) == 0: return None

        return dict( __result[0]['new_transaction'] ) 
        
