import pytest

from data_engineering.connectors.document_connector import DocumentConnector
from data_engineering.schemas.source_schema import SourceRecord


def test_document_connector_loads_txt_file(tmp_path):
    file_path = tmp_path / "project_notes.txt"

    file_path.write_text(
        "Authentication module is incomplete.",
        encoding="utf-8"
    )

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    assert len(records) == 1

    record = records[0]

    assert isinstance(record, SourceRecord)
    assert record.project_id == "TASKFLOW-001"
    assert record.source_type == "document"
    assert record.source_name == "project_notes.txt"
    assert "Authentication module" in record.content


def test_document_connector_loads_multiple_files(tmp_path):
    file1 = tmp_path / "notes1.txt"
    file2 = tmp_path / "notes2.txt"

    file1.write_text("First project note.")
    file2.write_text("Second project note.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file1), str(file2)]
    })

    assert len(records) == 2


def test_document_connector_generates_content_hash(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Sample project documentation.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    assert records[0].content_hash is not None
    assert len(records[0].content_hash) == 64


def test_document_connector_preserves_file_metadata(tmp_path):
    file_path = tmp_path / "architecture.txt"
    file_path.write_text("System architecture documentation.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    metadata = records[0].metadata

    assert metadata["file_type"] == "txt"
    assert metadata["file_name"] == "architecture.txt"
    assert metadata["character_count"] > 0


def test_document_connector_rejects_invalid_input():
    connector = DocumentConnector()

    with pytest.raises(TypeError):
        connector.load("invalid input")


def test_document_connector_rejects_missing_project_id():
    connector = DocumentConnector()

    with pytest.raises(ValueError):
        connector.load({
            "file_paths": ["test.txt"]
        })


def test_document_connector_rejects_empty_file_list():
    connector = DocumentConnector()

    with pytest.raises(ValueError):
        connector.load({
            "project_id": "TASKFLOW-001",
            "file_paths": []
        })


def test_document_connector_rejects_missing_file(tmp_path):
    connector = DocumentConnector()

    with pytest.raises(FileNotFoundError):
        connector.load({
            "project_id": "TASKFLOW-001",
            "file_paths": [str(tmp_path / "missing.txt")]
        })

def test_document_connector_preserves_file_fingerprint(tmp_path):
    import hashlib

    file_path = tmp_path / "fingerprint.txt"
    original_content = "Project architecture documentation."
    file_path.write_text(original_content, encoding="utf-8")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    record = records[0]

    expected_file_hash = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    expected_content_hash = hashlib.sha256(
        record.content.encode("utf-8")
    ).hexdigest()

    assert record.metadata["file_sha256"] == expected_file_hash
    assert record.metadata["content_sha256"] == expected_content_hash
    assert record.content_hash == expected_content_hash


def test_document_connector_preserves_pdf_page_provenance(tmp_path):
    import pymupdf

    file_path = tmp_path / "report.pdf"

    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "First page evidence.")

    page2 = document.new_page()
    page2.insert_text((72, 72), "Second page evidence.")

    document.save(file_path)
    document.close()

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    metadata = records[0].metadata

    assert len(metadata["pages"]) == 2
    assert metadata["pages"][0]["page_number"] == 1
    assert metadata["pages"][1]["page_number"] == 2
    assert "First page evidence." in metadata["pages"][0]["content"]
    assert "Second page evidence." in metadata["pages"][1]["content"]
    assert metadata["extraction_metadata"]["page_count"] == 2


def test_document_connector_preserves_docx_sections(tmp_path):
    from docx import Document

    file_path = tmp_path / "report.docx"

    document = Document()
    document.add_paragraph("Project overview.")

    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Task"
    table.cell(0, 1).text = "Status"

    document.add_paragraph("Project conclusion.")
    document.save(file_path)

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    metadata = records[0].metadata
    sections = metadata["sections"]

    assert len(sections) == 3
    assert sections[0]["type"] == "paragraph"
    assert sections[0]["content"] == "Project overview."
    assert sections[1]["type"] == "table"
    assert sections[1]["rows"][0] == ["Task", "Status"]
    assert sections[2]["type"] == "paragraph"
    assert sections[2]["content"] == "Project conclusion."
    assert metadata["extraction_metadata"]["section_count"] == 3


def test_document_connector_sets_provenance_schema_version(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Project notes.")

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    assert records[0].metadata["provenance_schema_version"] == "1.0"