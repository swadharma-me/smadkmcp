from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

from sqlalchemy import Float    


# 1. Paths
class YogaPath(str, Enum):
    raja = "राजयोग"
    karma = "कर्मयोग"
    bhakti = "भक्तियोग"
    jnana = "ज्ञानयोग"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths
#
# 8. Adhikara Bheda (Eligibility)
class Jati(str, Enum):
    brahmin = "ब्राह्मण"          # Priestly lineage
    kshatriya = "क्षत्रिय"        # Warrior or ruling lineage
    vaishya = "वैश्य"            # Merchant or agricultural lineage
    shudra = "शूद्र"             # Service-oriented lineage
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class Varna(str, Enum):
    brahmin = "ब्राह्मण"          # Scholarly/priestly duties
    kshatriya = "क्षत्रिय"        # Governance/protection duties
    vaishya = "वैश्य"            # Commerce/agriculture duties
    shudra = "शूद्र"             # Service/support duties
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class Ashrama(str, Enum):
    brahmachari = "ब्रह्मचारी"    # Student stage, focused on learning
    grihastha = "गृहस्थ"         # Householder stage, worldly duties
    vanaprastha = "वानप्रस्थ"     # Hermit stage, spiritual pursuits
    sannyasi = "सन्यासी"          # Renunciate stage, liberation-focused
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class StageOfCompetency(str, Enum):
    novice = "नवसिख"            # Beginner, basic eligibility
    intermediate = "मध्यवर्ती"    # Moderate skill, partial qualifications (e.g., basic yoga)
    advanced = "उन्नत"           # Advanced competency (e.g., ahimsa for higher yoga)
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths


# 5. Guna Classification
class Guna(str, Enum):
    sattvik = "सात्त्विक"        # Pure, clear, aligned with truth
    rajasik = "राजसिक"         # Passion-driven, seeking intellectual prestige
    tamasik = "तामसिक"         # Ignorant, misaligned with truth
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class AdhikaraBheda(BaseModel):
    jati: Jati = Field(..., description="Birth-based lineage, per Dharma Shastras.")
    varna: Varna = Field(..., description="Social function, per Gita 3.35.")
    ashrama: Ashrama = Field(..., description="Life stage, per Manusmriti.")
    stage_of_eligibility: StageOfCompetency = Field(..., description="Spiritual competency. Bhakti is for everyone, Karma is skewed towards jati-varna-ashrama, Jnana is for those with self-awareness-knowledge, Raja Yoga is for those with advanced competency in skils in self-control.")
# 6. Author Intent
class AuthorIntent(str, Enum):
    teaching = "शिक्षण"           # Conveying moral/spiritual lessons
    narrative = "कथन"            # Advancing a story or epic
    devotional = "भक्ति"          # Inspiring devotion
    philosophical = "दर्शन"       # Exploring metaphysical concepts
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 7. Dharma Alignment
class DharmaAlignment(str, Enum):
    within_boundaries_of_dharma = "धर्म"  # Righteous, aligned with cosmic order
    adharma = "अधर्म"                    # Unrighteous, disruptive to cosmic order
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths


# Bhakti Profile Model
class BhaktiMode(str, Enum):
    shravana = "श्रवण"
    kirtana = "कीर्तन"
    smarana = "स्मरण"
    padasevana = "पादसेवन"
    archana = "अर्चन"
    vandana = "वन्दन"
    dasya = "दास्य"
    sakhya = "सख्य"
    atmanivedana = "आत्मनिवेदन"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class BhaktiBhava(str, Enum):
    shanta = "शान्त"
    dasya = "दास्य"
    sakhya = "सख्य"
    vatsalya = "वात्सल्य"
    madhurya = "माधुर्य"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class BhaktiStage(str, Enum):
    sadhana = "साधना"
    bhava = "भाव"
    prema = "प्रेम"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class BhaktiLakshana(str, Enum):
    avirata = "अविरत"
    ananya = "अनन्य"
    nirmama = "निर्मम"
    ahaituki = "अहेतुक"
    anukampamayi = "अनुकम्पामयी"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class BhaktiProfile(BaseModel):
    mode: BhaktiMode = Field(
        ...,
        description="Mode of Bhakti (e.g., Navadha Bhakti: shravana, kirtana, smarana, etc. See Bhagavata Purana, Narada Bhakti Sutra)."
    )
    bhava: BhaktiBhava = Field(
        ...,
        description="Emotional flavor (Bhava/Rasa) as per Bhakti traditions: shanta, dasya, sakhya, vatsalya, madhurya."
    )
    stage: BhaktiStage = Field(
        ...,
        description="Stage or intensity of Bhakti: sadhana (practice), bhava (emotion), prema (divine love)."
    )
    lakshana: BhaktiLakshana = Field(
        ...,
        description="Key qualities of Bhakti as per Narada Bhakti Sutra: avirata (uninterrupted), ananya (exclusive), nirmama (selfless), ahaituki (unmotivated), anukampamayi (compassionate)."
    )
    characters_involved: List[str] = Field(
        ...,
        description="Characters expressing or affected by Bhakti in the sloka or narrative (e.g., Meera, Hanuman, Arjuna)."
    )
    author_intent: AuthorIntent = Field(
        ...,
        description="Author’s purpose in sloka/text: teaching, narrative, devotional, or philosophical."
    )
    dharma_alignment: DharmaAlignment = Field(
        ...,
        description="Alignment with cosmic order, per Bhakti texts and Gita. Options: within_boundaries_of_dharma (righteous) or adharma (disruptive)."
    )
    adhikara: AdhikaraBheda = Field(
        ...,
        description="Eligibility for Bhakti, based on jati (lineage), varna (social function), ashrama (life stage), and stage_of_eligibility (spiritual/skill competency)."
    )




# 2. Eight Limbs
class AshtangaLimb(str, Enum):
    yama = "यम"
    niyama = "नियम"
    asana = "आसन"
    pranayama = "प्राणायाम"
    pratyahara = "प्रत्याहार"
    dharana = "धारणा"
    dhyana = "ध्यान"
    samadhi = "समाधि"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 3. Stages of Samadhi
class SamadhiStage(str, Enum):
    savitarka = "सवितर्क"
    nirvitarka = "निर्वितर्क"
    savichara = "सविचार"
    nirvichara = "निर्विचार"
    sasmita = "सस्मित"
    nirbija = "निर्बीज"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 4. Citta States
class CittaBhumi(str, Enum):
    kshipta = "क्षिप्त"
    mudha = "मूढ"
    vikshipta = "विक्षिप्त"
    ekagra = "एकाग्र"
    nirodha = "निरोध"
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

class YogaProfile(BaseModel):
    path: YogaPath = Field(
        ...,
        description="Type of Yoga path (e.g., raja, karma, bhakti, jnana) as per Yoga Sutras and Bhagavad Gita."
    )
    limb: AshtangaLimb = Field(
        ...,
        description="Ashtanga Yoga limb (yama, niyama, asana, pranayama, pratyahara, dharana, dhyana, samadhi) as per Patanjali's Yoga Sutras."
    )
    samadhi_stage: SamadhiStage = Field(
        ...,
        description="Stage of Samadhi (savitarka, nirvitarka, savichara, nirvichara, sasmita, nirbija) as per Yoga Sutras 1.17-1.18."
    )
    citta_state: CittaBhumi = Field(
        ...,
        description="State of the mind-field (kshipta, mudha, vikshipta, ekagra, nirodha) as per Yoga Sutras 1.1-1.5."
    )
    characters_involved: List[str] = Field(
        ...,
        description="Characters practicing or exemplifying Yoga in the sloka or narrative (e.g., Patanjali, Arjuna, Krishna)."
    )
    author_intent: AuthorIntent = Field(
        ...,
        description="Author’s purpose in sloka/text: teaching, narrative, devotional, or philosophical."
    )
    dharma_alignment: DharmaAlignment = Field(
        ...,
        description="Alignment with cosmic order, per Yoga texts and Gita. Options: within_boundaries_of_dharma (righteous) or adharma (disruptive)."
    )
    adhikara: AdhikaraBheda = Field(
        ...,
        description="Eligibility for Yoga, based on jati (lineage), varna (social function), ashrama (life stage), and stage_of_eligibility (spiritual/skill competency)."
    )


# 1. Orientation
class KarmaOrientation(str, Enum):
    nishkama = "निष्कामकर्म"      # Selfless action, no attachment to outcomes
    sakama = "सकामकर्म"          # Desire-driven action, motivated by personal gain
    yajna = "यज्ञकर्म"            # Sacrificial action, dedicated to cosmic order
    svadharma = "स्वधर्मकर्म"      # Duty-based action, aligned with one's role
    akarma = "अकर्म"             # Non-binding action, producing no karmic residue
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 2. Motivation
class KarmaMotivation(str, Enum):
    mumukshu = "मुमुक्षु"          # Seeking liberation from samsara
    bhogi = "भोगी"               # Pursuing material or sensory pleasures
    lokasangrahi = "लोकसंग्रही"    # Acting for societal welfare
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 3. Phala Orientation
class KarmaPhalaRelation(str, Enum):
    tyagi = "त्यागी"              # Renounces all fruits of action
    upabhokta = "उपभोक्ता"        # Enjoys or accepts fruits of action
    arpanabhava = "अर्पणभाव"       # Offers fruits to divine (includes prasada-buddhi)
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 4. Karma Stage
class KarmaStage(str, Enum):
    sanchita = "संचित"            # Accumulated karmas from past lives
    prarabdha = "प्रारब्ध"         # Karmas currently fructifying
    agami = "आगामि"              # New karmas being generated
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 5. Guna Classification
class KarmaGuna(str, Enum):
    sattvik = "सात्त्विक"         # Pure, selfless, aligned with dharma
    rajasik = "राजसिक"           # Passionate, ego-driven, seeking reward
    tamasik = "तामसिक"           # Ignorant, harmful, disregarding consequences
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths


# Karma Profile Model
class KarmaProfile(BaseModel):
    orientation: KarmaOrientation = Field(
        ...,
        description="Mode of karma performance, per Bhagavad Gita (Ch. 3, 4.18). Includes selfless (nishkama), desire-driven (sakama), sacrificial (yajna), duty-based (svadharma), or non-binding (akarma)."
    )
    motivation: KarmaMotivation = Field(
        ...,
        description="Driving purpose, rooted in Purusharthas. Options: liberation-seeking (mumukshu), material-seeking (bhogi), or social-welfare oriented (lokasangrahi, Gita 3.20)."
    )
    phala_relation: KarmaPhalaRelation = Field(
        ...,
        description="Relationship to outcomes, per Jnana/Bhakti traditions. Includes renouncing results (tyagi, Gita 4.20), enjoying results (upabhokta), or offering results to divine (arpanabhava, Gita 9.27, includes prasada-buddhi)."
    )
    stage: KarmaStage = Field(
        ...,
        description="Temporal stage in karma cycle, per Vedanta. Includes accumulated (sanchita), currently fructifying (prarabdha), or newly generated (agami) karmas."
    )
    guna: KarmaGuna = Field(
        ...,
        description="Qualitative nature, per Gita (Ch. 18, Shlokas 23-25). Options: pure/selfless (sattvik), passionate/ego-driven (rajasik), or ignorant/harmful (tamasik)."
    )
    characters_involved: List[str] = Field(
        ...,
        description="Characters performing/affected by karma in a sloka or narrative (e.g., Arjuna in Gita)."
    )
    author_intent: AuthorIntent = Field(
        ...,
        description="Author’s purpose in sloka/text: teaching, narrative, devotional, or philosophical."
    )
    dharma_alignment: DharmaAlignment = Field(
        ...,
        description="Alignment with cosmic order, per Gita and Manusmriti. Options: within_boundaries_of_dharma (righteous) or adharma (disruptive)."
    )
    adhikara: AdhikaraBheda = Field(
        ...,
        description="Eligibility for karma, based on jati (lineage), varna (social function), ashrama (life stage), and stage_of_skill (spiritual/skill competency, e.g., ahimsa for yoga, Gita 3.35, Yoga Sutras)."
    )

## Jnana marga 



# 1. Approach
class JnanaApproach(str, Enum):
    shravana = "श्रवण"          # Listening to scriptures (e.g., Upanishads, Gita)
    manana = "मनन"            # Reflection on teachings for intellectual clarity
    nididhyasana = "निदिध्यासन" # Deep contemplation/meditation for realization
    atma_vichara = "आत्मविचार"  # Self-inquiry (e.g., Ramana Maharshi’s “Who am I?”)
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 2. Motivation
class JnanaMotivation(str, Enum):
    mumukshutva = "मुमुक्षुत्व"   # Intense desire for liberation (moksha)
    jijnasa = "जिज्ञासा"        # Curiosity for metaphysical truth
    sadhana = "साधना"          # Disciplined practice for self-realization
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 3. Realization Relation
class RealizationRelation(str, Enum):
    viveki = "विवेकी"           # Discriminating self from non-self (Atman vs. body/mind)
    vairagi = "वैरागी"          # Detached from worldly attachments
    samarpita = "समर्पित"       # Surrendered to Brahman or divine truth
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths

# 4. Jnana Stage
class JnanaStage(str, Enum):
    avidya = "अविद्या"          # Ignorance, pre-knowledge state
    sadhana = "साधना"          # Active pursuit of knowledge
    jnana_prapti = "ज्ञानप्राप्ति" # Attainment of self-realization
    jivanmukta = "जीवन्मुक्त"    # Liberated while living
    not_mentioned_in_text = "not_mentioned_in_text"  # Placeholder for undefined paths




# Jnana Profile Model
class JnanaProfile(BaseModel):
    approach: JnanaApproach = Field(
        ...,
        description="Method of pursuing Jnana Marga, per Upanishads and Gita (Ch. 2, 4). Includes listening to scriptures (shravana), reflection (manana), contemplation (nididhyasana), or self-inquiry (atma_vichara)."
    )
    motivation: JnanaMotivation = Field(
        ...,
        description="Driving intent for Jnana pursuit, rooted in Vedantic goals. Options: intense desire for liberation (mumukshutva), curiosity for truth (jijnasa), or disciplined practice (sadhana)."
    )
    realization_relation: RealizationRelation = Field(
        ...,
        description="Relation to spiritual outcome, per Vedanta. Includes discriminating self from non-self (viveki), detachment (vairagi), or surrender to Brahman (samarpita)."
    )
    stage: JnanaStage = Field(
        ...,
        description="Progress in Jnana Marga, per Upanishads. Includes ignorance (avidya), active pursuit (sadhana), realization (jnana_prapti), or liberation while living (jivanmukta)."
    )
    guna: Guna = Field(
        ...,
        description="Qualitative nature, per Gita (Ch. 18, Shlokas 20-22). Options: pure/clear (sattvik), prestige-seeking (rajasik), or ignorant (tamasik)."
    )
    characters_involved: List[str] = Field(
        ...,
        description="Characters pursuing/affected by Jnana in a sloka or narrative (e.g., Arjuna in Gita)."
    )
    author_intent: AuthorIntent = Field(
        ...,
        description="Author’s purpose in sloka/text: teaching, narrative, devotional, or philosophical."
    )
    dharma_alignment: DharmaAlignment = Field(
        ...,
        description="Alignment with cosmic order, per Gita and Manusmriti. Options: within_boundaries_of_dharma (righteous) or adharma (disruptive)."
    )
    adhikara: AdhikaraBheda = Field(
        ...,
        description="Eligibility for Jnana Marga, based on jati (lineage), varna (social function), ashrama (life stage), and stage_of_skill (spiritual competency, e.g., viveka, Upanishads)."
    )


# Assuming KarmaProfile, JnanaProfile, BhaktiProfile, YogaProfile already exist in dharma.py
class SlokaPhilosophicalOrientation(BaseModel):
    karma_marga: Optional["KarmaProfile"] = Field(None, description="Karma Marga profile for the sloka")
    assessment_accuracy_karma_marga: Optional[float] = Field(None, description="Confidence score for Karma Marga alignment (0–1). 1 best, 0 worst")

    jnana_marga: Optional["JnanaProfile"] = Field(None, description="Jnana Marga profile for the sloka")
    assessment_accuracy_jnana_marga: Optional[float] = Field(None, description="Confidence score for Jnana Marga alignment (0–1). 1 best, 0 worst")

    bhakti_marga: Optional["BhaktiProfile"] = Field(None, description="Bhakti Marga profile for the sloka")
    assessment_accuracy_bhakti_marga: Optional[float] = Field(None, description="Confidence score for Bhakti Marga alignment (0–1). 1 best, 0 worst")

    yoga_marga: Optional["YogaProfile"] = Field(None, description="Yoga Marga profile for the sloka")
    assessment_accuracy_yoga_marga: Optional[float] = Field(None, description="Confidence score for Yoga Marga alignment (0–1). 1 best, 0 worst")
    assessment_analysis: Optional[str] = Field(None, description="Analysis of the philosophical orientation assessment, including reasoning and confidence levels.")
    character_involved: List[str] = Field(None, description="List of characters involved in the sloka or narrative, relevant to the philosophical orientation.")

class NodeGroups(str, Enum):
    person = "person"
    devatas = "devatas"
    place = "place"
    event = "event"
    time = "time"
    dharma_places = "dharma_places"
    directions = "directions"
    shastras = "shastras"
    titles = "titles"
    jati_varna_ashrama = "jati_varna_ashrama"
    jyotisha = "jyotisha"
    dharma_life_events = "dharma_life_events"
    lokas = "lokas"
    dharma_concepts = "dharma_concepts"
    darshanas = "darshanas"
    pashu = "pashu"
    aushada = "aushada"
    indriyas = "indriyas"
    ayurveda = "ayurveda"
    miscellaneous = "miscellaneous"

# Forward references for self-referencing types
class StateOfMind(str, Enum):
    nirashih = "निराशीः"  
    # Desireless (freedom from expectation) — acting without attachment to outcomes, aligning with Gītā 2.47: "कर्मण्येवाधिकारस्ते…".  
    # It represents the Karma Yogī's mental discipline: perform action as duty, not for results.

    udasinah = "उदासीनः"  
    # Detached (indifference, equanimity) — "standing apart" without emotional agitation in dualities (BG 6.9).  
    # Root of true equanimity (समत्वम्), seeing friends and enemies alike.

    vyavasayah = "व्यवसायः"  
    # Determined (firm resolve) — One-pointed pursuit of dharma (BG 2.41: "व्यवसायात्मिका बुद्धिः").  
    # A Yogī’s unwavering commitment to the chosen path (mārga).

    bhaktiman = "भक्तिमान्"  
    # Devoted (possessing bhakti) — Loving surrender to Īśvara (BG 12.17).  
    # This is *Ananya-bhakti* (exclusive devotion), transcending ritual and intellectual dharma.

    dhrityutsahasamanvitah = "धृत्युत्साहसमन्वितः"  
    # Endowed with steadfastness & enthusiasm — Combining **dhṛti** (mental firmness) with **utsāha** (joyful energy).  
    # Seen in the Kṣatriya dharma: acting with vigor and resolve even in adversity.

    samabuddhih = "समबुद्धिः"  
    # Equal-mindedness (balanced intellect) — Treating pleasure/pain, gain/loss as equal (BG 5.18).  
    # A Jñāna-Yogī’s sign: seeing Brahman in all beings equally.

    samah = "समः"  
    # Equipoised — A settled mental disposition, free from likes/dislikes.  
    # Synonymous with **samatvaṁ**, a central Gītā teaching (BG 2.48).

    nityah = "नित्यः"  
    # Eternal (steadfast / enduring state) — Steadfast in Self, unaffected by impermanence.  
    # Implies identity with the ātman, which is nitya (eternal).

    nityasya = "नित्यस्य"  
    # Eternal (steadfast / enduring) — Variant form; often used to emphasize permanence of Self or dharmic principles.

    nityajatam = "नित्यजातम्"  
    # Eternally born — A philosophical insight: viewing birth-death as eternal, aligning with BG 2.20’s teaching of the unborn Self.

    samachittatvam = "समचित्तत्वम्"  
    # Evenness of mind — Mastering rajas/tamas, staying sattvic in all conditions.  
    # A yogic ideal: **उदासीनवदासीनः** (acting as a neutral witness).

    shraddhavan = "श्रद्धावान्"  
    # Faithful — Possessing **śraddhā**, an essential precondition for Jñāna (BG 4.39).  
    # Not blind belief, but reverent trust in Śāstra and Guru.

    muktasangah = "मुक्तसङ्गः"  
    # Free from attachment — Detached from karma-phala (fruits), aligning with **Sāṅkhya** and **Karma Yoga**.  
    # A liberated actor, untouched by bondage.

    vitaragabhayakrodhah = "वीतरागभयक्रोधः"  
    # Free from attachment, fear, and anger — Triple freedom: overcoming raga (attachment), bhaya (fear), and krodha (anger).  
    # Bhagavān’s qualities in BG 2.56; essential for a sthitaprajña.

    vimatsarah = "विमत्सरः"  
    # Free from envy — Pure-hearted, devoid of jealousy.  
    # Found in BG 12.13: **अद्वेष्टा सर्वभूतानां…**.

    sukheshu_vigatasprihah = "सुखेषु विगतस्पृहः"  
    # Free from longing in pleasures — Transcending hedonic craving.  
    # Sign of true **vairāgya**: enjoying without clinging.

    gatavyathah = "गतव्यथः"  
    # Freedom from sorrow — Inner composure, not shaken by suffering.  
    # Reflects Gītā’s teaching on transcending duḥkha (BG 6.23).

    krtakrityah = "कृतकृत्यः"  
    # Fulfilled his duties — Having accomplished what is to be done; aligns with **niṣkāma karma**.  
    # A sense of dharmic completion.

    danam = "दानम्"  
    # Generosity — Selfless giving, a yajñic act.  
    # In dharma-śāstra: divided as **sāttvika, rājasa, tāmasa** (BG 17.20–22).

    mardavam = "मार्दवं"  
    # Gentleness — Softness in speech, demeanor; opposite of harshness.  
    # Part of **Daivi-sampat** (divine qualities, BG 16.2).

    dhrtih = "धृतिः"  
    # Fortitude — Unshakable perseverance under suffering.  
    # BG 18.33: **सत्त्वेन धार्यते यत्र…**.

    kshantih = "क्षान्तिः"  
    # Forbearance — Bearing insult/injury without retaliation.  
    # A key quality of a Brāhmaṇa (BG 18.42).

    kshama = "क्षमा"  
    # Forgiveness — Deep compassion and letting go of injury.  
    # A yogic virtue also praised in Manusmṛti as essential for harmony.

    abhayam = "अभयम्"  
    # Fearlessness — Freedom from existential and situational fear (BG 16.1).  
    # Rooted in knowledge of ātman and surrender to Bhagavān.

    ahimsa = "अहिंसा"  
    # Non-violence — Compassion in thought, word, deed.  
    # In Sanātana Dharma: not mere pacifism, but **non-harm aligned with dharma** (BG 13.7). It balances ahiṁsā with righteous action (like Kṛṣṇa advising Arjuna to fight when dharma calls).


from pydantic import BaseModel, Field
from typing import List, Optional

class CanonicalNodeName(BaseModel):
    canonical_name: str = Field(..., description="The canonical (standardized) name for the node, e.g., 'Sanjaya'.")
    canonical_name_in_sanskrit: Optional[str] = Field(None, description="The canonical name in Devanagari (Sanskrit script), e.g., 'संजय'.")
    node_type: Optional[str] = Field(None, description="Semantic type of the node, e.g., 'person', 'epithet'.")
    variants: List[str] = Field(default_factory=list, description="List of variant names for the node, e.g., ['Sanjaya', 'Sanjay', ...].")

