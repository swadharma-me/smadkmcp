from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel


# --- Enums for controlled values ---

class Guna(str, Enum):
    sattva = "S"
    rajas = "R"
    tamas = "T"

class Klesa(str, Enum):
    avidya = "avidya"
    asmita = "asmita"
    raga = "raga"
    dvesha = "dvesha"
    abhinivesha = "abhinivesha"

class Antaraya(str, Enum):
    vyadhi = "vyadhi"
    styana = "styana"
    samsaya = "samsaya"
    pramada = "pramada"
    alasya = "alasya"
    avarati = "avarati"
    bhranti_darshana = "bhranti-darshana"
    alabdhabhumikatva = "alabdhabhumikatva"
    anavasthitatva = "anavasthitatva"

class PanchakoshaLocus(str, Enum):
    anna = "anna"
    prana = "prana"
    mano = "mano"
    vijnana = "vijnana"
    ananda = "ananda"

class KarmaYogaPosture(str, Enum):
    doer = "doer"
    enjoyer = "enjoyer"
    balanced = "balanced"

class Pramana(str, Enum):
    shastra = "shastra"
    acharya = "acharya"
    yukti = "yukti"
    anubhava = "anubhava"


# --- Nested models ---

class RoleAlignment(BaseModel):
    adhikara: Optional[str] = None
    svadharma: Optional[str] = None
    yama_niyama: List[str] = []

class GunasState(BaseModel):
    body: Optional[Guna] = None
    mind: Optional[Guna] = None
    speech: Optional[Guna] = None
    environment: Optional[Guna] = None

class Afflictions(BaseModel):
    klesa_primary: Optional[Klesa] = None
    samskara: List[str] = []
    vasana: List[str] = []
    shadripu: List[str] = []

class Obstacles(BaseModel):
    antaraya_primary: Optional[Antaraya] = None

class Epistemics(BaseModel):
    pramana_sources: List[Pramana] = []
    viveka_comment: Optional[str] = None

class KarmaYoga(BaseModel):
    phala_asakti: int = 0
    posture: Optional[KarmaYogaPosture] = None
    prasada_buddhi: int = 0

class PanchakoshaEcosystem(BaseModel):
    ahara: Optional[Guna] = None
    vihara: Optional[Guna] = None
    acara: Optional[Guna] = None
    sanga: Optional[Guna] = None

class Panchakosha(BaseModel):
    locus: Optional[PanchakoshaLocus] = None
    ecosystem: PanchakoshaEcosystem = PanchakoshaEcosystem()

class Devotional(BaseModel):
    shraddha: int = 0
    isvara_pranidhana: int = 0


# --- Root model ---

class DharmicDiagnosis(BaseModel):
    role_alignment: RoleAlignment = RoleAlignment()
    gunas: GunasState = GunasState()
    afflictions: Afflictions = Afflictions()
    obstacles: Obstacles = Obstacles()
    epistemics: Epistemics = Epistemics()
    karma_yoga: KarmaYoga = KarmaYoga()
    panchakosha: Panchakosha = Panchakosha()
    devotional: Devotional = Devotional()