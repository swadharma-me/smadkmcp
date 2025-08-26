from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from typing import Annotated

# ---------- Common Constraints ----------
# Use Annotated[str, Field(...)] for constrained strings to appease linters/runtime
sloka_index = Annotated[str, Field(min_length=3, max_length=80)]
scripture_name = Annotated[str, Field(min_length=3, max_length=40)]
MAX_TOP_N = 50

# ---------- Input Models ----------
class SlokaSemanticSearchInput(BaseModel):
    text: Annotated[str, Field(min_length=3, max_length=2000)]
    top_n: int = Field(10, ge=1, le=MAX_TOP_N)
    scripture_list: Optional[List[scripture_name]] = None

class RerankInput(BaseModel):
    agent_en_sloka_list: Optional[List[dict]] = None
    agent_sa_sloka_list: Optional[List[dict]] = None
    agent_glossary_sloka_list: Optional[List[dict]] = None
    top_n: int = Field(10, ge=1, le=MAX_TOP_N)

class SurroundingContextInput(BaseModel):
    sloka_index: sloka_index
    scripture_name: Optional[scripture_name] = None

class GetSlokaMeaningInput(BaseModel):
    sloka_index: Optional[sloka_index] = None
    scripture_name: Optional[scripture_name] = None

class GetSlokaMeaningOutput(BaseModel):
    sloka_index: sloka_index
    scripture_name: scripture_name
    input_sloka: Optional[str] = None
    sanskrit_glossary: Optional[List[str]] = None
    sanskrit_english_anvaya_combination: Optional[str] = None
    english_meaning: Optional[str] = None
    bhashya_sloka_indexes: Optional[List[sloka_index]] = None

class ChapterSummarySearchInput(BaseModel):
    text: Annotated[str, Field(min_length=3, max_length=2000)]
    top_n: int = Field(5, ge=1, le=MAX_TOP_N)
    scripture_name: scripture_name

class TransliterateInput(BaseModel):
    sloka_text: Annotated[str, Field(min_length=1, max_length=4000)]
    target_script: str = Field("telugu")

# ---------- Output Models ----------
class SlokaSearchResult(BaseModel):
    sloka_index: sloka_index
    scripture_name: scripture_name
    score: float = Field(..., ge=0)
    context_text: Optional[str] = None
    result_type: Literal["Sloka"] = "Sloka"
    lookup_ready: Literal[True] = True
    rank: Optional[int] = None

class RerankResult(BaseModel):
    sloka_index: sloka_index
    scripture_name: scripture_name
    score: float
    frequency: int
    contributing_agents: List[str]
    num_contributing_agents: int
    context_text: Optional[str] = None
    input_sloka: Optional[str] = None
    english_meaning: Optional[str] = None
    anvaya_ordered: Optional[str] = None
    sanskrit_english_anvaya_combination: Optional[str] = None
    narrator: Optional[str] = None
    inferred_speaker_from_sloka: Optional[str] = None
    entity_triplet_list: Optional[List] = None
    concept_triplet_list: Optional[List] = None

class SurroundingContextOutput(BaseModel):
    sloka_index: sloka_index
    scripture_name: Optional[scripture_name]
    surrounding_context: str
    context_slokas_count: int

class ChapterSummaryResult(BaseModel):
    summary_id: Optional[str]
    structure_level: str
    primary_section: Optional[str]
    subsection: Optional[str]
    total_slokas: Optional[int]
    start_sloka_index: Optional[str]
    end_sloka_index: Optional[str]
    short_summary: Optional[str]
    long_summary: Optional[str]
    emotional_elements: Optional[str]
    key_characters: Optional[str]
    thematic_analysis: Optional[str]
    dharmic_insights: Optional[str]
    sanskrit_glossary: Optional[str]
    score: Optional[float]

class TransliterateOutput(BaseModel):
    original: str
    target_script: str
    transliterated: str
    success: bool
    message: Optional[str] = None
