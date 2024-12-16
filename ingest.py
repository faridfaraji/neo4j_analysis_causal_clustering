import os
from tqdm import tqdm
from neo4j import GraphDatabase


# Neo4j connection details
USERNAME = "neo4j"
PASS = "secret123"  # Default password; replace if you’ve changed it
# graph = Graph("bolt://localhost:7687", auth=(USERNAME, PASS), database="neo4j")
local_path = "/Users/farid/neo4j/raw_data/csv/import"


class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False, database="neo4j")

    def close(self):
        self.driver.close()

    def run(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return result

    def list_databases(self):
        query = "SHOW DATABASES"
        with self.driver.session() as session:
            result = session.run(query)
            res = [record["name"] for record in result]
            print(res)
            return res


class Importer:

    def __init__(self):
        self.connector = Neo4jConnector("bolt://localhost:7617", USERNAME, PASS)

    def run(self):
        try:
            # Process initial steps (relations, persons, movies)

            # Create indices for person and movie IDs to improve query performance
            self.connector.run("CREATE INDEX person_id_index FOR (p:Person) ON (p.id)")
            self.connector.run("CREATE INDEX movie_id_index FOR (m:Movie) ON (m.id)")

            # Import persons to database
            i = 0
            with tqdm(desc="Person", unit="file") as pb:
                while True:
                    file_path = f'file:///myData{i}person.csv'
                    the_local_path = f"{local_path}/myData{i}person.csv"
                    if not os.path.exists(the_local_path):
                        print("file does not exist")
                        break

                    statement = (f"LOAD CSV WITH HEADERS FROM '{file_path}' AS row\n"
                                 "CREATE (e:Person {id: row.id, name: row.name, dateOfBirth: toInteger(row.dob), "
                                 "dateOfDeath: toInteger(row.dod), primaryProfession: split(row.pp, \";\"), "
                                 "knownForTitles: split(row.kft, \";\")})")
                    self.connector.run(statement)
                    pb.update(1)
                    i += 1

            # Import movies to database
            i = 0
            with tqdm(desc="Movies", unit="file") as pb:
                while True:
                    file_path = f'file:///myData{i}movie.csv'
                    the_local_path = f"{local_path}/myData{i}movie.csv"
                    if not os.path.exists(the_local_path):
                        print("file does not exist")
                        break

                    statement = (f"LOAD CSV WITH HEADERS FROM '{file_path}' AS row\n"
                                 "CREATE (e:Movie {id: row.id, originalTitle: row.name, primaryTitle: row.primTitle, "
                                 "type: row.type, isAdult: toBoolean(row.isAdult), startYear: toInteger(row.startYear), "
                                 "endYear: toInteger(row.endYear), runtimeMinutes: toInteger(row.runtimeMinutes), "
                                 "genres: split(row.genres, \";\")})")
                    self.connector.run(statement)
                    pb.update(1)
                    i += 1

            # Ensure the index is created by running a simple query
            self.connector.run("MATCH (m:Movie {id: 'tt0000721'}) RETURN m")

            # Import relations
            i = 3096
            with tqdm(desc="Relations", unit="file", initial=i) as pb:
                while True:
                    file_path = f'file:///myData{i}rel.csv'
                    the_local_path = f"{local_path}/myData{i}rel.csv"
                    if not os.path.exists(the_local_path):
                        print("file does not exist")
                        break
                    statement = (f"LOAD CSV WITH HEADERS FROM '{file_path}' AS row\n"
                                 "MATCH (m:Movie {id: row.titleid})\n"
                                 "MATCH (p:Person {id: row.personid})\n"
                                 "CREATE (p)-[r:part_of {category: row.category, job: row.job, "
                                 "characters: split(row.characters, ';')}]->(m);")
                    self.connector.run(statement)
                    pb.update(1)
                    i += 1

        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}")


# Example usage (assuming you have implemented the TSV2CSV class):
# tsv2csv = TSV2CSV("/path/to/neo4j")  # Replace with your actual TSV2CSV instance
importer = Importer()
importer.connector.list_databases()
importer.run()

