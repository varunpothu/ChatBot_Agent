from pathlib import Path

from knowledge.document_types import DocumentType,detect_type
from knowledge.schema import NormalizedDocument

IMAGE_TYPES={DocumentType.IMAGE}

def parse_image_with_ocr(path:str|Path)->NormalizedDocument:
    """OCR adapter boundary.

    The repository intentionally does not fake OCR results. Connect AWS
    Textract or another OCR provider here and preserve page/image metadata.
    """
    path=Path(path)
    if detect_type(path.name) not in IMAGE_TYPES:
        raise ValueError("OCR parser expects an image file")
    raise NotImplementedError("Connect the production OCR provider in the next milestone")
