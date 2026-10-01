import re
from knowledge.schema import NormalizedChunk,NormalizedDocument,SourceLocation

def semantic_chunks(document:NormalizedDocument,max_chars:int=1200,overlap:int=160)->list[NormalizedChunk]:
    if overlap>=max_chars: raise ValueError("overlap must be smaller than max_chars")
    paragraphs=[p.strip() for p in re.split(r"\n\s*\n",document.text) if p.strip()]
    chunks=[]; buffer=""
    for p in paragraphs:
        if len(buffer)+len(p)+1<=max_chars: buffer=f"{buffer}\n{p}".strip(); continue
        if buffer: chunks.append(_make(document,buffer,len(chunks)))
        buffer=f"{buffer[-overlap:] if buffer else ''}\n{p}".strip()
    if buffer: chunks.append(_make(document,buffer,len(chunks)))
    return chunks

def _make(document,text,index):
    loc=document.source_locations[min(index,len(document.source_locations)-1)] if document.source_locations else SourceLocation()
    return NormalizedChunk(f"{document.document_id}-chunk-{index}",document.document_id,text,loc,{"document_type":document.document_type.value,"filename":document.filename})
