
from typing import Optional, List, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class Utsav(BaseModel):
    utsav_name: str
    utsav_type: str
    alternate_names: str
    maasa_num: int
    maasa: str
    thithi_num: int
    thithi: str
    description: str
    created_by: str
    modified_by: Optional[str]
# Yogasutras schema (get only, no id, no audit fields)
class Yogasutras(BaseModel):
    sloka_index: Optional[str]
    adhyaya: Optional[str]
    sloka_num: Optional[str]
    sloka_text: Optional[str]
# Ramayana schema (get only, no id, no audit fields)
class Ramayana(BaseModel):
    sloka_index: Optional[str]
    kanda: Optional[str]
    sarga: Optional[str]
    sloka_num: Optional[str]
    kanda_name: Optional[str]
    sloka_text: Optional[str]
# Mahabharata schema (get only, no id, no audit fields)
class Mahabharata(BaseModel):
    parva: Optional[str]
    adhyaya: Optional[str]
    sloka_num: Optional[str]
    parva_name: Optional[str]
    sloka_index: Optional[str]
    sloka_text: Optional[str]



# Wrapper class for triplet lists
class TripletList(BaseModel):
    triples: Optional[List[dict]]

from typing import Union

class SlokaMeta(BaseModel):
    sloka_index: Optional[str]  # Accepts string IDs like 'KRISHNA_BG_01_31'
    scripture_name: Optional[str]
    input_sloka: Optional[str]
    sandhi_vicheda: Optional[Union[str, List[str]]]  # Accepts string or list
    output_sloka: Optional[str]
    anvaya_ordered: Optional[Union[str, List[str]]]  # Accepts string or list
    sanskrit_english_anvaya_combination: Optional[str]
    english_meaning: Optional[str]
    narrator: Optional[str]
    inferred_speaker_from_sloka: Optional[str]
    inferred_speaker_from_prev_sloka: Optional[str]
    inferred_speaker_from_other_sources: Optional[str]
    # TripletList expects a dict, not a JSON string. Parse if needed in fetch method.
    entity_triplet_list: Optional[TripletList]
    concept_triplet_list: Optional[TripletList]

class Gita(BaseModel):
    parva: Optional[str]
    adhyaya: Optional[str]
    sloka_num: Optional[str]
    parva_name: Optional[str]
    sloka_index: Optional[str]
    sloka_text: Optional[str]
    original_adhyaya: Optional[int]

class Bhagavatham(BaseModel):
    id: UUID
    sloka_index: Optional[str]
    skanda: Optional[str]
    adhyaya: Optional[str]
    sloka_num: Optional[str]
    skanda_name: Optional[str]
    sloka_text: Optional[str]


# Scriptures schema (get only, no id, no audit fields)
class Scriptures(BaseModel):

    scripture_name: Optional[str]
    author: Optional[str]
    description: Optional[str]
    summary: Optional[str]
    publication_year: Optional[int]
    language: Optional[str]
    genre: Optional[str]
    target_table_name: Optional[str]

# Nuggets schema
class Nuggets(BaseModel):
    sloka_index: str
    scripture_name: str
    nugget: str
    explanation: str
    nugget_type: str
    confidence_score: float
    sanskrit_english_word_reference: List[str]

# Rasa schema
class Rasa(BaseModel):
    sloka_index: str
    scripture_name: str
    rasa_type: str
    chandas_type: str
    rasa_targets:  Optional[List[str]]
    alankara_type: Optional[str]
    confidence_score: float
    rasa_description: str
    rasa_experienced: Optional[List[str]]
    presentation_form: str
    rasa_presented_in_sloka: str
    author_intent_explanation: str
    sanskrit_english_word_reference: List[str]

# Marga schema
class Marga(BaseModel):
    sloka_index: str
    scripture_name: str
    yoga_marga_path: Optional[str]
    yoga_marga_limb: Optional[str]
    yoga_marga_samadhi_stage: Optional[str]
    yoga_marga_citta_state: Optional[str]
    yoga_marga_characters_involved: Optional[List[str]]
    yoga_marga_author_intent: Optional[str]
    yoga_marga_dharma_alignment: Optional[str]
    yoga_marga_adhikara_jati: Optional[str]
    yoga_marga_adhikara_varna: Optional[str]
    yoga_marga_adhikara_ashrama: Optional[str]
    yoga_marga_adhikara_stage_of_eligibility: Optional[str]
    jnana_marga_approach: Optional[str]
    jnana_marga_motivation: Optional[str]
    jnana_marga_realization_relation: Optional[str]
    jnana_marga_stage: Optional[str]
    jnana_marga_guna: Optional[str]
    jnana_marga_characters_involved:  Optional[List[str]]
    jnana_marga_author_intent: Optional[str]
    jnana_marga_dharma_alignment: Optional[str]
    jnana_marga_adhikara_jati: Optional[str]
    jnana_marga_adhikara_varna: Optional[str]
    jnana_marga_adhikara_ashrama: Optional[str]
    jnana_marga_adhikara_stage_of_eligibility: Optional[str]
    karma_marga_orientation: Optional[str]
    karma_marga_motivation: Optional[str]
    karma_marga_phala_relation: Optional[str]
    karma_marga_stage: Optional[str]
    karma_marga_guna: Optional[str]
    karma_marga_characters_involved:  Optional[List[str]]
    karma_marga_author_intent: Optional[str]
    karma_marga_dharma_alignment: Optional[str]
    karma_marga_adhikara_jati: Optional[str]
    karma_marga_adhikara_varna: Optional[str]
    karma_marga_adhikara_ashrama: Optional[str]
    karma_marga_adhikara_stage_of_eligibility: Optional[str]
    bhakti_marga_mode: Optional[str]
    bhakti_marga_bhava: Optional[str]
    bhakti_marga_stage: Optional[str]
    bhakti_marga_lakshana: Optional[str]
    bhakti_marga_characters_involved:  Optional[List[str]]
    bhakti_marga_author_intent: Optional[str]
    bhakti_marga_dharma_alignment: Optional[str]
    bhakti_marga_adhikara_jati: Optional[str]
    bhakti_marga_adhikara_varna: Optional[str]
    bhakti_marga_adhikara_ashrama: Optional[str]
    bhakti_marga_adhikara_stage_of_eligibility: Optional[str]
    assessment_accuracy_karma_marga: Optional[float]
    assessment_accuracy_jnana_marga: Optional[float]
    assessment_accuracy_bhakti_marga: Optional[float]
    assessment_accuracy_yoga_marga: Optional[float]
    assessment_analysis: Optional[str]
    character_involved:  Optional[List[str]]
