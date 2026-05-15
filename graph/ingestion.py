import json
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# LOAD ENV VARIABLES
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# CONNECT TO NEO4J
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# LOAD REFINED GRAPH
GRAPH_PATH = "../raw/graphify-out/refined_graph.json"

with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    graph_data = json.load(f)

nodes = graph_data["nodes"]
links = graph_data["links"]

# CREATE NODES
def create_node(tx, node):

    entity_type = node.get("entity_type", "Entity")

    # Prevent invalid Neo4j labels
    entity_type = entity_type.replace(" ", "_")

    query = f"""
    MERGE (n:{entity_type} {{id: $id}})
    
    SET n.label = $label,
        n.norm_label = $norm_label,
        n.file_type = $file_type,
        n.community = $community,
        n.source_file = $source_file,
        n.source_chunk = $source_chunk,
        n.author = $author,
        n.contributor = $contributor,
        n.captured_at = $captured_at,
        n.entity_type = $entity_type
    """

    tx.run(
        query,

        id=node.get("id"),
        label=node.get("label"),
        norm_label=node.get("norm_label"),

        file_type=node.get("file_type"),
        community=node.get("community"),

        source_file=node.get("source_file"),
        source_chunk=node.get("source_chunk"),

        author=node.get("author"),
        contributor=node.get("contributor"),
        captured_at=node.get("captured_at"),

        entity_type=entity_type
    )

# CREATE RELATIONSHIPS
def create_relationship(tx, rel):

    relation_type = rel.get("relation", "RELATED_TO")

    # Neo4j-safe relationship type
    relation_type = relation_type.upper().replace(" ", "_")

    query = f"""
    MATCH (a {{id: $source}})
    MATCH (b {{id: $target}})

    MERGE (a)-[r:{relation_type}]->(b)

    SET r.confidence = $confidence,
        r.confidence_score = $confidence_score,
        r.weight = $weight,
        r.source_file = $source_file,
        r.source_chunk = $source_chunk
    """

    tx.run(
        query,

        source=rel.get("source"),
        target=rel.get("target"),

        confidence=rel.get("confidence"),
        confidence_score=rel.get("confidence_score"),
        weight=rel.get("weight"),

        source_file=rel.get("source_file"),
        source_chunk=rel.get("source_chunk")
    )

# OPTIONAL INDEXES
def create_indexes(tx):

    queries = [

        "CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:Company) ON (n.id)",

        "CREATE INDEX entity_label_index IF NOT EXISTS FOR (n:Company) ON (n.label)"
    ]

    for q in queries:
        tx.run(q)

# INGEST GRAPH
with driver.session() as session:

    print("\nCreating indexes...\n")
    session.execute_write(create_indexes)

    print("\nCreating nodes...\n")

    for node in nodes:
        session.execute_write(create_node, node)

    print(f"Inserted {len(nodes)} nodes.")

    print("\nCreating relationships...\n")

    for rel in links:
        session.execute_write(create_relationship, rel)

    print(f"Inserted {len(links)} relationships.")

# CLOSE CONNECTION
driver.close()

print("\nGraph ingestion completed successfully.")