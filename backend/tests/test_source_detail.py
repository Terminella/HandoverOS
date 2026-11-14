"""Tests for authenticated source-detail retrieval and uploaded PDF text."""

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.security import create_user_session
from data_engineering.storage.database import Base, get_db
from data_engineering.storage.models import Project, ProjectMember, Source, User


@pytest.fixture
def source_api(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'sources.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with SessionLocal() as db:
        owner = User(
            name="Source Owner",
            email="source-owner@example.com",
            password_hash="not-used",
        )
        outsider = User(
            name="Project Outsider",
            email="project-outsider@example.com",
            password_hash="not-used",
        )
        db.add_all([owner, outsider])
        db.flush()

        project = Project(
            name="Source Project",
            description="",
            owner_id=owner.id,
            status="active",
        )
        other_project = Project(
            name="Other Project",
            description="",
            owner_id=owner.id,
            status="active",
        )
        db.add_all([project, other_project])
        db.flush()
        db.add(ProjectMember(project_id=project.id, user_id=owner.id, role="owner"))

        source = Source(
            project_id=project.id,
            source_type="document",
            source_name="sample.pdf",
            source_id="sample-content-hash",
            title="sample",
            content="First paragraph.\n\nSecond paragraph.",
            source_metadata={"file_name": "sample.pdf", "file_type": "pdf"},
        )
        other_source = Source(
            project_id=other_project.id,
            source_type="document",
            source_name="private.pdf",
            source_id="other-content-hash",
            title="private",
            content="Private project text.",
            source_metadata={"file_name": "private.pdf", "file_type": "pdf"},
        )
        db.add_all([source, other_source])
        db.flush()

        owner_token = create_user_session(db, owner.id)
        outsider_token = create_user_session(db, outsider.id)
        ids = {
            "project_id": project.id,
            "source_id": source.id,
            "other_source_id": other_source.id,
            "owner_token": owner_token,
            "outsider_token": outsider_token,
        }

    yield TestClient(app), ids

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_source_detail_returns_extracted_text_and_metadata(source_api):
    client, ids = source_api

    response = client.get(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": ids["source_id"],
        "name": "sample.pdf",
        "title": "sample",
        "type": "document",
        "content": "First paragraph.\n\nSecond paragraph.",
        "metadata": {"file_name": "sample.pdf", "file_type": "pdf"},
    }


def test_source_detail_requires_authentication(source_api):
    client, ids = source_api

    response = client.get(f"/api/sources/{ids['project_id']}/{ids['source_id']}")

    assert response.status_code == 401


def test_source_detail_rejects_non_member(source_api):
    client, ids = source_api

    response = client.get(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}",
        headers={"Authorization": f"Bearer {ids['outsider_token']}"},
    )

    assert response.status_code == 403


def test_source_detail_returns_404_for_missing_source(source_api):
    client, ids = source_api

    response = client.get(
        f"/api/sources/{ids['project_id']}/missing-source",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert response.status_code == 404


def test_source_detail_cannot_read_source_from_another_project(source_api):
    client, ids = source_api

    response = client.get(
        f"/api/sources/{ids['project_id']}/{ids['other_source_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert response.status_code == 404


def test_uploaded_pdf_extracted_text_can_be_retrieved(source_api):
    client, ids = source_api
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Text extracted from the uploaded PDF.")
    pdf_bytes = pdf.tobytes()
    pdf.close()

    upload_response = client.post(
        f"/api/sources/upload?project_id={ids['project_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
        files={"file": ("uploaded.pdf", pdf_bytes, "application/pdf")},
    )

    assert upload_response.status_code == 201
    source_id = upload_response.json()["id"]
    sources_response = client.get(
        f"/api/sources/{ids['project_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )
    detail_response = client.get(
        f"/api/sources/{ids['project_id']}/{source_id}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert sources_response.status_code == 200
    assert any(
        source["id"] == source_id and source["name"] == "uploaded.pdf"
        for source in sources_response.json()
    )
    assert detail_response.status_code == 200
    assert "Text extracted from the uploaded PDF." in detail_response.json()["content"]
    assert detail_response.json()["metadata"]["file_name"] == "uploaded.pdf"
