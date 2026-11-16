import csv
from pathlib import Path

import pymupdf
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


class DocumentExtractor:
    """Extract structured text and metadata from supported documents."""

    SUPPORTED_FORMATS = {".pdf", ".docx", ".txt", ".csv"}

    def extract(self, file_path: str) -> dict:
        """
        Extract document content while preserving available structure.

        Supports PDF, DOCX, TXT and CSV files. Returns extracted content,
        document metadata, and page or section information where available.
        """
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {extension}")

        metadata = {}
        pages = []
        sections = []

        try:
            if extension == ".pdf":
                content, pages = self._extract_pdf(path)
                metadata["page_count"] = len(pages)

            elif extension == ".docx":
                content, sections = self._extract_docx(path)
                metadata["section_count"] = len(sections)

            elif extension == ".txt":
                content = self._extract_txt(path)

            else:
                content = self._extract_csv(path)

        except (pymupdf.FileDataError, RuntimeError) as error:
            raise ValueError(
                f"Unable to extract document: {error}"
            ) from error

        except Exception as error:
            if isinstance(error, (ValueError, FileNotFoundError)):
                raise

            raise ValueError(
                f"Document extraction failed: {error}"
            ) from error

        return {
            "source_name": path.name,
            "file_type": extension.lstrip("."),
            "content": content,
            "character_count": len(content),
            "pages": pages,
            "sections": sections,
            "metadata": metadata,
        }

    def _extract_pdf(self, path: Path) -> tuple[str, list[dict]]:
        """
        Extract PDF text page by page.

        Preserves individual page numbers and their extracted text.
        """
        pages = []

        with pymupdf.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text()

                pages.append({
                    "page_number": page_number,
                    "content": page_text,
                })

        content = "\n".join(
            f"\n--- Page {page['page_number']} ---\n{page['content']}"
            for page in pages
        )

        return content, pages

    def _extract_docx(self, path: Path) -> tuple[str, list[dict]]:
        """
        Extract DOCX paragraphs and tables in their original document order.
        """
        document = Document(path)
        body_elements = []

        for element in document.element.body.iterchildren():

            if isinstance(element, CT_P):
                paragraph = Paragraph(element, document)
                text = paragraph.text.strip()

                if text:
                    body_elements.append({
                        "type": "paragraph",
                        "content": text,
                    })

            elif isinstance(element, CT_Tbl):
                table = Table(element, document)
                rows = []

                for row in table.rows:
                    rows.append([
                        cell.text.strip()
                        for cell in row.cells
                    ])

                body_elements.append({
                    "type": "table",
                    "rows": rows,
                })

        content_parts = []

        for section in body_elements:
            if section["type"] == "paragraph":
                content_parts.append(section["content"])

            else:
                for row_number, row in enumerate(
                    section["rows"], start=1
                ):
                    content_parts.append(
                        f"Row {row_number}: "
                        + " | ".join(row)
                    )

        return "\n\n".join(content_parts), body_elements

    def _extract_txt(self, path: Path) -> str:
        """Extract text from a UTF-8 encoded plain-text file."""
        return path.read_text(encoding="utf-8-sig")

    def _extract_csv(self, path: Path) -> str:
        """
        Extract CSV records while preserving column names and values.

        Validates headers and checks for missing or extra row values.
        """
        rows = []

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as csv_file:

                reader = csv.DictReader(csv_file)

                if not reader.fieldnames:
                    raise ValueError(
                        "CSV file is empty or has no headers."
                    )

                headers = reader.fieldnames

                if any(not header.strip() for header in headers):
                    raise ValueError(
                        "CSV contains an empty column name."
                    )

                if len(headers) != len(set(headers)):
                    raise ValueError(
                        "CSV contains duplicate column names."
                    )

                for row_number, row in enumerate(reader, start=1):

                    if None in row:
                        raise ValueError(
                            f"CSV row {row_number} contains extra values."
                        )

                    if any(value is None for value in row.values()):
                        raise ValueError(
                            f"CSV row {row_number} has missing columns."
                        )

                    row_content = [
                        f"{column}: {value}"
                        for column, value in row.items()
                    ]

                    rows.append(
                        f"Row {row_number}:\n"
                        + "\n".join(row_content)
                    )

        except csv.Error as error:
            raise ValueError(
                f"Unable to parse CSV file: {error}"
            ) from error

        return "\n\n".join(rows)