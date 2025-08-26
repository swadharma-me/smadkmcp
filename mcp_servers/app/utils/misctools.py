"""
Miscellaneous utility functions for date/time operations and text transliteration.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

# Set up logger for this module
logger = logging.getLogger("misctools")
logger.setLevel(logging.INFO)

# Add a handler if one doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

try:
    from indic_transliteration import sanscript
    transliteration_available = True
    logger.info("Indic transliteration library loaded successfully")
except ImportError:
    transliteration_available = False
    logger.warning("Indic transliteration library not available. Install with: pip install indic-transliteration")


def get_current_datetime_formatted() -> dict:
    """
    Get the current date and time in full format with GMT time.
    
    Returns:
        Dictionary containing formatted date/time information:
        - formatted_date: DD MM YYYY format
        - formatted_time: HH:MM:SS format  
        - gmt_datetime: Full GMT datetime string
        - local_datetime: Full local datetime string
        - timestamp: Unix timestamp
    """
    try:
        # Get current time in local timezone
        local_now = datetime.now()
        
        # Get current time in GMT/UTC
        gmt_now = datetime.now(timezone.utc)
        
        # Format date as DD MM YYYY
        formatted_date = local_now.strftime("%d %m %Y")
        
        # Format time as HH:MM:SS
        formatted_time = local_now.strftime("%H:%M:%S")
        
        # Full GMT datetime string
        gmt_datetime = gmt_now.strftime("%d %m %Y %H:%M:%S GMT")
        
        # Full local datetime string
        local_datetime = local_now.strftime("%d %m %Y %H:%M:%S %Z")
        
        # Unix timestamp
        timestamp = int(local_now.timestamp())
        
        result = {
            "formatted_date": formatted_date,
            "formatted_time": formatted_time,
            "gmt_datetime": gmt_datetime,
            "local_datetime": local_datetime,
            "timestamp": timestamp,
            "iso_format": local_now.isoformat(),
            "gmt_iso_format": gmt_now.isoformat()
        }
        
        logger.info(f"Generated datetime info: {formatted_date} {formatted_time}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating datetime info: {e}")
        return {
            "error": f"Failed to get datetime: {str(e)}",
            "formatted_date": "",
            "formatted_time": "",
            "gmt_datetime": "",
            "local_datetime": "",
            "timestamp": 0
        }


def transliterate_sloka(sloka_text: str, target_script: str = "telugu") -> dict:
    """
    Transliterate a Sanskrit sloka from Devanagari to target Indic script.
    
    Args:
        sloka_text: The Sanskrit text in Devanagari script
        target_script: Target script for transliteration. Supported scripts include:
                      'telugu', 'tamil', 'kannada', 'malayalam', 'gujarati', 
                      'gurmukhi', 'bengali', 'oriya', 'iast' (romanized)
    
    Returns:
        Dictionary containing:
        - original_text: Input text
        - transliterated_text: Text in target script
        - source_script: Source script (devanagari)
        - target_script: Target script name
        - success: Boolean indicating if transliteration succeeded
    """
    try:
        if not transliteration_available:
            return {
                "original_text": sloka_text,
                "transliterated_text": "",
                "source_script": "devanagari",
                "target_script": target_script,
                "success": False,
                "error": "Indic transliteration library not available. Install with: pip install indic-transliteration"
            }
        
        if not sloka_text or not sloka_text.strip():
            return {
                "original_text": sloka_text,
                "transliterated_text": "",
                "source_script": "devanagari", 
                "target_script": target_script,
                "success": False,
                "error": "No input text provided"
            }
        
        # Map common script names to sanscript constants
        script_mapping = {
            'telugu': sanscript.TELUGU,
            'tamil': sanscript.TAMIL,
            'kannada': sanscript.KANNADA,
            'malayalam': sanscript.MALAYALAM,
            'gujarati': sanscript.GUJARATI,
            'gurmukhi': sanscript.GURMUKHI,
            'bengali': sanscript.BENGALI,
            'oriya': sanscript.ORIYA,
            'iast': sanscript.IAST,  # Romanized Sanskrit
            'itrans': sanscript.ITRANS,
            'hk': sanscript.HK,  # Harvard-Kyoto
            'slp1': sanscript.SLP1  # Sanskrit Library Phonetic Basic
        }
        
        target_script_lower = target_script.lower()
        if target_script_lower not in script_mapping:
            available_scripts = ', '.join(script_mapping.keys())
            return {
                "original_text": sloka_text,
                "transliterated_text": "",
                "source_script": "devanagari",
                "target_script": target_script,
                "success": False,
                "error": f"Unsupported target script '{target_script}'. Available scripts: {available_scripts}"
            }
        
        # Perform transliteration from Devanagari to target script
        transliterated = sanscript.transliterate(
            sloka_text.strip(),
            sanscript.DEVANAGARI,
            script_mapping[target_script_lower]
        )
        
        result = {
            "original_text": sloka_text,
            "transliterated_text": transliterated,
            "source_script": "devanagari",
            "target_script": target_script_lower,
            "success": True
        }
        
        logger.info(f"Successfully transliterated text to {target_script_lower}")
        return result
        
    except Exception as e:
        logger.error(f"Error during transliteration: {e}")
        return {
            "original_text": sloka_text,
            "transliterated_text": "",
            "source_script": "devanagari",
            "target_script": target_script,
            "success": False,
            "error": f"Transliteration failed: {str(e)}"
        }


def get_supported_scripts() -> list:
    """
    Get list of supported transliteration scripts.
    
    Returns:
        List of supported script names
    """
    if not transliteration_available:
        return []
    
    return [
        'telugu', 'tamil', 'kannada', 'malayalam', 'gujarati',
        'gurmukhi', 'bengali', 'oriya', 'iast', 'itrans', 'hk', 'slp1'
    ]


def normalize_sloka_search_results(raw: list) -> list:
    """Normalize raw verse search rows into standard dicts."""
    normalized = []
    for idx, r in enumerate(raw or []):
        if not isinstance(r, dict):
            continue
        si = r.get('sloka_index')
        if not si:
            continue
        normalized.append({
            'sloka_index': si,
            'scripture_name': r.get('scripture_name'),
            'score': r.get('score'),
            'context_text': r.get('context_text'),
            'result_type': 'verse',
            'lookup_ready': True,
            'rank': idx + 1
        })
    return normalized


def build_chapter_summary_results(raw: list, structure_level: str) -> list:
    """Map chapter-level raw rows into unified summary structure."""
    out = []
    for r in raw or []:
        if not isinstance(r, dict):
            continue
        out.append({
            'summary_id': r.get('summary_id'),
            'structure_level': structure_level,
            'primary_section': r.get('kanda') or r.get('parva') or r.get('skanda'),
            'subsection': r.get('sarga') or r.get('adhyaya'),
            'total_slokas': r.get('total_slokas'),
            'start_sloka_index': r.get('start_sloka_index'),
            'end_sloka_index': r.get('end_sloka_index'),
            'short_summary': r.get('short_summary'),
            'long_summary': r.get('long_summary'),
            'emotional_elements': r.get('emotional_elements'),
            'key_characters': r.get('key_characters'),
            'thematic_analysis': r.get('thematic_analysis'),
            'dharmic_insights': r.get('dharmic_insights'),
            'sanskrit_glossary': r.get('sanskrit_glossary'),
            'score': r.get('score'),
        })
    return out


def rerank_sloka_candidates(agent_en_sloka_list: list, agent_sa_sloka_list: list, agent_glossary_sloka_list: list, top_n: int, meaning_fetcher=None) -> list:
    """Merge and frequency-rerank sloka candidate lists from multiple semantic searches.
    Parameters:
        agent_en_sloka_list: results from english embedding search
        agent_sa_sloka_list: results from sanskrit embedding search
        agent_glossary_sloka_list: results from glossary/epithet embedding search
        top_n: limit for trimmed enriched list
        meaning_fetcher: optional callable (sloka_index, scripture_name)-> list[meaning dict]
    Returns:
        List of merged + enriched sloka dicts ordered by composite score.
    """
    sloka_frequency = {}
    sloka_details = {}
    sloka_sources = {}

    def ingest(items, label):
        for it in items or []:
            if not isinstance(it, dict):
                continue
            si = it.get('sloka_index')
            sc = it.get('scripture_name')
            if not si:
                continue
            key = f"{si}|{sc}"
            if key not in sloka_frequency:
                sloka_frequency[key] = 0
                sloka_sources[key] = []
                sloka_details[key] = {
                    'sloka_index': si,
                    'scripture_name': sc,
                    'context_text': it.get('context_text', '')
                }
            sloka_frequency[key] += 1
            sloka_sources[key].append(label)

    ingest(agent_en_sloka_list, 'english')
    ingest(agent_sa_sloka_list, 'sanskrit')
    ingest(agent_glossary_sloka_list, 'glossary')

    merged = []
    for k, freq in sloka_frequency.items():
        d = sloka_details[k]
        merged.append({
            'sloka_index': d['sloka_index'],
            'scripture_name': d['scripture_name'],
            'score': freq * 10,
            'frequency': freq,
            'contributing_agents': sloka_sources[k],
            'num_contributing_agents': len(sloka_sources[k]),
            'context_text': d.get('context_text', '')
        })
    merged.sort(key=lambda x: x['score'], reverse=True)
    trimmed = merged[:top_n]

    # Enrich with meanings if fetcher provided
    if meaning_fetcher:
        enriched = []
        for r in trimmed:
            try:
                full = meaning_fetcher(r['sloka_index'], r['scripture_name'])
                if full:
                    f = full[0]
                    r.update({
                        'input_sloka': f.get('input_sloka'),
                        'english_meaning': f.get('english_meaning'),
                        'anvaya_ordered': f.get('anvaya_ordered'),
                        'sanskrit_english_anvaya_combination': f.get('sanskrit_english_anvaya_combination'),
                        'narrator': f.get('narrator'),
                        'inferred_speaker_from_sloka': f.get('inferred_speaker_from_sloka'),
                        'entity_triplet_list': f.get('entity_triplet_list'),
                        'concept_triplet_list': f.get('concept_triplet_list'),
                    })
            except Exception as e:
                logger.warning(f"Meaning enrichment failed for {r.get('sloka_index')}:{r.get('scripture_name')} - {e}")
            enriched.append(r)
        return enriched
    return trimmed
