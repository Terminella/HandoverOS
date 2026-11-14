"""Tests for authenticated source-detail retrieval and uploaded PDF text."""

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.security import create_user_session
from data_engineering.storage.database import Base, get_db
from app.core.config import settings
from data_engineering.storage.models import (
    Activity,
    EvidenceLink,
    Handover,
    HandoverItem,
    KnowledgeItem,
    Project,
    ProjectMember,
    Source,
    User,
)


@pytest.fixture
def source_api(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SOURCE_STORAGE_ROOT", str(tmp_path / "source-files"))
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
            source_name="tmp-existing-upload.pdf",
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
        knowledge_item = KnowledgeItem(
            project_id=project.id,
            item_type="decision",
            title="Preserved finding",
            content="Finding remains after source removal.",
            status="identified",
        )
        activity = Activity(
            project_id=project.id,
            source=source,
            activity_type="document",
            title="Preserved activity",
            description="The source reference is cleared on deletion.",
        )
        handover = Handover(
            project_id=project.id,
            created_by=owner.id,
            version=1,
            status="draft",
        )
        db.add_all([source, other_source, knowledge_item, activity, handover])
        db.flush()
        evidence_link = EvidenceLink(
            knowledge_item_id=knowledge_item.id,
            source_id=source.id,
            evidence_note="Source evidence",
        )
        handover_item = HandoverItem(
            handover_id=handover.id,
            knowledge_item_id=knowledge_item.id,
            source_id=source.id,
            content="Preserved handover item",
            section="Decisions",
        )
        db.add_all([evidence_link, handover_item])
        db.flush()

        owner_token = create_user_session(db, owner.id)
        outsider_token = create_user_session(db, outsider.id)
        ids = {
            "project_id": project.id,
            "source_id": source.id,
            "other_source_id": other_source.id,
            "knowledge_item_id": knowledge_item.id,
            "activity_id": activity.id,
            "handover_id": handover.id,
            "handover_item_id": handover_item.id,
            "session_factory": SessionLocal,
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


def test_source_delete_requires_authentication(source_api):
    client, ids = source_api

    response = client.delete(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}"
    )

    assert response.status_code == 401


def test_source_delete_rejects_non_member(source_api):
    client, ids = source_api

    response = client.delete(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}",
        headers={"Authorization": f"Bearer {ids['outsider_token']}"},
    )

    assert response.status_code == 403


def test_source_delete_cannot_remove_source_from_another_project(source_api):
    client, ids = source_api

    response = client.delete(
        f"/api/sources/{ids['project_id']}/{ids['other_source_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert response.status_code == 404


def test_source_delete_returns_404_for_invalid_source_id(source_api):
    client, ids = source_api

    response = client.delete(
        f"/api/sources/{ids['project_id']}/missing-source",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert response.status_code == 404


def test_source_delete_preserves_findings_and_detaches_references(source_api):
    client, ids = source_api
    headers = {"Authorization": f"Bearer {ids['owner_token']}"}

    response = client.delete(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": ids["source_id"],
        "message": "Source removed successfully",
    }

    listed_sources = client.get(
        f"/api/sources/{ids['project_id']}",
        headers=headers,
    )
    deleted_source = client.get(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}",
        headers=headers,
    )
    assert listed_sources.status_code == 200
    assert all(item["id"] != ids["source_id"] for item in listed_sources.json())
    assert deleted_source.status_code == 404

    from sqlalchemy import select

    db = ids["session_factory"]()
    try:
        assert db.get(KnowledgeItem, ids["knowledge_item_id"]) is not None
        assert db.get(Activity, ids["activity_id"]).source_record_id is None
        assert db.get(Handover, ids["handover_id"]) is not None
        handover_item = db.get(HandoverItem, ids["handover_item_id"])
        assert handover_item is not None
        assert handover_item.source_id is None
        assert db.scalar(
            select(EvidenceLink).where(
                EvidenceLink.source_id == ids["source_id"]
            )
        ) is None
    finally:
        db.close()


def test_uploaded_pdf_extracted_text_can_be_retrieved(source_api):
    client, ids = source_api
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Text extracted from sample_handover.pdf.")
    pdf_bytes = pdf.tobytes()
    pdf.close()

    upload_response = client.post(
        f"/api/sources/upload?project_id={ids['project_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
        files={"file": ("sample_handover.pdf", pdf_bytes, "application/pdf")},
    )

    assert upload_response.status_code == 201
    source_id = upload_response.json()["id"]
    assert upload_response.json()["name"] == "sample_handover.pdf"
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
        source["id"] == source_id and source["name"] == "sample_handover.pdf"
        for source in sources_response.json()
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == source_id
    assert detail_response.json()["name"] == "sample_handover.pdf"
    assert "Text extracted from sample_handover.pdf." in detail_response.json()["content"]
    assert detail_response.json()["metadata"]["file_name"] == "sample_handover.pdf"

    refreshed_sources_response = client.get(
        f"/api/sources/{ids['project_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )
    refreshed_detail_response = client.get(
        f"/api/sources/{ids['project_id']}/{source_id}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )

    assert refreshed_sources_response.status_code == 200
    assert any(
        source["id"] == source_id and source["name"] == "sample_handover.pdf"
        for source in refreshed_sources_response.json()
    )
    assert refreshed_detail_response.status_code == 200
    assert "Text extracted from sample_handover.pdf." in refreshed_detail_response.json()["content"]

    content_hash_response = client.get(
        f"/api/sources/{ids['project_id']}/{upload_response.json()['source_id']}",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )
    assert content_hash_response.status_code == 404

    original_pdf_response = client.get(
        f"/api/sources/{ids['project_id']}/{source_id}/file",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )
    assert original_pdf_response.status_code == 200
    assert original_pdf_response.headers["content-type"] == "application/pdf"
    assert original_pdf_response.content == pdf_bytes


def test_old_pdf_source_explains_reupload_is_required(source_api):
    client, ids = source_api
    response = client.get(
        f"/api/sources/{ids['project_id']}/{ids['source_id']}/file",
        headers={"Authorization": f"Bearer {ids['owner_token']}"},
    )
    assert response.status_code == 404
    assert "Re-upload" in response.json()["detail"]
