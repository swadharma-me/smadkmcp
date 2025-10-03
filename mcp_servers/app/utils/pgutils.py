import sys
import os
import json
import logging
from typing import Optional
from app.utils.llmutils import get_embeddings
from app.utils.pgconnect import execute_query, get_connection
from app.schemas.slokas import SlokaMeta, Gita, Bhagavatham, Mahabharata, Ramayana, Yogasutras, Utsav, Scriptures, Nuggets, Rasa, Marga

# Configuration constants
MAX_RESULTS_LIMIT = 50  # Maximum number of results to return from any query

# Set up logger for this module
logger = logging.getLogger("pgutils")

    
def get_bhashya_references(sloka_index: str, scripture_name: str | None) -> list:
    """Return list of bhashya (commentary) verse references for a base sloka.
    Each element: {"scripture_name": <str>, "sloka_index": <str>}.
    Supports:
      - Gita: all commentary verses mapped via gita_sloka_index
      - Yogasutras: single bhashya verse mapped via yogasutras_sloka_index
    Others: empty list.
    Gracefully handles errors.
    """
    if not sloka_index or not scripture_name:
        return []
    base = scripture_name.lower()
    try:
        if base == 'gita':
            q = """
                SELECT scripture_name, sloka_index
                FROM dharma.gita_bhashya
                WHERE gita_sloka_index = %s
            """
            rows = execute_query(q, params=(sloka_index,), fetch='all') or []
            return [
                {"scripture_name": r.get("scripture_name"), "sloka_index": r.get("sloka_index")}
                for r in rows if r and r.get('sloka_index')
            ]
        if base == 'yogasutras':
            q = """
                SELECT yogasutras_bhashya_sloka_index AS sloka_index, scripture_name
                FROM dharma.yogasutras_bhashyas
                WHERE sloka_index = %s
                LIMIT 1
            """
            r = execute_query(q, params=(sloka_index,), fetch='one')
            if r and r.get('sloka_index'):
                return [{"scripture_name": r.get('scripture_name'), "sloka_index": r.get('sloka_index')}]
        return []
    except Exception as e:
        logger.error(f"get_bhashya_references error for {sloka_index=} {scripture_name=}: {e}")
        return []


def get_bashya_sloka_index_given_gita_sloka_index(gita_sloka_index: str, scripture_name:str) -> Optional[str]:
    """
    Get the corresponding Bhashya sloka index for a given Gita sloka index.
    
    Args:
        gita_sloka_index (str): The Gita sloka index to look up.
        scripture_name (str): The name of the scripture to filter by.
        
    Returns:
        Optional[str]: The corresponding Bhashya sloka index if found, else None.
    """
    query = """
        SELECT sloka_index FROM dharma.gita_bhashya
        WHERE gita_sloka_index = %s AND scripture_name = %s
        LIMIT 1;
    """
    try:
        result = execute_query(query, params=(gita_sloka_index, scripture_name), fetch='one')
        return result['sloka_index'] if result else None
    except Exception as e:
        logger.error(f"Failed to get Bhashya sloka index for Gita sloka {gita_sloka_index}: {e}")
        return None


def get_gita_sloka_index_given_bhashya_sloka_index(bhashya_sloka_index: str, scripture_name:str) -> Optional[str]:
    """
    Get the corresponding Gita sloka index for a given Bhashya sloka index.
    
    Args:
        bhashya_sloka_index (str): The Bhashya sloka index to look up.
        scripture_name (str): The name of the scripture to filter by.
        
    Returns:
        Optional[str]: The corresponding Gita sloka index if found, else None.
    """
    query = """
        SELECT gita_sloka_index FROM dharma.gita_bhashya
        WHERE sloka_index = %s AND scripture_name = %s
        LIMIT 1;
    """
    try:
        result = execute_query(query, params=(bhashya_sloka_index, scripture_name), fetch='one')
    
        return result['gita_sloka_index'] if result else None
    except Exception as e:
        logger.error(f"Failed to get Gita sloka index for Bhashya sloka {bhashya_sloka_index}: {e}")
        return None
    

def get_yogasutras_sloka_index_given_yogasutras_bhashya_sloka_index(yogasutras_bhashya_sloka_index: str, scripture_name:str) -> Optional[str]:
    """
    Get the corresponding Yogasutras sloka index for a given Yogasutras Bhashya sloka index.
    
    Args:
        yogasutras_bhashya_sloka_index (str): The Yogasutras Bhashya sloka index to look up.
        scripture_name (str): The name of the scripture to filter by.
        
    Returns:
        Optional[str]: The corresponding Yogasutras sloka index if found, else None.
    """
    query = """
        SELECT sloka_index FROM dharma.yogasutras_bhashyas
        WHERE yogasutras_bhashya_sloka_index = %s AND scripture_name = %s
        LIMIT 1;
    """
    try:
        result = execute_query(query, params=(yogasutras_bhashya_sloka_index, scripture_name), fetch='one')
        return result['sloka_index'] if result else None
    except Exception as e:
        logger.error(f"Failed to get Yogasutras sloka index for Bhashya sloka {yogasutras_bhashya_sloka_index}: {e}")
        return None

def get_yogasutras_bhashya_sloka_index_given_yogasutras_sloka_index(yogasutras_sloka_index: str, scripture_name:str) -> Optional[str]:  
    """
    Get the corresponding Yogasutras Bhashya sloka index for a given Yogasutras sloka index.
    
    Args:
        yogasutras_sloka_index (str): The Yogasutras sloka index to look up.
        scripture_name (str): The name of the scripture to filter by.
        
    Returns:
        Optional[str]: The corresponding Yogasutras Bhashya sloka index if found, else None.
    """
    query = """
        SELECT yogasutras_bhashya_sloka_index FROM dharma.yogasutras_bhashyas
        WHERE sloka_index = %s AND scripture_name = %s
        LIMIT 1;
    """
    try:
        result = execute_query(query, params=(yogasutras_sloka_index, scripture_name), fetch='one')
        return result['yogasutras_bhashya_sloka_index'] if result else None
    except Exception as e:
        logger.error(f"Failed to get Yogasutras Bhashya sloka index for sloka {yogasutras_sloka_index}: {e}")
        return None


def search_sloka_meaning_en_embeddings_top_n(text, top_n=1, scripture_list=None):
    """
    Search for the top-N most semantically similar slokas (English meaning embeddings).
    Returns lean rows (no aggregated context_text) to reduce token usage.
    Output fields per match: sloka_index, scripture_name, input_sloka, english_meaning, glossary_keywords, score, bhashya_sloka_indexes.
    """
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    scripture_filter = ""
    if scripture_list:
        escaped_scriptures = [s.replace("'", "''") for s in scripture_list]
        scripture_conditions = " OR ".join([f"scripture_name = '{s}'" for s in escaped_scriptures])
        scripture_filter = f" AND ({scripture_conditions})"

    content_type_filter = " AND content_type = 'english'"

    query = f"""
        SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords,
               (1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.sloka_meaning_en_embeddings
        WHERE 1=1
        {content_type_filter}
        {scripture_filter}
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching sloka_meaning_en_embeddings lean (top_n={top_n}) scriptures={scripture_list}")
        results = execute_query(query, fetch='all') or []
        output_matches = []
        for r in results:
            si = r.get('sloka_index')
            if not si:
                continue
            sn = r.get('scripture_name')
            enriched = {
                'sloka_index': si,
                'scripture_name': sn,
                'input_sloka': r.get('input_sloka'),
                'english_meaning': r.get('english_meaning'),
                'glossary_keywords': r.get('glossary_keywords'),
                'score': r.get('score'),
                'bhashya_sloka_indexes': get_bhashya_references(si, sn)
            }
            output_matches.append(enriched)
        logger.info(f"Found {len(output_matches)} english matches")
        return output_matches
    except Exception as e:
        logger.error(f"Failed english semantic search: {e}")
        return []


def search_sloka_meaning_sa_embeddings_top_n(text, top_n=1, scripture_list=None):
    """Search for top-N similar slokas (Sanskrit embeddings) with bhashya references."""
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    scripture_filter = ""
    if scripture_list:
        escaped_scriptures = [s.replace("'", "''") for s in scripture_list]
        scripture_conditions = " OR ".join([f"scripture_name = '{s}'" for s in escaped_scriptures])
        scripture_filter = f" AND ({scripture_conditions})"

    content_type_filter = " AND content_type = 'sanskrit'"

    query = f"""
        SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords,
               (1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.sloka_meaning_sa_embeddings
        WHERE 1=1
        {content_type_filter}
        {scripture_filter}
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching sloka_meaning_sa_embeddings lean (top_n={top_n}) scriptures={scripture_list}")
        results = execute_query(query, fetch='all') or []
        output_matches = []
        for r in results:
            si = r.get('sloka_index')
            if not si:
                continue
            sn = r.get('scripture_name')
            output_matches.append({
                'sloka_index': si,
                'scripture_name': sn,
                'input_sloka': r.get('input_sloka'),
                'english_meaning': r.get('english_meaning'),
                'glossary_keywords': r.get('glossary_keywords'),
                'score': r.get('score'),
                'bhashya_sloka_indexes': get_bhashya_references(si, sn)
            })
        logger.info(f"Found {len(output_matches)} sanskrit matches")
        return output_matches
    except Exception as e:
        logger.error(f"Failed sanskrit semantic search: {e}")
        return []


def search_sloka_meaning_glossary_embeddings_top_n(text, top_n=1, scripture_list=None):
    """Search for top-N similar slokas (Glossary embeddings) with bhashya references."""
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    scripture_filter = ""
    if scripture_list:
        escaped_scriptures = [s.replace("'", "''") for s in scripture_list]
        scripture_conditions = " OR ".join([f"scripture_name = '{s}'" for s in escaped_scriptures])
        scripture_filter = f" AND ({scripture_conditions})"

    content_type_filter = " AND content_type = 'glossary'"

    query = f"""
        SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords,
               (1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.sloka_meaning_glossary_embeddings
        WHERE 1=1
        {content_type_filter}
        {scripture_filter}
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching sloka_meaning_glossary_embeddings lean (top_n={top_n}) scriptures={scripture_list}")
        results = execute_query(query, fetch='all') or []
        output_matches = []
        for r in results:
            si = r.get('sloka_index')
            if not si:
                continue
            sn = r.get('scripture_name')
            output_matches.append({
                'sloka_index': si,
                'scripture_name': sn,
                'input_sloka': r.get('input_sloka'),
                'english_meaning': r.get('english_meaning'),
                'glossary_keywords': r.get('glossary_keywords'),
                'score': r.get('score'),
                'bhashya_sloka_indexes': get_bhashya_references(si, sn)
            })
        logger.info(f"Found {len(output_matches)} glossary matches")
        return output_matches
    except Exception as e:
        logger.error(f"Failed glossary semantic search: {e}")
        return []

def get_sloka_meanings(sloka_index=None, scripture_name=None):
    """Fetch sloka meanings with optional filters and attach bhashya references."""
    query = "SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords FROM dharma.sloka_meaning"
    filters = []
    if sloka_index:
        filters.append("sloka_index = '%s'" % sloka_index.replace("'", "''"))
    if scripture_name:
        filters.append("LOWER(scripture_name) = '%s'" % scripture_name.lower().replace("'", "''"))
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += f" LIMIT {MAX_RESULTS_LIMIT}"
    try:
        results = execute_query(query, fetch='all') or []
        for row in results:
            row['bhashya_sloka_indexes'] = get_bhashya_references(row.get('sloka_index'), row.get('scripture_name'))
        return results
    except Exception as e:
        logger.error(f"Failed to fetch sloka meanings: {e}")
        return []

def fetch_utsav_records(sloka_index=None):
    query = "SELECT * FROM dharma.utsavs"
    filters = []
    if sloka_index:
        filters.append(f"sloka_index = '{sloka_index}'")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    else:
        # Limit results when no specific sloka_index is provided
        query += f" LIMIT {MAX_RESULTS_LIMIT}"
    try:
        results = execute_query(query, fetch='all')
        utsav_list = [Utsav(**row) for row in results]
        logger.debug(f"Fetched Utsav records: {utsav_list}")
        return utsav_list
    except Exception as e:
        logger.error(f"Failed to fetch utsav records: {e}")
        return []

# Fetch all records from scriptures as a list of Scriptures objects

def list_all_scriptures():
    """
    Fetch scriptures metadata. Return raw dict rows instead of Pydantic models to be
    resilient to schema drifts (e.g., optional columns like target_table_name).

    Expected columns (when present):
      - scripture_name, author, description, summary, publication_year,
        language, genre, start_sloka_index, end_sloka_index, target_table_name
    """
    query = f"SELECT * FROM dharma.scriptures LIMIT {MAX_RESULTS_LIMIT}"
    try:
        results = execute_query(query, fetch='all') or []
        # Ensure we always return a list of plain dicts
        normalized = []
        for row in results:
            try:
                # Some callers expect start/end_sloka_index to infer canonical prefix
                normalized.append({
                    **row,
                    # keep keys as-is; add explicit None defaults for optional fields when missing
                    'target_table_name': row.get('target_table_name'),
                })
            except Exception:
                # Fallback: include row as-is
                normalized.append(row)
        logger.debug(f"Fetched Scriptures records: {len(normalized)} rows")
        return normalized
    except Exception as e:
        logger.error(f"Failed to fetch scriptures records: {e}")
        return []

def get_sloka_idf_scores_summary(keywords_list, max_results=10):
    """
    Get summary of IDF scores for keywords across slokas.
    
    Args:
        keywords_list (list): List of keywords to search for
        max_results (int): Maximum number of results to return (max 50)
    
    Returns:
        list: Summary of IDF scores
    """
    # Enforce maximum results limit
    max_results = min(max_results, MAX_RESULTS_LIMIT)
    
    # TODO: Implement IDF scores functionality
    logger.info(f"IDF scores summary requested for keywords: {keywords_list}, max_results: {max_results}")
    return []

def get_slokas_before_current_sloka(current_sloka_index, scripture_name=None, number_before=5):
    """Fetch slokas appearing before the given sloka (lean rows)."""
    query = "SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords FROM dharma.sloka_meaning"
    query += " WHERE sloka_index < %s"
    params = [current_sloka_index]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    query += " ORDER BY sloka_index DESC LIMIT %s"
    params.append(number_before)
    try:
        rows = execute_query(query, params=params, fetch='all') or []
        results = [
            {
                'sloka_index': r.get('sloka_index'),
                'scripture_name': r.get('scripture_name'),
                'input_sloka': r.get('input_sloka'),
                'english_meaning': r.get('english_meaning'),
                'glossary_keywords': r.get('glossary_keywords')
            } for r in rows if r.get('sloka_index')
        ]
        logger.debug(f"Fetched {len(results)} slokas before {current_sloka_index}")
        return results
    except Exception as e:
        logger.error(f"Failed to fetch slokas before current sloka: {e}")
        return []

def get_slokas_after_current_sloka(current_sloka_index, scripture_name=None, number_after=5):
    """Fetch slokas appearing after the given sloka (lean rows)."""
    query = "SELECT sloka_index, scripture_name, input_sloka, english_meaning, keywords as glossary_keywords FROM dharma.sloka_meaning"
    query += " WHERE sloka_index > %s"
    params = [current_sloka_index]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    query += " ORDER BY sloka_index ASC LIMIT %s"
    params.append(number_after)
    try:
        rows = execute_query(query, params=params, fetch='all') or []
        results = [
            {
                'sloka_index': r.get('sloka_index'),
                'scripture_name': r.get('scripture_name'),
                'input_sloka': r.get('input_sloka'),
                'english_meaning': r.get('english_meaning'),
                'glossary_keywords': r.get('glossary_keywords')
            } for r in rows if r.get('sloka_index')
        ]
        logger.debug(f"Fetched {len(results)} slokas after {current_sloka_index}")
        return results
    except Exception as e:
        logger.error(f"Failed to fetch slokas after current sloka: {e}")
        return []   
    
def get_gita_sloka_index_given_bashya_sloka_index(bashya_sloka_index, scripture_name=None):
    """
    Fetch the sloka index for a given bhashya sloka.
    
    Args:
        sloka_index (str): The index of the bhashya sloka
        scripture_name (str, optional): Name of the scripture to filter by
    
    Returns:
        str: The corresponding sloka index if found, else None
    """
    query = "SELECT gita_sloka_index, sloka_index FROM dharma.gita_bhashya WHERE sloka_index = %s"
    params = [bashya_sloka_index]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    
    try:
        result = execute_query(query, params=params, fetch='one')
        if result:
            return result.get('gita_sloka_index')
        return None
    except Exception as e:
        logger.error(f"Failed to get sloka index by bhashya: {e}")
        return None

def get_all_bhashya_sloka_indexes_given_gita_sloka_index(gita_sloka_index, scripture_name=None):
    """
    Fetch all bhashya sloka indices for a given Gita sloka.

    Args:
        gita_sloka_index (str): The index of the Gita sloka
        scripture_name (str, optional): Name of the scripture to filter by
    
    Returns:
        list: A list of corresponding bhashya sloka indices if found, else an empty list
    """
    query = "SELECT scripture_name, sloka_index FROM dharma.gita_bhashya WHERE gita_sloka_index = %s"
    params = [gita_sloka_index]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    
    try:
        result = execute_query(query, params=params, fetch='fetchall')
        if result:
            return [row.get('sloka_index') for row in result]
        return []
    except Exception as e:
        logger.error(f"Failed to get bhashya sloka index by Gita sloka: {e}")
        return []

def get_yogasutra_bashya_id_given_sutra_id(sutra_id, scripture_name=None):
    """
    Fetch the bhashya ID for a given Yogasutra sutra ID.
    
    Args:
        sutra_id (str): The ID of the Yogasutra sutra
        scripture_name (str, optional): Name of the scripture to filter by
    
    Returns:
        str: The corresponding bhashya ID if found, else None
    """
    query = "SELECT bhashya_id FROM dharma.yogasutra_bhashya WHERE sutra_id = %s"
    params = [sutra_id]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    
    try:
        result = execute_query(query, params=params, fetch='one')
        if result:
            return result.get('bhashya_id')
        return None
    except Exception as e:
        logger.error(f"Failed to get bhashya ID by sutra ID: {e}")
        return None

def get_yogasutra_sutra_id_given_bhashya_id(bhashya_id, scripture_name=None):
    """
    Fetch the sutra ID for a given Yogasutra bhashya ID.
    
    Args:
        bhashya_id (str): The ID of the Yogasutra bhashya
        scripture_name (str, optional): Name of the scripture to filter by
    
    Returns:
        str: The corresponding sutra ID if found, else None
    """
    query = "SELECT sutra_id FROM dharma.yogasutra_bhashya WHERE bhashya_id = %s"
    params = [bhashya_id]
    if scripture_name:
        query += " AND LOWER(scripture_name) = %s"
        params.append(scripture_name.lower())
    
    try:
        result = execute_query(query, params=params, fetch='one')
        if result:
            return result.get('sutra_id')
        return None
    except Exception as e:
        logger.error(f"Failed to get sutra ID by bhashya ID: {e}")
        return None

def trace_immediate_context(sloka_index, scripture_name):
    """
    Fetch immediate context for a sloka: previous 3, current, and next 3 slokas.
    Returns a single ordered list: [previous...(chronological), current, next...]
    """
    previous_slokas = get_slokas_before_current_sloka(sloka_index, scripture_name)
    # Ensure previous slokas are in ascending order for natural reading
    previous_slokas = list(reversed(previous_slokas)) if previous_slokas else []

    # Fetch current sloka (lean with bhashya references)
    current_list = get_sloka_meanings(sloka_index=sloka_index, scripture_name=scripture_name)
    current_sloka = current_list[0] if current_list else None

    # Placeholder collection before adding next slokas (per request)
    sloka_collection = previous_slokas + ([current_sloka] if current_sloka else [])

    next_slokas = get_slokas_after_current_sloka(sloka_index, scripture_name)

    sloka_collection += next_slokas
    return sloka_collection

def trace_back_chapter_context(sloka_index, scripture_name):
    if scripture_name.lower() not in ["ramayana", "mahabharata", "bhagavatham"]:
        return []
    elif scripture_name.lower() == "ramayana":
        query ="""
            SELECT short_summary, long_summary, emotional_elements,key_characters,thematic_analysis,dharmic_insights,sanskrit_glossary  FROM dharma.mv_ramayana_sarga_embeddings_enriched
            WHERE %s BETWEEN start_sloka_index AND end_sloka_index
        """
    elif scripture_name.lower() == "mahabharata":
        query ="""
            SELECT short_summary, long_summary, emotional_elements,key_characters,thematic_analysis,dharmic_insights,sanskrit_glossary FROM dharma.mv_mahabharata_sarga_embeddings_enriched
            WHERE %s BETWEEN start_sloka_index AND end_sloka_index
        """
    elif scripture_name.lower() == "bhagavatham":
        query ="""
            SELECT short_summary, long_summary, emotional_elements,key_characters,thematic_analysis,dharmic_insights,sanskrit_glossary FROM dharma.mv_bhagavatham_glossary
            WHERE %s BETWEEN start_sloka_index AND end_sloka_index

    """
    try:
        result = execute_query(query, params=(scripture_name, sloka_index), fetch='all')
        return [{
            "short_summary": row['short_summary'],
            "long_summary": row['long_summary'],
            "emotional_elements": row['emotional_elements'],
            "key_characters": row['key_characters'],
            "thematic_analysis": row['thematic_analysis'],
            "dharmic_insights": row['dharmic_insights'],
            "sanskrit_glossary": row['sanskrit_glossary']
        } for row in result] if result else []
    except Exception as e:
        logger.error(f"Failed to trace back chapter context for sloka {sloka_index}: {e}")
        return []
    
## All search functions for summarries and glossaries for ramayana,bhagavatham and mahabharata 
def search_ramayana_sarga_summary_embeddings_top_n(text, top_n=1, scripture_name="ramayana"):
    """
    Search for the top-N most semantically similar Ramayana sarga summaries using vector embeddings.
    
    This function performs semantic search against the mv_ramayana_sarga_embeddings_enriched materialized view,
    which contains sarga summaries and their vector embeddings. It uses cosine similarity
    to find the most relevant sargas based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "ramayana".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - kanda_name (str): Name of the kanda
            - total_slokas (int): Total number of slokas in this sarga
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the sarga
            - long_summary (str): Detailed summary of the sarga
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against sarga-level summaries for narrative context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,kanda_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_ramayana_sarga_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching ramayana sarga summaries (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "kanda_name": row.get('kanda_name'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Ramayana sargas with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search ramayana sarga summary embeddings: {e}")
        return []


def search_ramayana_sarga_glossary_embeddings_top_n(text, top_n=1, scripture_name="ramayana"):
    """
    Search for the top-N most semantically similar Ramayana sarga glossaries using vector embeddings.
    
    This function performs semantic search against the mv_ramayana_glossary_embeddings_enriched materialized view,
    which contains sarga glossaries and their vector embeddings. It uses cosine similarity
    to find the most relevant Sanskrit terms and explanations based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "ramayana".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - kanda_name (str): Name of the kanda
            - total_slokas (int): Total number of slokas in this sarga
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the sarga
            - long_summary (str): Detailed summary of the sarga
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against Sanskrit glossary content for terminology context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,kanda_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_ramayana_glossary_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching ramayana glossary embeddings (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "kanda_name": row.get('kanda_name'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Ramayana glossary entries with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search ramayana glossary embeddings: {e}")
        return []


def search_mahabharata_adhyaya_summary_embeddings_top_n(text, top_n=1, scripture_name="mahabharata"):
    """
    Search for the top-N most semantically similar Mahabharata adhyaya summaries using vector embeddings.
    
    This function performs semantic search against the mv_mahabharata_adhyaya_embeddings_enriched materialized view,
    which contains adhyaya summaries and their vector embeddings. It uses cosine similarity
    to find the most relevant adhyayas based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "mahabharata".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - parva_name (str): Name of the parva
            - total_slokas (int): Total number of slokas in this adhyaya
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the adhyaya
            - long_summary (str): Detailed summary of the adhyaya
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against adhyaya-level summaries for narrative context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,parva_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_mahabharata_adhyaya_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching mahabharata adhyaya summaries (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "parva_name": row.get('parva_name'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Mahabharata adhyayas with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search mahabharata adhyaya summary embeddings: {e}")
        return []


def search_mahabharata_glossary_embeddings_top_n(text, top_n=1, scripture_name="mahabharata"):
    """
    Search for the top-N most semantically similar Mahabharata glossaries using vector embeddings.
    
    This function performs semantic search against the mv_mahabharata_glossary_embeddings_enriched materialized view,
    which contains adhyaya glossaries and their vector embeddings. It uses cosine similarity
    to find the most relevant Sanskrit terms and explanations based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "mahabharata".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - parva (str): Parva number/name
            - adhyaya (str): Adhyaya number/name  
            - parva_name (str): Name of the parva
            - total_slokas (int): Total number of slokas in this adhyaya
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the adhyaya
            - long_summary (str): Detailed summary of the adhyaya
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against Sanskrit glossary content for terminology context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,parva_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_mahabharata_glossary_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching mahabharata glossary embeddings (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "parva": row.get('parva'),
                "adhyaya": row.get('adhyaya'),
                "parva_name": row.get('parva_name'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Mahabharata glossary entries with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search mahabharata glossary embeddings: {e}")
        return []


def search_bhagavatham_adhyaya_summary_embeddings_top_n(text, top_n=1, scripture_name="bhagavatham"):
    """
    Search for the top-N most semantically similar Bhagavatham adhyaya summaries using vector embeddings.
    
    This function performs semantic search against the mv_bhagavatham_adhyaya_embeddings_enriched materialized view,
    which contains adhyaya summaries and their vector embeddings. It uses cosine similarity
    to find the most relevant adhyayas based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "bhagavatham".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - skanda_name (str): Name of the skanda
            - total_slokas (int): Total number of slokas in this adhyaya
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the adhyaya
            - long_summary (str): Detailed summary of the adhyaya
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against adhyaya-level summaries for narrative context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,skanda_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_bhagavatham_adhyaya_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching bhagavatham adhyaya summaries (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "skanda_name": row.get('skanda_name'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Bhagavatham adhyayas with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search bhagavatham adhyaya summary embeddings: {e}")
        return []


def search_bhagavatham_glossary_embeddings_top_n(text, top_n=1, scripture_name="bhagavatham"):
    """
    Search for the top-N most semantically similar Bhagavatham glossaries using vector embeddings.
    
    This function performs semantic search against the mv_bhagavatham_glossary_embeddings_enriched materialized view,
    which contains adhyaya glossaries and their vector embeddings. It uses cosine similarity
    to find the most relevant Sanskrit terms and explanations based on the input text.

    Args:
        text (str): Input text to search for using semantic embeddings
        top_n (int, optional): Number of top matches to return. Defaults to 1. 
                              Maximum allowed is 50 (enforced by MAX_RESULTS_LIMIT)
        scripture_name (str, optional): Scripture name to filter by. Defaults to "bhagavatham".

    Returns:
        list[dict]: List of up to top_n dictionaries, each containing:
            - summary_id (int): Unique identifier for the summary
            - skanda (str): Skanda number/name
            - total_slokas (int): Total number of slokas in this adhyaya
            - start_sloka_index (str): Starting sloka index
            - end_sloka_index (str): Ending sloka index
            - short_summary (str): Brief summary of the adhyaya
            - long_summary (str): Detailed summary of the adhyaya
            - emotional_elements (str): Emotional aspects present
            - key_characters (str): Main characters involved
            - thematic_analysis (str): Thematic elements analysis
            - dharmic_insights (str): Dharmic teachings and insights
            - sanskrit_glossary (str): Sanskrit terms and explanations
            - score (float): Cosine similarity score (0-1, higher is better)
    
    Notes:
        - Uses cosine similarity: (1 - (embedding <#> query_embedding)) for scoring
        - Searches against Sanskrit glossary content for terminology context
        - Results are ordered by similarity score (highest first)
        
    Raises:
        Exception: Database query errors are logged and empty list is returned
    """
    # Enforce maximum results limit
    top_n = min(top_n, MAX_RESULTS_LIMIT)
    
    sloka_embedding = get_embeddings(text)
    emb_str = str(sloka_embedding.tolist()) if hasattr(sloka_embedding, 'tolist') else str(sloka_embedding)

    query = f"""
        SELECT summary_id,skanda_name, total_slokas, start_sloka_index, end_sloka_index, short_summary, long_summary, emotional_elements, key_characters, thematic_analysis, dharmic_insights, sanskrit_glossary,(1 - (embedding <#> '{emb_str}')) AS score
        FROM dharma.mv_bhagavatham_glossary_embeddings_enriched
        WHERE 1=1
        ORDER BY score DESC
        LIMIT {top_n};
    """
    try:
        logger.info(f"Searching bhagavatham glossary embeddings (top_n={top_n}): {emb_str[:50]}... (scripture={scripture_name})")
        results = execute_query(query, fetch='all')
        
        output_matches = []
        for row in results:
            output_matches.append({
                "summary_id": row.get('summary_id'),
                "skanda": row.get('skanda'),
                "total_slokas": row.get('total_slokas'),
                "start_sloka_index": row.get('start_sloka_index'),
                "end_sloka_index": row.get('end_sloka_index'),
                "short_summary": row.get('short_summary'),
                "long_summary": row.get('long_summary'),
                "emotional_elements": row.get('emotional_elements'),
                "key_characters": row.get('key_characters'),
                "thematic_analysis": row.get('thematic_analysis'),
                "dharmic_insights": row.get('dharmic_insights'),
                "sanskrit_glossary": row.get('sanskrit_glossary'),
                "score": row.get('score')
            })
            
        logger.info(f"Found {len(output_matches)} matching Bhagavatham glossary entries with scores: {[m['score'] for m in output_matches[:3]]}")
        return output_matches
    except Exception as e:
        logger.error(f"Failed to search bhagavatham glossary embeddings: {e}")
        return []

def search_enriched_dharma_concepts(text, top_n=3):
    """
    Semantic search over dharma.dharmic_enriched_concepts using pgvector cosine similarity.

    Args:
        text (str): Query text to embed and search against the table embedding column.
        top_n (int): Number of top matches to return (capped by MAX_RESULTS_LIMIT).

    Returns:
        list[dict]: Each dict includes selected columns and a similarity 'score' (0..1).
    """
    try:
        if not text or not str(text).strip():
            return []
        # Enforce maximum results limit
        top_n = min(top_n, MAX_RESULTS_LIMIT)

        # Build embedding for the input query
        query_embedding = get_embeddings(text)
        emb_str = str(query_embedding.tolist()) if hasattr(query_embedding, 'tolist') else str(query_embedding)

        # Use cosine similarity via pgvector: 1 - (embedding <#> query_embedding)
        query = f"""
            SELECT
                id,
                concept_name,
                secular_one_liner,
                dharmic_one_liner,
                expanded_sanskrit_glossary,
                expanded_references,
                expanded_sadhana,
                detailed_commentary,
                key_insights_gita_yogasutras,
                connected_examples_from_itihasas,
                contemplative_questions,
                tags,
                refs,
                sadhana,
                sanskrit_glossary,
                commentary,
                content_type,
                (1 - (embedding <#> '{emb_str}')) AS score
            FROM dharma.dharmic_enriched_concepts
            WHERE content_type = 'dharmic_concept'
            ORDER BY score DESC
            LIMIT {top_n};
        """

        logger.info(
            f"Searching dharmic_enriched_concepts (top_n={top_n}) "
            f"query_emb_sample={emb_str[:64]}..."
        )

        rows = execute_query(query, fetch='all') or []
        results = []
        for r in rows:
            # Keep payload lean but useful; include score for ranking transparency
            results.append({
                "id": r.get("id"),
                "concept_name": r.get("concept_name"),
                "secular_one_liner": r.get("secular_one_liner"),
                "dharmic_one_liner": r.get("dharmic_one_liner"),
                "expanded_sanskrit_glossary": r.get("expanded_sanskrit_glossary"),
                "expanded_references": r.get("expanded_references"),
                "expanded_sadhana": r.get("expanded_sadhana"),
                "detailed_commentary": r.get("detailed_commentary"),
                "key_insights_gita_yogasutras": r.get("key_insights_gita_yogasutras"),
                "connected_examples_from_itihasas": r.get("connected_examples_from_itihasas"),
                "contemplative_questions": r.get("contemplative_questions"),
                "tags": r.get("tags"),
                "refs": r.get("refs"),
                "sadhana": r.get("sadhana"),
                "sanskrit_glossary": r.get("sanskrit_glossary"),
                "commentary": r.get("commentary"),
                "content_type": r.get("content_type"),
                "score": r.get("score"),
            })

        logger.info(f"Found {len(results)} enriched dharmic concepts")
        return results

    except Exception as e:
        logger.error(f"Failed to search enriched dharmic concepts: {e}")
        return []