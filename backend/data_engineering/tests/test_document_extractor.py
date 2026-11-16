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


def test_multi_page_pdf_extraction(extractor, tmp_path):
    file_path = tmp_path / "multi_page.pdf"

    document = pymupdf.open()

    for number in range(1, 4):
        page = document.new_page()
        page.insert_text(
            (72, 72),
            f"Content of page {number}"
        )

    document.save(file_path)
    document.close()

    result = extractor.extract(str(file_path))

    assert len(result["pages"]) == 3
    assert result["metadata"]["page_count"] == 3
    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][2]["page_number"] == 3
    assert "Content of page 2" in result["pages"][1]["content"]


def test_docx_table_extraction(extractor, tmp_path):
    file_path = tmp_path / "project_table.docx"

    document = Document()
    document.add_paragraph("Project Information")

    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Task"
    table.cell(0, 1).text = "Status"
    table.cell(1, 0).text = "Backend"
    table.cell(1, 1).text = "Completed"

    document.save(file_path)

    result = extractor.extract(str(file_path))

    assert "Project Information" in result["content"]
    assert "Backend" in result["content"]
    assert "Completed" in result["content"]

    assert any(
        section["type"] == "table"
        for section in result["sections"]
    )


def test_empty_pdf(extractor, tmp_path):
    file_path = tmp_path / "empty.pdf"

    # Create a valid PDF containing one blank page.
    document = pymupdf.open()
    document.new_page()
    document.save(file_path)
    document.close()

    result = extractor.extract(str(file_path))

    assert len(result["pages"]) == 1
    assert result["metadata"]["page_count"] == 1
    assert result["pages"][0]["content"].strip() == ""