from pathlib import Path

import pymupdf
from docx import Document


class DocumentExtractor:

    SUPPORTED_FORMATS = {".pdf", ".docx", ".txt"}

    def extract(self, file_path: str) -> dict:
        """
        Extract text from PDF, DOCX or TXT files.

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary containing extracted text and file information.
        """

        path = Path(file_path)

        # Check whether the file exists
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Identify file format
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )

        # Extract according to file format
        if extension == ".pdf":
            content = self._extract_pdf(path)

        elif extension == ".docx":
            content = self._extract_docx(path)

        else:
            content = self._extract_txt(path)

        return {
            "source_name": path.name,
            "file_type": extension.lstrip("."),
            "content": content,
            "character_count": len(content)
        }

    def _extract_pdf(self, path: Path) -> str:
        """Extract text page by page from a PDF."""

        pages = []

        with pymupdf.open(path) as pdf:

            for page_number, page in enumerate(pdf, start=1):

                page_text = page.get_text()

                pages.append(
                    f"\n--- Page {page_number} ---\n{page_text}"
                )

        return "\n".join(pages)

    def _extract_docx(self, path: Path) -> str:
        """Extract paragraphs from a Word document."""

        document = Document(path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    def _extract_txt(self, path: Path) -> str:
        """Extract text from a plain text file."""

        return path.read_text(encoding="utf-8-sig")