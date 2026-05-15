import logging
import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase
from groq import Groq
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz

from graph.security import (
    detect_prompt_injection,
    mask_pii,
    detect_toxicity,
    check_guardrails,
)

from graph.logger import log_interaction

load_dotenv()

logger = logging.getLogger("graphrag.retrieval")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VECTOR_TOP_K = 8
VECTOR_MIN_SCORE = 0.32
GRAPH_LIMIT_PER_QUERY = 25
MAX_CHUNK_CHARS = 520
MAX_GRAPH_TRIPLES = 20
MAX_VECTOR_CHUNKS = 6
MAX_FUSED_CONTEXT_CHARS = 4500
FUZZY_GRAPH_THRESHOLD = 72

FILLER_PHRASES = [
    "my email is",
    "can you",
    "please",
    "tell me",
    "explain to me",
    "i want to know",
    "what is",
    "what are",
    "who is",
    "how does",
]

STOP_TOKENS = {
    "the", "and", "for", "with", "from", "that", "this", "what", "when",
    "where", "which", "about", "into", "your", "their", "apple", "does",
    "have", "been", "were", "will", "would", "could", "should", "also",
}

STOP_ACRONYMS = {
    "AI", "US", "UK", "EU", "CEO", "CFO", "CTO", "PDF", "HTML", "HTTP",
    "API", "LLM", "RAG", "IT", "HR", "QA", "ID", "OK", "VS",
}

GENERIC_GRAPH_WORDS = {
    "clean", "energy", "water", "supplier", "program", "fund", "hub",
    "apple", "chain", "global", "environmental", "social", "progress",
}

PROGRAM_SUFFIX_PATTERN = re.compile(
    r"\b(?:[A-Z][\w&'-]*\s+){0,6}"
    r"(?:Program|Initiative|Fund|Hub|Alliance|Partnership|Code of Conduct|"
    r"Standards|Framework|Platform|Network|Commitment|Goals|Strategy)\b",
    re.IGNORECASE,
)

TITLE_CASE_PHRASE = re.compile(
    r"\b(?:[A-Z][a-z]+(?:['-][A-Za-z]+)?)(?:\s+(?:[A-Z][a-z]+(?:['-][A-Za-z]+)?)){1,5}\b"
)

SINGLE_PROPER_NOUN = re.compile(r"\b[A-Z][a-z]{2,}(?:['-][A-Za-z]+)?\b")
ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,8}\b")
QUOTED_SPAN = re.compile(r'"([^"]{2,80})"|\'([^\']{2,80})\'')

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)

client = Groq(api_key=GROQ_API_KEY)

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def clean_retrieval_query(user_query: str) -> str:
    """Remove fillers and PII patterns; preserve casing for proper nouns."""
    query = re.sub(r"[\w\.-]+@[\w\.-]+", "", user_query)

    cleaned = query
    for phrase in FILLER_PHRASES:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else user_query.strip()


def fetch_graph_entities():
    entities = []
    query = """
    MATCH (n)
    WHERE n.label IS NOT NULL AND trim(n.label) <> ''
    RETURN DISTINCT n.label AS label
    """
    with driver.session() as session:
        for record in session.run(query):
            label = (record.get("label") or "").strip()
            if label:
                entities.append(label)
    return entities


graph_entities = fetch_graph_entities()


def normalize_entity_span(span: str) -> str:
    return re.sub(r"\s+", " ", span.strip())


def _is_noise_span(span: str) -> bool:
    normalized = span.strip()
    if len(normalized) < 2:
        return True
    if normalized.lower() in STOP_TOKENS:
        return True
    if normalized.isupper() and normalized in STOP_ACRONYMS:
        return True
    if "?" in normalized or " relate " in normalized.lower():
        return True
    if len(normalized.split()) > 7:
        return True
    return False


def _is_high_confidence_heuristic(span: str) -> bool:
    """Allow ungrounded spans only when they look like real named entities."""
    if PROGRAM_SUFFIX_PATTERN.search(span):
        return True
    if ACRONYM_PATTERN.fullmatch(span.strip()):
        return span.strip() not in STOP_ACRONYMS
    words = span.split()
    if len(words) == 1 and SINGLE_PROPER_NOUN.fullmatch(span.strip()):
        return len(span.strip()) >= 3
    if len(words) >= 2 and TITLE_CASE_PHRASE.fullmatch(span.strip()):
        return True
    return False


def extract_heuristic_entities(user_query: str) -> list[str]:
    """Lightweight proper-noun / program / acronym extraction for graph grounding."""
    candidates = []

    for match in PROGRAM_SUFFIX_PATTERN.finditer(user_query):
        candidates.append(normalize_entity_span(match.group(0)))

    for match in TITLE_CASE_PHRASE.finditer(user_query):
        candidates.append(normalize_entity_span(match.group(0)))

    for match in SINGLE_PROPER_NOUN.finditer(user_query):
        candidates.append(normalize_entity_span(match.group(0)))

    for match in ACRONYM_PATTERN.finditer(user_query):
        token = match.group(0)
        if token not in STOP_ACRONYMS:
            candidates.append(token)

    for match in QUOTED_SPAN.finditer(user_query):
        span = match.group(1) or match.group(2)
        if span:
            candidates.append(normalize_entity_span(span))

    # Sustainability / technology phrasing (case-insensitive spans)
    tech_program_patterns = [
        r"\b(?:supplier\s+clean\s+water\s+program)\b",
        r"\b(?:clean\s+energy\s+program)\b",
        r"\b(?:supplier\s+employee\s+development\s+fund)\b",
        r"\b(?:environmental\s+progress\s+hub)\b",
        r"\b(?:daisy\s+robot(?:s)?)\b",
    ]
    lowered = user_query.lower()
    for pattern in tech_program_patterns:
        for match in re.finditer(pattern, lowered, re.IGNORECASE):
            candidates.append(normalize_entity_span(match.group(0).title()))

    deduped = []
    seen_lower = set()
    for cand in candidates:
        if _is_noise_span(cand):
            continue
        key = cand.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        deduped.append(cand)

    return deduped


def ground_to_graph_entity(span: str):
    """Map a span to the best canonical graph label, if confident."""
    if not span or not graph_entities:
        return None

    span_lower = span.lower()
    best_label = None
    best_score = 0

    for entity in graph_entities:
        entity_lower = entity.lower()

        if span_lower == entity_lower:
            return entity

        if span_lower in entity_lower or entity_lower in span_lower:
            score = 95
        else:
            score = max(
                fuzz.partial_ratio(span_lower, entity_lower),
                fuzz.token_sort_ratio(span_lower, entity_lower),
            )

        if score > best_score:
            best_score = score
            best_label = entity

    if best_score >= FUZZY_GRAPH_THRESHOLD:
        return best_label
    return None


def detect_entities(user_query: str) -> list[str]:
    """
    Entity detection for graph grounding only (not retrieval routing).
    Combines heuristics + fuzzy match against known graph labels.
    """
    detected = []
    seen_lower = set()

    def add_entity(label: str) -> None:
        if not label:
            return
        key = label.lower()
        if key in seen_lower:
            return
        seen_lower.add(key)
        detected.append(label)

    for span in extract_heuristic_entities(user_query):
        grounded = ground_to_graph_entity(span)
        if grounded:
            add_entity(grounded)
        elif _is_high_confidence_heuristic(span):
            add_entity(span)

    query_lower = user_query.lower()
    for entity in graph_entities:
        entity_lower = entity.lower()
        if len(entity_lower) < 3:
            continue

        if entity_lower in GENERIC_GRAPH_WORDS and " " not in entity_lower:
            continue

        boundary_match = re.search(
            rf"\b{re.escape(entity_lower)}\b",
            query_lower,
            re.IGNORECASE,
        )
        if boundary_match:
            add_entity(entity)
            continue

        if len(entity_lower) < 5:
            continue

        score = max(
            fuzz.partial_ratio(entity_lower, query_lower),
            fuzz.token_set_ratio(entity_lower, query_lower),
        )
        if score >= FUZZY_GRAPH_THRESHOLD:
            add_entity(entity)

    return detected


def detect_intent(user_query: str) -> str:
    """Logged for observability only; does not control retrieval routing."""
    query = user_query.lower()

    graph_keywords = [
        "connected", "related", "relationship", "associated", "linked",
        "organization", "organizations", "program", "programs", "entity", "entities",
    ]
    vector_keywords = [
        "explain", "describe", "summary", "summarize", "purpose", "meaning",
        "what does", "how does", "why", "works", "function",
    ]

    graph_score = sum(1 for word in graph_keywords if word in query)
    vector_score = sum(1 for word in vector_keywords if word in query)

    if graph_score > vector_score:
        return "graph"
    if vector_score > graph_score:
        return "vector"
    return "hybrid"


def _sanitize_cypher_param(value: str) -> str:
    """Strip characters that could break CONTAINS matching."""
    return re.sub(r"[^\w\s\-&'./]", "", value).strip()[:80]


def graph_retrieval(entities: list[str]) -> list[str]:
    """Single-hop graph retrieval with case-insensitive partial matching."""
    if not entities:
        logger.debug("graph_retrieval: no entities, skipping")
        return []

    safe_entities = []
    for entity in entities:
        cleaned = _sanitize_cypher_param(entity)
        if cleaned and len(cleaned) >= 2:
            safe_entities.append(cleaned)

    if not safe_entities:
        return []

    triples = []
    seen_triples = set()

    query = """
    MATCH (a)-[r]->(b)
    WHERE ANY(e IN $entities WHERE
        toLower(coalesce(a.label, '')) CONTAINS toLower(e)
        OR toLower(coalesce(b.label, '')) CONTAINS toLower(e)
    )
    RETURN DISTINCT
        coalesce(a.label, '') AS source,
        type(r) AS relation,
        coalesce(b.label, '') AS target
    LIMIT $limit
    """

    try:
        with driver.session() as session:
            results = session.run(
                query,
                entities=safe_entities,
                limit=GRAPH_LIMIT_PER_QUERY,
            )
            for record in results:
                source = (record.get("source") or "").strip()
                relation = (record.get("relation") or "RELATED_TO").strip()
                target = (record.get("target") or "").strip()
                if not source or not target:
                    continue

                triple = f"{source} --{relation}--> {target}"
                key = triple.lower()
                if key in seen_triples:
                    continue
                seen_triples.add(key)
                triples.append(triple)
    except Exception as exc:
        logger.warning("graph_retrieval failed: %s", exc)
        return []

    return triples[:MAX_GRAPH_TRIPLES]


def _normalize_chunk_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _trim_text(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def vector_retrieval(user_query: str) -> list[str]:
    """Neo4j vector index retrieval; always used regardless of entities."""
    if not user_query.strip():
        return []

    query_embedding = embedding_model.encode(user_query).tolist()
    formatted = []
    seen_chunks = set()

    cypher = """
    CALL db.index.vector.queryNodes(
        'chunk_embedding_index',
        $top_k,
        $embedding
    )
    YIELD node, score
    WHERE score >= $min_score
    RETURN node.text AS text,
           node.id AS chunk_id,
           score
    ORDER BY score DESC
  """

    try:
        with driver.session() as session:
            results = session.run(
                cypher,
                top_k=VECTOR_TOP_K,
                embedding=query_embedding,
                min_score=VECTOR_MIN_SCORE,
            )
            for record in results:
                text = record.get("text") or ""
                norm = _normalize_chunk_text(text)
                if not norm or norm in seen_chunks:
                    continue
                seen_chunks.add(norm)

                chunk_id = record.get("chunk_id") or "unknown"
                score = record.get("score")
                trimmed = _trim_text(text, MAX_CHUNK_CHARS)
                formatted.append(
                    f"[{chunk_id}] (relevance: {score:.3f})\n{trimmed}"
                )
    except Exception as exc:
        logger.warning("vector_retrieval failed: %s", exc)
        return []

    return formatted[:MAX_VECTOR_CHUNKS]


def _dedupe_lines(lines: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for line in lines:
        key = line.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped


def fuse_context(graph_context: list[str], vector_context: list[str]) -> str:
    """
    High-precision context fusion with deduplication and size caps.
    """
    graph_lines = _dedupe_lines(graph_context)[:MAX_GRAPH_TRIPLES]
    vector_lines = _dedupe_lines(vector_context)[:MAX_VECTOR_CHUNKS]

    sections = []

    if graph_lines:
        graph_body = "\n".join(f"- {line}" for line in graph_lines)
        sections.append(f"[GRAPH CONTEXT]\n{graph_body}")

    if vector_lines:
        vector_body = "\n\n".join(vector_lines)
        sections.append(f"[VECTOR CONTEXT]\n{vector_body}")

    fused = "\n\n".join(sections).strip()

    if len(fused) > MAX_FUSED_CONTEXT_CHARS:
        fused = fused[: MAX_FUSED_CONTEXT_CHARS - 3].rstrip() + "..."

    return fused


def build_context(graph_context: list[str], vector_context: list[str]) -> str:
    return fuse_context(graph_context, vector_context)


def _log_retrieval_debug(
    *,
    cleaned_query: str,
    entities: list[str],
    graph_count: int,
    vector_count: int,
    fused_chars: int,
) -> None:
    logger.info(
        "retrieval_debug | cleaned_query=%r | entities=%s | graph_results=%d | "
        "vector_results=%d | fused_context_chars=%d",
        cleaned_query,
        entities,
        graph_count,
        vector_count,
        fused_chars,
    )


def generate_response(user_query: str) -> str:
    if detect_prompt_injection(user_query):
        return "Prompt injection attempt detected."

    if detect_toxicity(user_query):
        return "Toxic or abusive language detected."

    if not check_guardrails(user_query):
        return "Only Apple supply chain related queries are allowed."

    sanitized_query = mask_pii(user_query)
    retrieval_query = clean_retrieval_query(sanitized_query)

    entities = detect_entities(sanitized_query)
    retrieval_mode = detect_intent(retrieval_query)

    graph_context = []
    if entities:
        graph_context = graph_retrieval(entities)

    vector_context = vector_retrieval(retrieval_query)

    final_context = build_context(graph_context, vector_context)

    _log_retrieval_debug(
        cleaned_query=retrieval_query,
        entities=entities,
        graph_count=len(graph_context),
        vector_count=len(vector_context),
        fused_chars=len(final_context),
    )

    prompt = f"""
You are an enterprise AI supply chain analyst.

Answer ONLY using the retrieved context.

Rules:
- Do not hallucinate
- Do not use outside knowledge
- If information is missing, say so
- Use graph context for relationships
- Use vector context for explanations
- Be concise but informative

Retrieved Context:
{final_context}

User Question:
{user_query}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    answer = response.choices[0].message.content

    log_interaction(
        original_query=user_query,
        sanitized_query=sanitized_query,
        retrieval_query=retrieval_query,
        detected_entities=entities,
        retrieval_mode=retrieval_mode,
        answer=answer,
    )

    return answer
