from data_engineering.generators.repository_generator import RepositoryGenerator
from data_engineering.connectors.synthetic_repository_loader import SyntheticRepositoryLoader
from data_engineering.preprocessing.normalizer import TextNormalizer
from data_engineering.preprocessing.validator import DataValidator


class IngestionPipeline:
    """
    Coordinates synthetic repository generation, loading,
    text normalization, and data validation.
    """

    def __init__(self):
        self.generator = RepositoryGenerator()
        self.loader = SyntheticRepositoryLoader()
        self.normalizer = TextNormalizer()

    def run(self):
        """
        Execute the complete data ingestion pipeline.

        Returns:
            list[SourceRecord]: Clean and validated source records.
        """

        # Step 1: Generate synthetic repository data
        repository_data = self.generator.generate_base_data()

        # Step 2: Convert repository data into SourceRecord objects
        records = self.loader.load(repository_data)

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