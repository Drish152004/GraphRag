import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# -----------------------------------
# LOAD ENV
# -----------------------------------

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# -----------------------------------
# CONNECT TO NEO4J
# -----------------------------------

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

# -----------------------------------
# LOAD EMBEDDING MODEL
# -----------------------------------

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# -----------------------------------
# LOAD CLEANED TEXT
# -----------------------------------

TEXT_PATH = "../raw/cleaned_apple_supply_chain.txt"

with open(TEXT_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------
# SIMPLE CHUNKING
# -----------------------------------

chunk_size = 500

chunks = []

for i in range(0, len(text), chunk_size):

    chunk = text[i:i + chunk_size]

    if len(chunk.strip()) > 50:
        chunks.append(chunk)

print(f"\nCreated {len(chunks)} chunks.")

# -----------------------------------
# FETCH GRAPH ENTITIES
# -----------------------------------

def fetch_entities():

    entities = []

    query = """
    MATCH (n)
    RETURN DISTINCT n.label AS label
    """

    with driver.session() as session:

        results = session.run(query)

        for record in results:
            entities.append(record["label"])

    return entities

graph_entities = fetch_entities()

print(f"Loaded {len(graph_entities)} graph entities.")

# -----------------------------------
# CREATE VECTOR INDEX
# -----------------------------------

def create_vector_index(tx):

    query = """
    CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
    FOR (c:Chunk)
    ON c.embedding
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """

    tx.run(query)

# -----------------------------------
# CREATE CHUNK NODE
# -----------------------------------

def create_chunk(tx, chunk_id, chunk_text, embedding):

    query = """
    MERGE (c:Chunk {id: $id})

    SET c.text = $text,
        c.embedding = $embedding
    """

    tx.run(
        query,
        id=chunk_id,
        text=chunk_text,
        embedding=embedding
    )

# -----------------------------------
# CREATE ENTITY-CHUNK RELATIONS
# -----------------------------------

def connect_entities_to_chunk(tx, chunk_id, chunk_text):

    for entity in graph_entities:

        if entity.lower() in chunk_text.lower():

            query = """
            MATCH (e)
            WHERE e.label = $entity

            MATCH (c:Chunk {id: $chunk_id})

            MERGE (e)-[:MENTIONED_IN]->(c)
            """

            tx.run(
                query,
                entity=entity,
                chunk_id=chunk_id
            )

# -----------------------------------
# STORE CHUNKS
# -----------------------------------

with driver.session() as session:

    print("\nCreating vector index...\n")

    session.execute_write(create_vector_index)

    print("\nEmbedding and storing chunks...\n")

    for idx, chunk in enumerate(chunks):

        chunk_id = f"chunk_{idx}"

        embedding = model.encode(chunk).tolist()

        # Create chunk node
        session.execute_write(
            create_chunk,
            chunk_id,
            chunk,
            embedding
        )

        # Connect entities
        session.execute_write(
            connect_entities_to_chunk,
            chunk_id,
            chunk
        )

        print(f"Stored {chunk_id}")

# -----------------------------------
# CLOSE DRIVER
# -----------------------------------

driver.close()

print("\nHybrid GraphRAG chunk embedding completed.")