import json
from datetime import datetime

LOG_FILE = "logs.json"

def log_interaction(

    original_query,
    sanitized_query,
    retrieval_query,
    detected_entities,
    retrieval_mode,
    answer

):

    log_data = {

        "timestamp": str(datetime.now()),

        "original_query": original_query,

        "sanitized_query": sanitized_query,

        "retrieval_query": retrieval_query,

        "detected_entities": detected_entities,

        "retrieval_mode": retrieval_mode,

        "answer": answer
    }

    try:

        with open(LOG_FILE, "r", encoding="utf-8") as f:

            logs = json.load(f)

    except:

        logs = []

    logs.append(log_data)

    with open(LOG_FILE, "w", encoding="utf-8") as f:

        json.dump(
            logs,
            f,
            indent=4
        )