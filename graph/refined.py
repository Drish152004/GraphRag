import json
import re

# LOAD GRAPH
with open("../raw/graphify-out/graph.json", "r", encoding="utf-8") as f:
    graph = json.load(f)

nodes = graph["nodes"]
links = graph["links"]


# ENTITY TYPE CLASSIFICATION
def classify_entity(label):

    label_lower = label.lower()

    if "apple" in label_lower:
        return "Company"

    elif "university" in label_lower:
        return "University"

    elif (
        "organization" in label_lower
        or "ilo" in label_lower
        or "iom" in label_lower
    ):
        return "NGO"

    elif (
        "fund" in label_lower
        or "program" in label_lower
        or "hub" in label_lower
    ):
        return "Program"

    elif (
        "code of conduct" in label_lower
        or "policy" in label_lower
    ):
        return "Policy"

    elif "lab" in label_lower:
        return "Facility"

    elif "robot" in label_lower:
        return "Technology"

    elif "khan" in label_lower:
        return "Person"

    else:
        return "Entity"


# NOISE FILTERING
filtered_nodes = []

for node in nodes:

    label = node.get("label", "").strip()

    # Remove empty labels
    if not label:
        continue

    # Remove very short labels
    if len(label) < 3:
        continue

    # Remove labels with excessive symbols
    if re.match(r"^[^a-zA-Z0-9]+$", label):
        continue

    # Add entity type
    node["entity_type"] = classify_entity(label)

    # Add provenance
    node["source_chunk"] = node.get("source_file", "unknown")

    filtered_nodes.append(node)

nodes = filtered_nodes

# VALID NODE IDS
valid_node_ids = set(node["id"] for node in nodes)


# RELATIONSHIP NORMALIZATION
RELATION_MAPPING = {
    "references": "RELATED_TO",
    "calls": "USES",
    "implements": "IMPLEMENTS"
}

filtered_links = []

for link in links:

    # Skip broken relationships
    if (
        link["source"] not in valid_node_ids
        or link["target"] not in valid_node_ids
    ):
        continue

    original_relation = link["relation"].lower()

    normalized_relation = RELATION_MAPPING.get(
        original_relation,
        original_relation.upper()
    )

    link["relation"] = normalized_relation

    # Add provenance
    link["source_chunk"] = link.get(
        "source_file",
        "unknown"
    )

    filtered_links.append(link)

links = filtered_links

# FINAL GRAPH
refined_graph = {
    "nodes": nodes,
    "links": links
}

# SAVE OUTPUT
with open(
    "../raw/graphify-out/refined_graph.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(refined_graph, f, indent=2)

print("\nGraph refinement completed successfully.")
print("Saved as refined_graph.json")
print(f"Nodes: {len(nodes)}")
print(f"Relationships: {len(links)}")