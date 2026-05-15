import re

# prompt injection detection

def detect_prompt_injection(user_query):

    injection_patterns = [

        "ignore previous instructions",
        "reveal system prompt",
        "bypass security",
        "jailbreak",
        "forget previous instructions",
        "pretend you are",
        "act as",
        "disable safety",
        "developer mode",
        "system prompt"
    ]

    query_lower = user_query.lower()

    for pattern in injection_patterns:

        if pattern in query_lower:
            return True

    return False

# pii masking

def mask_pii(user_query):

    # email masking

    user_query = re.sub(
        r'[\w\.-]+@[\w\.-]+',
        '[EMAIL_MASKED]',
        user_query
    )

    # phone masking

    user_query = re.sub(
        r'\b\d{10}\b',
        '[PHONE_MASKED]',
        user_query
    )

    return user_query

# toxicity detection

def detect_toxicity(user_query):

    toxic_words = [

        "idiot",
        "stupid",
        "hate",
        "kill",
        "abuse",
        "dumb",
        "shut up"
    ]

    query_lower = user_query.lower()

    for word in toxic_words:

        if word in query_lower:
            return True

    return False

# guardrails

def check_guardrails(user_query):

    allowed_topics = [

        "apple",
        "supply chain",
        "supplier",
        "daisy",
        "sustainability",
        "program",
        "technology",
        "worker",
        "education",
        "logistics",
        "factory",
        "manufacturing",
        "operations",
        "sedf"
    ]

    query_lower = user_query.lower()

    for topic in allowed_topics:

        if topic in query_lower:
            return True

    return False