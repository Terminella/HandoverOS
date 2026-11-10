import hashlib
from pathlib import Path
from typing import Any

from data_engineering.connectors.base_connector import BaseConnector
from data_engineering.extractors.document_extractor import DocumentExtractor
from data_engineering.schemas.source_schema import SourceRecord


class DocumentConnector(BaseConnector):

    def __init__(self):
        self.extractor = DocumentExtractor()

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

            extracted = self.extractor.extract(file_path)

            content = extracted["content"]

            content_hash = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            path = Path(file_path)

            record = SourceRecord(
                project_id=project_id,
                source_type="document",
                source_name=extracted["source_name"],
                source_id=content_hash,
                title=path.stem,
                content=content,
                content_hash=content_hash,
                metadata={
                    "file_type": extracted["file_type"],
                    "character_count": extracted["character_count"],
                    "file_name": path.name,
                }
            )

            records.append(record)

        return records