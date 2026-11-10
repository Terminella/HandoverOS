from typing import Any

from data_engineering.generators.repository_generator import RepositoryGenerator

from data_engineering.connectors.base_connector import BaseConnector
from data_engineering.connectors.synthetic_repository_loader import (
    SyntheticRepositoryLoader
)

from data_engineering.preprocessing.normalizer import TextNormalizer
from data_engineering.preprocessing.validator import DataValidator


class IngestionPipeline:
    """
    Coordinates data ingestion, normalization and validation.

    Supports interchangeable connectors implementing BaseConnector.
    """

    def __init__(self, connector: BaseConnector | None = None):

        # Use the synthetic connector by default
        if connector is None:
            self.generator = RepositoryGenerator()
            self.connector = SyntheticRepositoryLoader()
        else:
            if not isinstance(connector, BaseConnector):
                raise TypeError(
                    "Connector must implement the BaseConnector interface."
                )

            self.generator = None
            self.connector = connector

        self.normalizer = TextNormalizer()

    def run(self, source_data: Any = None):
        """
        Execute the complete data ingestion pipeline.

        Args:
            source_data: Raw data supplied to the selected connector.

        Returns:
            List of normalized and validated SourceRecord objects.
        """

        # Step 1: Generate default demonstration data if necessary
        if source_data is None:

            if self.generator is None:
                raise ValueError(
                    "Source data must be provided when using a custom connector."
                )

            source_data = self.generator.generate_base_data()

        # Step 2: Load data through the selected connector
        records = self.connector.load(source_data)

        # Step 3: Normalize text content
        normalized_records = []

        for record in records:

            record_data = record.model_dump()

            record_data["content"] = self.normalizer.normalize_text(
                record_data["content"]
            )

            if record_data.get("title"):
                record_data["title"] = self.normalizer.normalize_text(
                    record_data["title"]
                )

            normalized_records.append(record_data)

        # Step 4: Validate normalized records
        validated_records = DataValidator.validate_records(
            normalized_records
        )

        return validated_records


if __name__ == "__main__":

    pipeline = IngestionPipeline()

    results = pipeline.run()

    print("\n========== HANDOVEROS DATA INGESTION ==========")

    print(f"Total records ingested: {len(results)}")

    print("\nRecord distribution:")

    distribution = {}

    for record in results:

        distribution[record.source_name] = (
            distribution.get(record.source_name, 0) + 1
        )

    for source, count in distribution.items():
        print(f"{source}: {count}")

    print("\nSample record:")
    print(results[0].model_dump_json(indent=4))

    print("\nData ingestion completed successfully!")