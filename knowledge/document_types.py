from enum import StrEnum

class DocumentType(StrEnum):
    PDF="pdf"; DOCX="docx"; PPTX="pptx"; XLSX="xlsx"; CSV="csv"; TXT="txt"; MD="md"; HTML="html"; JSON="json"; IMAGE="image"; UNKNOWN="unknown"

SUPPORTED_EXTENSIONS={".pdf":DocumentType.PDF,".docx":DocumentType.DOCX,".pptx":DocumentType.PPTX,".xlsx":DocumentType.XLSX,".xls":DocumentType.XLSX,".csv":DocumentType.CSV,".txt":DocumentType.TXT,".md":DocumentType.MD,".html":DocumentType.HTML,".htm":DocumentType.HTML,".json":DocumentType.JSON,".png":DocumentType.IMAGE,".jpg":DocumentType.IMAGE,".jpeg":DocumentType.IMAGE,".webp":DocumentType.IMAGE}

def detect_type(filename:str)->DocumentType:
    from pathlib import Path
    return SUPPORTED_EXTENSIONS.get(Path(filename).suffix.lower(),DocumentType.UNKNOWN)
