from neo4j import GraphDatabase
import uuid
import time


primary_uri = "bolt://localhost:7617"
replica_uri = "bolt://localhost:7627"
user = "neo4j"
password = "secret123"


def generate_unique_label():
    unique = str(uuid.uuid4()).replace("-", "")
    return unique


class Neo4jConnector:
    def __init__(self, uri, user, password, dbname=None):
        self.uri = uri
        self.user = user
        self.password = password
        self.dbname = dbname
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)

    def close(self):
        self.driver.close()

    def run(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return result.single()


# Function to create a node
def create_node(connector, node_label):
    query = """
        CREATE (p:Person) 
        SET p.name = $node_label, p.createdAt = timestamp(), p.testAttribute = 'InitialValue' 
        RETURN p
    """
    result = connector.run(query, {"node_label": node_label})
    query = "MATCH (p:Person {name: $node_label}) RETURN count(p)"
    result = connector.run(query, {"node_label": node_label})
    count = result[0]
    if count == 1:
        print(f"Person {node_label} Created")
        return True
    else:
        print(f"Person {node_label}  Not Created")
        assert False


# Function to check for the node's existence on replicas
def check_node_on_replicas(connector, node_label):
    query = "MATCH (p:Person {name: $node_label}) RETURN count(p)"
    result = connector.run(query, {"node_label": node_label})
    count = result[0]
    if count == 1:
        print(f"Person {node_label} found on replica secondary. Consistency verified.")
        return True
    else:
        print(f"Person {node_label} not found on replica secondary. Consistency not verified.")
        # assert False, "Node not found on replicas. Consistency test failed."


def test_consistency_read(node_label):
    primary_connector = Neo4jConnector(primary_uri, user, password)
    try:
        create_node(primary_connector, node_label)
    finally:
        primary_connector.close()
    print("sleep seconds")
    time.sleep(4)  # Allow time for synchronization
    # Connect to a replica node and check for consistency
    replica_connector = Neo4jConnector(replica_uri, user, password)
    try:
        check_node_on_replicas(replica_connector, node_label)
    finally:
        replica_connector.close()




if __name__ == "__main__":

    # Node details
    node_label = generate_unique_label()
    test_consistency_read(node_label=node_label)
