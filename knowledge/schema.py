from dataclasses import dataclass, field
from datetime import datetime
from knowledge.document_types import DocumentType

@dataclass(frozen=True)
class SourceLocation:
    page:int|None=None
    slide:int|None=None
    sheet:str|None=None
    row:int|None=None
    section:str|None=None

@dataclass(frozen=True)
class NormalizedDocument:
    document_id:str
    filename:str
    document_type:DocumentType
    title:str
    text:str
    source_locations:tuple[SourceLocation,...]=()
    metadata:dict[str,str]=field(default_factory=dict)
    extracted_at:datetime|None=None

@dataclass(frozen=True)
class NormalizedChunk:
    chunk_id:str
    document_id:str
    text:str
    location:SourceLocation
    metadata:dict[str,str]=field(default_factory=dict)
