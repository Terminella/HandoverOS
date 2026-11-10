from data_engineering.connectors.synthetic_repository_loader import (
    SyntheticRepositoryLoader
)
from data_engineering.generators.repository_generator import (
    RepositoryGenerator
)


def test_loader_converts_complete_repository():
    generator = RepositoryGenerator()
    repository_data = generator.generate_base_data()

    loader = SyntheticRepositoryLoader()
    records = loader.load(repository_data)

    assert len(records) > 0
    assert all(record.source_type == "synthetic" for record in records)


def test_loader_preserves_repository_id():
    generator = RepositoryGenerator()
    repository_data = generator.generate_base_data()

    loader = SyntheticRepositoryLoader()
    records = loader.load(repository_data)

    assert all(
        record.project_id == "TASKFLOW-001"
        for record in records
    )


def test_loader_preserves_commit_information():
    generator = RepositoryGenerator()
    repository_data = generator.generate_base_data()

    loader = SyntheticRepositoryLoader()
    records = loader.load(repository_data)

    commit_records = [
        record for record in records
        if record.source_name == "Synthetic Commit"
    ]

    assert len(commit_records) == 59
    assert commit_records[0].author == "Alex Morgan"
    assert commit_records[0].title == "Initial FastAPI project structure"


def test_loader_preserves_issues_and_pull_requests():
    generator = RepositoryGenerator()
    repository_data = generator.generate_base_data()

    loader = SyntheticRepositoryLoader()
    records = loader.load(repository_data)

    issues = [
        record for record in records
        if record.source_name == "Synthetic Issue"
    ]

    pull_requests = [
        record for record in records
        if record.source_name == "Synthetic Pull Request"
    ]

    assert len(issues) == 20
    assert len(pull_requests) == 12


def test_loader_rejects_invalid_repository_data():
    loader = SyntheticRepositoryLoader()

    try:
        loader.load([])
        assert False, "Expected TypeError"
    except TypeError:
        pass


def test_loader_rejects_missing_repository_metadata():
    loader = SyntheticRepositoryLoader()

    try:
        loader.load({"developers": []})
        assert False, "Expected ValueError"
    except ValueError:
        pass