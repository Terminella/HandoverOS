from data_engineering.ingestion_pipeline import IngestionPipeline
from data_engineering.storage.database import SessionLocal
from data_engineering.storage.repository import SourceRecordRepository


def ingest_and_store():
    # Generate and process synthetic repository data
    pipeline = IngestionPipeline()
    records = pipeline.run()

    print(f"Successfully processed {len(records)} records.")

    # Connect to local PostgreSQL
    db = SessionLocal()

    try:
        repository = SourceRecordRepository(db)

        # Store all processed records
        stored_records = repository.create_many(records)

        print(f"Successfully stored {len(stored_records)} records.")

        # Verify database count
        total_records = repository.count()

        print(f"Total records in database: {total_records}")

        return total_records

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    ingest_and_store()