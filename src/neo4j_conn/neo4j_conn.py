"""
Your module description
"""

from os import environ as env
import logging
from neo4j import GraphDatabase
from neo4j import Driver

class Neo:
    def __init__(self, *initial_data, **kwargs):
        self.__driver:Driver = None
        self.logger = logging.getLogger(__name__)
        
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def connect(self, neo4j_database:dict) -> bool:
        try:
            self.__driver = GraphDatabase.driver(
                    neo4j_database['neo4j_server'], 
                    auth=( neo4j_database['neo4j_credentials']['login'], neo4j_database['neo4j_credentials']['password'] ),
                    encrypted= False
                    )
            self.logger.info("Neo4j: %s Table: %s", neo4j_database['neo4j_server'],neo4j_database['neo4j_credentials']['table'])
            return True
        except:
            raise
        
        return False
        
    def driver(self) -> Driver:
        return self.__driver
