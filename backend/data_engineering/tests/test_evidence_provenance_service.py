import pytest

from data_engineering.schemas.source_schema import SourceRecord
from data_engineering.services.evidence_provenance_service import (
    EvidenceProvenanceResolver,
)


@pytest.fixture
def resolver():
    return EvidenceProvenanceResolver()


@pytest.fixture
def text_source():
    return SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="notes.txt",
        source_id="text-source-001",
        content="The authentication module is incomplete.",
        content_hash="content-hash",
        metadata={
            "file_sha256": "original-file-hash"
        },
    )


def test_resolves_exact_text_quote(resolver, text_source):
    result = resolver.resolve(
        text_source,
        "authentication module is incomplete"
    )

    assert result["status"] == "found"
    assert result["match_count"] == 1

    match = result["matches"][0]

    assert match["location_type"] == "full_text"
    assert match["start_offset"] == 4
    assert match["end_offset"] == 39


def test_returns_document_fingerprint(resolver, text_source):
    result = resolver.resolve(
        text_source,
        "authentication module"
    )

    assert result["document_hash"] == "original-file-hash"
    assert result["content_hash"] == "content-hash"


def test_normalizes_whitespace(resolver, text_source):
    result = resolver.resolve(
        text_source,
        "authentication   module\nis incomplete."
    )

    assert result["status"] == "found"
    assert result["match_count"] == 1


def test_normalizes_unicode(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="unicode.txt",
        source_id="unicode-source",
        content="The ＡＰＩ module is ready.",
    )

    result = resolver.resolve(source, "API module")

    assert result["status"] == "found"


def test_detects_duplicate_quotes(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="duplicate.txt",
        source_id="duplicate-source",
        content="System is ready. System is ready.",
    )

    result = resolver.resolve(source, "System is ready.")

    assert result["status"] == "ambiguous"
    assert result["match_count"] == 2


def test_reports_missing_quote(resolver, text_source):
    result = resolver.resolve(
        text_source,
        "Database migration completed."
    )

    assert result["status"] == "not_found"
    assert result["match_count"] == 0
    assert result["matches"] == []


def test_resolves_pdf_page_location(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.pdf",
        source_id="pdf-source",
        content="Combined PDF content",
        metadata={
            "file_sha256": "pdf-hash",
            "pages": [
                {
                    "page_number": 1,
                    "content": "Project introduction."
                },
                {
                    "page_number": 2,
                    "content": "Authentication module failed."
                },
            ],
        },
    )

    result = resolver.resolve(
        source,
        "Authentication module failed."
    )

    assert result["status"] == "found"
    assert result["matches"][0]["location_type"] == "pdf_page"
    assert result["matches"][0]["page_number"] == 2
    assert result["matches"][0]["start_offset"] == 0


def test_resolves_docx_paragraph_location(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.docx",
        source_id="docx-source",
        content="Project overview. Authentication failed.",
        metadata={
            "sections": [
                {
                    "type": "paragraph",
                    "content": "Project overview."
                },
                {
                    "type": "paragraph",
                    "content": "Authentication failed."
                },
            ]
        },
    )

    result = resolver.resolve(
        source,
        "Authentication failed."
    )

    assert result["status"] == "found"

    match = result["matches"][0]

    assert match["location_type"] == "docx_paragraph"
    assert match["section_index"] == 1
    assert match["start_offset"] == 0


def test_resolves_docx_table_row_location(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="tasks.docx",
        source_id="table-source",
        content="Task: Authentication | Status: Pending",
        metadata={
            "sections": [
                {
                    "type": "table",
                    "rows": [
                        ["Task", "Status"],
                        ["Authentication", "Pending"],
                    ],
                }
            ]
        },
    )

    result = resolver.resolve(
        source,
        "Authentication | Pending"
    )

    assert result["status"] == "found"

    match = result["matches"][0]

    assert match["location_type"] == "docx_table_row"
    assert match["section_index"] == 0
    assert match["row_index"] == 1


def test_rejects_invalid_source(resolver):
    with pytest.raises(TypeError):
        resolver.resolve("invalid source", "some quotation")


def test_rejects_empty_quote(resolver, text_source):
    with pytest.raises(ValueError):
        resolver.resolve(text_source, "   ")


def test_returns_multiple_pdf_locations(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.pdf",
        source_id="multi-page-source",
        content="Repeated evidence",
        metadata={
            "pages": [
                {
                    "page_number": 1,
                    "content": "System operational."
                },
                {
                    "page_number": 2,
                    "content": "System operational."
                },
            ]
        },
    )

    result = resolver.resolve(source, "System operational.")

    assert result["status"] == "ambiguous"
    assert result["match_count"] == 2

    page_numbers = [
        match["page_number"]
        for match in result["matches"]
    ]

    assert page_numbers == [1, 2]


def test_end_to_end_pdf_provenance(tmp_path):
    import pymupdf

    from data_engineering.connectors.document_connector import (
        DocumentConnector,
    )

    file_path = tmp_path / "maintenance_report.pdf"

    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "Routine maintenance completed.")

    page2 = document.new_page()
    page2.insert_text(
        (72, 72),
        "The cooling system experienced abnormal pressure."
    )

    document.save(file_path)
    document.close()

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    resolver = EvidenceProvenanceResolver()

    result = resolver.resolve(
        records[0],
        "cooling system experienced abnormal pressure."
    )

    assert result["status"] == "found"
    assert result["matches"][0]["location_type"] == "pdf_page"
    assert result["matches"][0]["page_number"] == 2
    assert result["document_hash"] is not None


def test_end_to_end_docx_provenance(tmp_path):
    from docx import Document

    from data_engineering.connectors.document_connector import (
        DocumentConnector,
    )

    file_path = tmp_path / "project_report.docx"

    document = Document()

    document.add_paragraph("Project overview.")

    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Module"
    table.cell(0, 1).text = "Status"

    table.add_row().cells[0].text = "Authentication"
    table.rows[1].cells[1].text = "Incomplete"

    document.add_paragraph("Further work is required.")

    document.save(file_path)

    connector = DocumentConnector()

    records = connector.load({
        "project_id": "TASKFLOW-001",
        "file_paths": [str(file_path)]
    })

    resolver = EvidenceProvenanceResolver()

    result = resolver.resolve(
        records[0],
        "Authentication | Incomplete"
    )

    assert result["status"] == "found"
    assert result["matches"][0]["location_type"] == "docx_table_row"
    assert result["matches"][0]["row_index"] == 1
    assert result["document_hash"] is not None


def test_combining_unicode_preserves_original_offsets(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="unicode.txt",
        source_id="unicode-001",
        content="Cafe\u0301 is ready.",
    )

    result = resolver.resolve(source, "Café")

    assert result["status"] == "found"
    assert result["matches"][0]["start_offset"] == 0
    assert result["matches"][0]["end_offset"] == 5


def test_compatibility_character_preserves_original_offsets(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="unicode.txt",
        source_id="unicode-002",
        content="The ﬁle exists.",
    )

    result = resolver.resolve(source, "The file")

    assert result["status"] == "found"
    assert result["matches"][0]["start_offset"] == 0
    assert result["matches"][0]["end_offset"] == 7


def test_leading_and_trailing_whitespace_preserves_offsets(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="spaces.txt",
        source_id="spaces-001",
        content="  Alpha \t beta  ",
    )

    result = resolver.resolve(source, " Alpha beta ")

    assert result["status"] == "found"
    assert result["matches"][0]["start_offset"] == 2
    assert result["matches"][0]["end_offset"] == 14


def test_malformed_docx_sections_fall_back_to_full_text(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.docx",
        source_id="docx-002",
        content="Authentication failed.",
        metadata={
            "sections": [
                "malformed section",
                {
                    "type": "paragraph",
                    "content": "Authentication failed.",
                },
            ]
        },
    )

    result = resolver.resolve(source, "Authentication failed.")

    assert result["status"] == "found"
    assert result["match_count"] == 1
    assert result["matches"][0]["location_type"] == "full_text"
    assert "section_index" not in result["matches"][0]


def test_malformed_pdf_pages_fall_back_to_full_text(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.pdf",
        source_id="pdf-malformed",
        content="Important information from the damaged page.",
        metadata={
            "pages": [
                {
                    "page_number": 1,
                    "content": "Normal page content.",
                },
                {
                    "page_number": "invalid",
                    "content": "Malformed page metadata.",
                },
            ]
        },
    )

    result = resolver.resolve(
        source,
        "Important information from the damaged page.",
    )

    assert result["status"] == "found"
    assert result["match_count"] == 1
    assert result["matches"][0]["location_type"] == "full_text"


def test_malformed_docx_table_falls_back_to_full_text(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="report.docx",
        source_id="docx-malformed",
        content="Critical information inside the damaged table.",
        metadata={
            "sections": [
                {
                    "type": "paragraph",
                    "content": "Normal paragraph.",
                },
                {
                    "type": "table",
                    "rows": [
                        ["Valid cell", 123],
                    ],
                },
            ]
        },
    )

    result = resolver.resolve(
        source,
        "Critical information inside the damaged table.",
    )

    assert result["status"] == "found"
    assert result["match_count"] == 1
    assert result["matches"][0]["location_type"] == "full_text"


def test_hangul_jamo_normalization_preserves_original_offsets(resolver):
    source = SourceRecord(
        project_id="TASKFLOW-001",
        source_type="document",
        source_name="unicode.txt",
        source_id="unicode-hangul",
        content="한글 is ready.",
    )

    result = resolver.resolve(source, "한글")

    assert result["status"] == "found"
    assert result["matches"][0]["start_offset"] == 0
    assert result["matches"][0]["end_offset"] == 6


