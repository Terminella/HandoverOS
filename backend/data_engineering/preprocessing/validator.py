from pydantic import ValidationError

from data_engineering.schemas.source_schema import SourceRecord


class DataValidator:

    @staticmethod
    def validate_record(data: dict) -> SourceRecord:
        """
        Validate incoming data against the SourceRecord schema.

        Returns:
            Validated SourceRecord object.

        Raises:
            ValidationError: If the record is invalid.
        """

        return SourceRecord(**data)

    @staticmethod
    def validate_records(records: list[dict]) -> list[SourceRecord]:
        """
        Validate multiple records.

        Invalid records are rejected rather than silently discarded.
        """

        validated_records = []

        for record in records:
            validated_records.append(
                DataValidator.validate_record(record)
            )

        return validated_records