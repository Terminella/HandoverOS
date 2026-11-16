import hashlib
from pathlib import Path
from typing import Any

from data_engineering.connectors.base_connector import BaseConnector
from data_engineering.extractors.document_extractor import DocumentExtractor
from data_engineering.schemas.source_schema import SourceRecord


class DocumentConnector(BaseConnector):
    """Loads documents and preserves their extraction provenance."""

    def __init__(self):
        self.extractor = DocumentExtractor()

    @staticmethod
    def _calculate_sha256(content: bytes) -> str:
        """Generate a SHA-256 fingerprint for supplied bytes."""
        return hashlib.sha256(content).hexdigest()

    def load(self, source_data: Any) -> list[SourceRecord]:
        """
        Extract documents and convert them into SourceRecords.

        Expected input:
        {
            "project_id": "TASKFLOW-001",
            "file_paths": ["documents/notes.pdf"]
        }
        """
        if not isinstance(source_data, dict):
            raise TypeError("Source data must be a dictionary.")

        project_id = source_data.get("project_id")
        file_paths = source_data.get("file_paths")

        if not project_id:
            raise ValueError("project_id is required.")

        if not isinstance(file_paths, list) or not file_paths:
            raise ValueError("file_paths must be a non-empty list.")

        records = []

        for file_path in file_paths:
            path = Path(file_path)

            extracted = self.extractor.extract(str(path))

            content = extracted["content"]

            # Fingerprint the original file bytes.
            file_hash = self._calculate_sha256(
                path.read_bytes()
            )

            # Preserve the existing extracted-content hash behaviour.
            content_hash = self._calculate_sha256(
                content.encode("utf-8")
            )

            metadata = {
                "file_type": extracted["file_type"],
                "character_count": extracted["character_count"],
                "file_name": path.name,

                # Original document fingerprint.
                "file_sha256": file_hash,

                # Fingerprint of the extracted text.
                "content_sha256": content_hash,

                # Extraction structure for evidence provenance.
                "pages": extracted.get("pages", []),
                "sections": extracted.get("sections", []),

                "extraction_metadata": extracted.get(
                    "metadata", {}
                ),

                "provenance_schema_version": "1.0",
            }

            record = SourceRecord(
                project_id=project_id,
                source_type="document",
                source_name=extracted["source_name"],
                source_id=content_hash,
                title=path.stem,
                content=content,
                content_hash=content_hash,
                metadata=metadata,
            )

            records.append(record)

        return records