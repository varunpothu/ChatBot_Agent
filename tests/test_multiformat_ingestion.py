from pathlib import Path
from knowledge.document_types import DocumentType,detect_type
from knowledge.parsers import parse_document

def test_supported_types():
    assert detect_type("course.docx")==DocumentType.DOCX
    assert detect_type("fees.xlsx")==DocumentType.XLSX
    assert detect_type("policy.pdf")==DocumentType.PDF
    assert detect_type("faq.md")==DocumentType.MD
    assert detect_type("data.csv")==DocumentType.CSV

def test_markdown(tmp_path:Path):
    p=tmp_path/"faq.md"; p.write_text("# Fees\n\nThe fee is £2800.",encoding="utf-8")
    d=parse_document(p); assert "£2800" in d.text

def test_csv(tmp_path:Path):
    p=tmp_path/"fees.csv"; p.write_text("course,fee\nData Science,2800\n",encoding="utf-8")
    d=parse_document(p); assert "Data Science" in d.text and "2800" in d.text
