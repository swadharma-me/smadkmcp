"""
MCP Tool for SanatanaSearch Postgres access, exposing data-fetching and embedding-matching functions as MCP tools with SSE endpoint support.
"""
import logging
from fastmcp import FastMCP
import app.utils.pgutils as pgutils
import app.utils.llmutils as llmutils
import app.utils.misctools as misctools
from app.utils.misctools import normalize_sloka_search_results, build_chapter_summary_results

from app.schemas.schema import (
    SlokaSemanticSearchInput, SlokaSearchResult,
    RerankInput, RerankResult,GetSlokaMeaningOutput,
    SurroundingContextInput, SurroundingContextOutput,
    ChapterSummarySearchInput, ChapterSummaryResult,
    TransliterateInput, TransliterateOutput,
    GetSlokaMeaningInput
)
from typing import List, Optional, Dict
import os

# Set up logger for this module
logger = logging.getLogger("mcptools")
logger.setLevel(logging.INFO)

# Add a handler if one doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

mcp_server = FastMCP()

# Helper to safely log outputs without flooding logs
_DEF_SAMPLE_LEN = 1

def _log_output(func_name: str, result):
    try:
        if isinstance(result, list):
            sample = result[:_DEF_SAMPLE_LEN]
            logger.info(f"{func_name} output: list len={len(result)} sample={sample}")
        elif isinstance(result, dict):
            logger.info(f"{func_name} output: dict keys={list(result.keys())}")
        else:
            logger.info(f"{func_name} output: type={type(result).__name__} value_snip={str(result)[:200]}")
    except Exception as e:
        logger.warning(f"{func_name} output logging failed: {e}")

@mcp_server.tool(description="Granularity: festival • Content: utsav metadata (name,type,tithi) • Intent: fetch festival info; optional filter via sloka_index.")
def fetch_utsav_records(sloka_index: str = None):
    logger.info(f"fetch_utsav_records called sloka_index={sloka_index}")
    results = pgutils.fetch_utsav_records(sloka_index)
    _log_output("fetch_utsav_records", results)
    return results


@mcp_server.tool(description="Granularity: corpus list • Content: scripture metadata (prefix, range) • Intent: discover valid scripture_name & sloka_index formats before other tools.")
def list_all_scriptures():
    logger.info("list_all_scriptures called")
    results = pgutils.list_all_scriptures()
    _log_output("list_all_scriptures", results)
    return results



@mcp_server.tool(
    name="get_sloka_meaning",
    description="Granularity: Sloka • Content: full meaning/sanskrit english combination of explanation/speakers/triplets • Intent: retrieve authoritative details for a known sloka_index. Note: verses mean slokas, commentaries usually mean bhashyas. Sanskrit version of the bhashyas are usually stored in input_sloka field.",
)
def get_sloka_meaning(sloka_index: str, scripture_name: str = None):
    logger.info(f"get_sloka_meaning called sloka_index={sloka_index} scripture_name={scripture_name}")
    results = pgutils.get_sloka_meanings(sloka_index, scripture_name)
    _log_output("get_sloka_meaning", results)
    return results


@mcp_server.tool(
    name="get_bhashya_references",
    description="Granularity: Commentary • Content: bhashya/commentary verse references • Intent: find commentary verses for a base sloka. Returns list of {scripture_name, sloka_index} for related bhashyas. Supports Gita (multiple bhashyas/commentaries) and Yogasutras (single bhashya/commentary)."
)
def get_bhashya_references(sloka_index: str, scripture_name: str):
    logger.info(f"get_bhashya_references called sloka_index={sloka_index} scripture_name={scripture_name}")
    results = pgutils.get_bhashya_references(sloka_index, scripture_name)
    _log_output("get_bhashya_references", results)
    return results


@mcp_server.tool(
    name="search_slokas_index_list_sanskrit_top_n",
    description="Granularity: Sloka • Content: Sanskrit embeddings • Intent: semantic match for Sanskrit phrasing / morphology queries. Returns top N slokas matching the input text. Use scripture_list parameter as list e.g. ['gita','ramayana','mahabharata','bhagavatham','yogasutras']. If scripture_list is None, searches all scriptures.",
)
def search_slokas_index_list_sanskrit_top_n(text: str, top_n: int = 10, scripture_list: Optional[List[str]] = None):
    logger.info(f"search_slokas_index_list_sanskrit_top_n called text='{text[:60]}...' top_n={top_n} scripture_list={scripture_list}")
    raw = pgutils.search_sloka_meaning_sa_embeddings_top_n(text, top_n=top_n, scripture_list=scripture_list)
    results = normalize_sloka_search_results(raw)
    _log_output("search_slokas_index_list_sanskrit_top_n", results)
    return results

@mcp_server.tool(
    name="search_slokas_index_list_english_top_n",
    description="Granularity: Sloka • Content: English meaning embeddings • Intent: semantic retrieval for natural-language English questions. Use scripture_list parameter as list e.g. ['gita','ramayana','mahabharata','bhagavatham','yogasutras']. If scripture_list is None, searches all scriptures."
)
def search_slokas_index_list_english_top_n(text: str, top_n: int = 10, scripture_list: Optional[List[str]] = None):
    logger.info(f"search_slokas_index_list_english_top_n called text='{text[:60]}...' top_n={top_n} scripture_list={scripture_list}")
    raw = pgutils.search_sloka_meaning_en_embeddings_top_n(text, top_n=top_n, scripture_list=scripture_list)
    results = normalize_sloka_search_results(raw)
    _log_output("search_slokas_index_list_english_top_n", results)
    return results

@mcp_server.tool(
    name="search_slokas_index_list_glossary_top_n",
    description="Granularity: Sloka • Content: glossary/epithet embeddings • Intent: find slokas by epithets / technical terms. Use scripture_list parameter as list e.g. ['gita','ramayana','mahabharata','bhagavatham','yogasutras']. If scripture_list is None, searches all scriptures."
)
def search_slokas_index_list_glossary_top_n(text: str, top_n: int = 10, scripture_list: Optional[List[str]] = None):
    logger.info(f"search_slokas_index_list_glossary_top_n called text='{text[:60]}...' top_n={top_n} scripture_list={scripture_list}")
    raw = pgutils.search_sloka_meaning_glossary_embeddings_top_n(text, top_n=top_n, scripture_list=scripture_list)
    results = normalize_sloka_search_results(raw)
    _log_output("search_slokas_index_list_glossary_top_n", results)
    return results


@mcp_server.tool(
    name="rerank_slokas",
    description="Granularity: Sloka set • Content: merged candidate lists • Intent: unify multi-agent results via frequency scoring + enrich."
)
def rerank_slokas(agent_en_sloka_list: Optional[List[dict]] = None, 
                  agent_sa_sloka_list: Optional[List[dict]] = None, 
                  agent_glossary_sloka_list: Optional[List[dict]] = None, 
                  top_n: int = 10):
    logger.info("rerank_slokas called")
    results = misctools.rerank_sloka_candidates(
        agent_en_sloka_list=agent_en_sloka_list or [],
        agent_sa_sloka_list=agent_sa_sloka_list or [],
        agent_glossary_sloka_list=agent_glossary_sloka_list or [],
        top_n=top_n,
        meaning_fetcher=pgutils.get_sloka_meanings
    )
    _log_output("rerank_slokas", results)
    return results

@mcp_server.tool(description="Granularity: window (N previous) • Content: prior Sloka texts • Intent: supply immediate lead-in context.")
def previous_sloka_details(sloka_index: str = None, scripture_name: str = None, number_before: int = 5):
    logger.info(f"previous_sloka_details called sloka_index={sloka_index} scripture_name={scripture_name} number_before={number_before}")
    results = pgutils.get_slokas_before_current_sloka(sloka_index, scripture_name, number_before=5)
    _log_output("previous_sloka_details", results)
    return results

@mcp_server.tool(description="Granularity: window (N next) • Content: following Sloka texts • Intent: supply immediate continuation context.")
def next_sloka_details(sloka_index: str = None, scripture_name: str = None, number_after: int = 5):
    logger.info(f"next_sloka_details called sloka_index={sloka_index} scripture_name={scripture_name} number_after={number_after}")
    results = pgutils.get_slokas_after_current_sloka(sloka_index, scripture_name, number_after=5)
    _log_output("next_sloka_details", results)
    return results


@mcp_server.tool(
    name="surrounding_context",
    description="Granularity: local passage (prev+current+next) • Content: LLM summary of contiguous slokas • Intent: narrative framing for a target Sloka."
)
def immediate_surrounding_context(sloka_index: str, scripture_name: str):
    """Return summary of immediate context (previous/current/next slokas) using trace_immediate_context.
    trace_immediate_context now supplies ordered list: prev (chronological), current, next.
    """
    logger.info(f"surrounding_context called sloka_index={sloka_index} scripture_name={scripture_name}")
    try:
        slokas = pgutils.trace_immediate_context(sloka_index, scripture_name) or []
    except Exception as e:
        logger.error(f"trace_immediate_context failed: {e}")
        slokas = []

    if not slokas:
        result = {
            'sloka_index': sloka_index,
            'scripture_name': scripture_name,
            'surrounding_context': 'No contextual slokas found.',
            'context_slokas_count': 0
        }
        _log_output("surrounding_context", result)
        return result

    try:
        summary = llmutils.generate_sloka_summary(slokas)
    except Exception as e:
        logger.error(f"generate_sloka_summary failed: {e}")
        summary = 'Context gathered but summary generation failed.'

    result = {
        'sloka_index': sloka_index,
        'scripture_name': scripture_name,
        'surrounding_context': summary,
        'context_slokas_count': len(slokas)
    }
    _log_output("surrounding_context", result)
    return result


@mcp_server.tool(description="Granularity: timestamp • Content: formatted date/time variants • Intent: supply temporal context or logging tags.")
def get_current_datetime():
    logger.info("get_current_datetime called")
    result = misctools.get_current_datetime_formatted()
    _log_output("get_current_datetime", result)
    return result


@mcp_server.tool(
    name="search_ramayana_sarga_summaries",
    description="Granularity: chapter • Content: Ramayana narrative/thematic summary embeddings • Intent: macro context (no sloka_index). Uses scripture_name parameter for 'ramayana'."
)
def search_ramayana_sarga_summaries(text: str, top_n: int = 5, scripture_name: str = "ramayana"):
    logger.info(f"search_ramayana_sarga_summaries called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    raw = pgutils.search_ramayana_sarga_summary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    results = build_chapter_summary_results(raw, 'sarga')
    _log_output("search_ramayana_sarga_summaries", results)
    return results

@mcp_server.tool(
    name="search_ramayana_chapter_glossary_terms",
    description="Granularity: chapter (sarga) • Content: terminology/epithet glossary embedding • Intent: locate Ramayana sargas via Sanskrit terms. (No sloka_index in results.) Uses scripture_name parameter for 'ramayana'."
)
def search_ramayana_chapter_glossary_terms(text: str, top_n: int = 5, scripture_name: str = "ramayana"):
    logger.info(f"search_ramayana_chapter_glossary_terms called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    results = pgutils.search_ramayana_sarga_glossary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    _log_output("search_ramayana_chapter_glossary_terms", results)
    return results

@mcp_server.tool(
    name="search_mahabharata_adhyaya_summaries",
    description="Granularity: chapter • Content: Mahabharata narrative/thematic summary embeddings • Intent: complex episode / plot context (no sloka_index). Uses scripture_name parameter for 'mahabharata'."
)
def search_mahabharata_adhyaya_summaries(text: str, top_n: int = 5, scripture_name: str = "mahabharata"):
    logger.info(f"search_mahabharata_adhyaya_summaries called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    raw = pgutils.search_mahabharata_adhyaya_summary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    results = build_chapter_summary_results(raw, 'adhyaya')
    _log_output("search_mahabharata_adhyaya_summaries", results)
    return results

@mcp_server.tool(
    name="search_mahabharata_chapter_glossary_terms",
    description="Granularity: chapter (adhyaya) • Content: terminology/epithet glossary embedding • Intent: locate Mahabharata adhyayas via Sanskrit terms. (No sloka_index in results.) Uses scripture_name parameter for 'mahabharata'."
)
def search_mahabharata_chapter_glossary_terms(text: str, top_n: int = 5, scripture_name: str = "mahabharata"):
    logger.info(f"search_mahabharata_chapter_glossary_terms called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    results = pgutils.search_mahabharata_glossary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    _log_output("search_mahabharata_chapter_glossary_terms", results)
    return results

@mcp_server.tool(
    name="search_bhagavatham_adhyaya_summaries",
    description="Granularity: chapter • Content: Bhagavatham narrative/thematic summary embeddings • Intent: bhakti/lila macro context (no sloka_index). Uses scripture_name parameter for 'bhagavatham'."
)
def search_bhagavatham_adhyaya_summaries(text: str, top_n: int = 5, scripture_name: str = "bhagavatham"):
    logger.info(f"search_bhagavatham_adhyaya_summaries called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    raw = pgutils.search_bhagavatham_adhyaya_summary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    results = build_chapter_summary_results(raw, 'adhyaya')
    _log_output("search_bhagavatham_adhyaya_summaries", results)
    return results

@mcp_server.tool(
    name="search_bhagavatham_chapter_glossary_terms",
    description="Granularity: chapter (adhyaya) • Content: devotional/theological glossary embedding • Intent: locate Bhagavatham adhyayas via divine names/concepts. (No sloka_index in results.) Uses scripture_name parameter for 'bhagavatham'."
)
def search_bhagavatham_chapter_glossary_terms(text: str, top_n: int = 5, scripture_name: str = "bhagavatham"):
    logger.info(f"search_bhagavatham_chapter_glossary_terms called text='{text[:60]}...' top_n={top_n} scripture_name={scripture_name}")
    results = pgutils.search_bhagavatham_glossary_embeddings_top_n(text, top_n=top_n, scripture_name=scripture_name)
    _log_output("search_bhagavatham_chapter_glossary_terms", results)
    return results

@mcp_server.tool(
    name="get_chapter_context",
    description="Granularity: chapter • Content: narrative/thematic/glossary summary row(s) for the chapter containing the sloka_index • Intent: supply macro context for a specific Sloka."
)
def get_chapter_context(sloka_index: str, scripture_name: str):
    """Return chapter-level context (summary, themes, glossary) for the chapter containing the given sloka.
    Wraps pgutils.trace_back_chapter_context.
    """
    logger.info(f"get_chapter_context called sloka_index={sloka_index} scripture_name={scripture_name}")
    try:
        rows = pgutils.trace_back_chapter_context(sloka_index, scripture_name) or []
        _log_output("get_chapter_context", rows)
        return rows
    except Exception as e:
        logger.error(f"get_chapter_context failed: {e}")
        return []

def run_server():
    """Run the MCP server (SSE) using optional environment overrides.
    Environment variables:
        SANATANA_MCP_HOST (default 0.0.0.0)
        SANATANA_MCP_PORT (default 8002)
        SANATANA_MCP_PATH (default /sse)
        SANATANA_MCP_LOG_LEVEL (default debug)
    """
    host = os.environ.get('SANATANA_MCP_HOST', '0.0.0.0')
    port = int(os.environ.get('SANATANA_MCP_PORT', '8002'))
    path = os.environ.get('SANATANA_MCP_PATH', '/sse')
    log_level = os.environ.get('SANATANA_MCP_LOG_LEVEL', 'debug')
    logger.info(f"Starting MCP server host={host} port={port} path={path} log_level={log_level}")
    mcp_server.run(
        transport="sse",
        path=path,
        host=host,
        port=port,
        log_level=log_level
    )


# Expose FastMCP instance as ASGI app for uvicorn
app = mcp_server.sse_app  # Uvicorn-compatible ASGI app for SSE

if __name__ == "__main__":
    import os  # ensure os is available even if trimmed above
    run_server()
