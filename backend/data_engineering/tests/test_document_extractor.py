import pytest

from docx import Document
import pymupdf

from data_engineering.extractors.document_extractor import DocumentExtractor


@pytest.fixture
def extractor():
    return DocumentExtractor()


def test_txt_extraction(extractor, tmp_path):

    file_path = tmp_path / "project_notes.txt"

    file_path.write_text(
        "HandoverOS preserves critical project knowledge.",
        encoding="utf-8"
    )

    result = extractor.extract(str(file_path))

    assert result["source_name"] == "project_notes.txt"
    assert result["file_type"] == "txt"
    assert "HandoverOS" in result["content"]
    assert result["character_count"] > 0


def test_docx_extraction(extractor, tmp_path):

    file_path = tmp_path / "project_notes.docx"

    document = Document()
    document.add_paragraph(
        "HandoverOS preserves project knowledge."
    )
    document.save(file_path)

    result = extractor.extract(str(file_path))

    assert result["source_name"] == "project_notes.docx"
    assert result["file_type"] == "docx"
    assert "HandoverOS" in result["content"]


def test_pdf_extraction(extractor, tmp_path):

    file_path = tmp_path / "project_notes.pdf"

    document = pymupdf.open()
    page = document.new_page()

    page.insert_text(
        (72, 72),
        "HandoverOS preserves project knowledge."
    )

    document.save(file_path)
    document.close()

    result = extractor.extract(str(file_path))

    assert result["source_name"] == "project_notes.pdf"
    assert result["file_type"] == "pdf"
    assert "HandoverOS" in result["content"]
    assert "Page 1" in result["content"]


def test_unsupported_file(extractor, tmp_path):

    file_path = tmp_path / "test.xyz"
    file_path.write_text("Testing")

    with pytest.raises(ValueError):
        extractor.extract(str(file_path))


def test_missing_file(extractor):

    with pytest.raises(FileNotFoundError):
        extractor.extract("missing_file.pdf")


def test_empty_txt_file(extractor, tmp_path):

    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    result = extractor.extract(str(file_path))

    assert result["content"] == ""
    assert result["character_count"] == 0