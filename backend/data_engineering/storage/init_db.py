from data_engineering.storage.database import engine, Base
from data_engineering.storage.models import SourceRecordModel


def initialize_database():
    Base.metadata.create_all(bind=engine)

    print("HandoverOS database initialized successfully!")

    print("Created tables:")
    for table in Base.metadata.sorted_tables:
        print(f"- {table.name}")


if __name__ == "__main__":
    initialize_database()