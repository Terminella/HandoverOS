import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.security import create_user_session
from data_engineering.storage.database import Base, get_db
from data_engineering.storage.models import User, Project, ProjectMember


@pytest.fixture
def member_api(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'members.db'}",
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
        owner = User(name="Owner", email="owner@test.com", password_hash="unused")
        editor = User(name="Editor", email="editor@test.com", password_hash="unused")
        viewer = User(name="Viewer", email="viewer@test.com", password_hash="unused")
        outsider = User(name="Outsider", email="outsider@test.com", password_hash="unused")
        db.add_all([owner, editor, viewer, outsider])
        db.flush()

        project = Project(
            name="Test Project",
            description="",
            owner_id=owner.id,
            status="active",
        )
        db.add(project)
        db.flush()

        db.add(ProjectMember(project_id=project.id, user_id=owner.id, role="owner"))
        db.commit()

        owner_id, editor_id, viewer_id, outsider_id = (
            owner.id, editor.id, viewer.id, outsider.id
        )
        project_id = project.id

        owner_token = create_user_session(db, owner_id)
        outsider_token = create_user_session(db, outsider_id)
        db.commit()

    client = TestClient(app)
    yield client, project_id, owner_id, editor_id, viewer_id, outsider_id, owner_token, outsider_token

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_owner_can_add_update_and_remove_member(member_api):
    client, project_id, owner_id, editor_id, _, _, owner_token, _ = member_api
    headers = {"Authorization": f"Bearer {owner_token}"}

    response = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json={"user_id": editor_id, "role": "editor"},
    )
    assert response.status_code == 201
    assert response.json()["member"]["role"] == "editor"

    response = client.patch(
        f"/api/projects/{project_id}/members/{editor_id}",
        headers=headers,
        json={"role": "viewer"},
    )
    assert response.status_code == 200
    assert response.json()["member"]["role"] == "viewer"

    response = client.delete(
        f"/api/projects/{project_id}/members/{editor_id}",
        headers=headers,
    )
    assert response.status_code == 200


def test_non_owner_cannot_manage_members(member_api):
    client, project_id, _, editor_id, _, _, _, outsider_token = member_api
    headers = {"Authorization": f"Bearer {outsider_token}"}

    response = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json={"user_id": editor_id, "role": "viewer"},
    )
    assert response.status_code == 403


def test_owner_cannot_be_demoted_or_removed(member_api):
    client, project_id, owner_id, _, _, _, owner_token, _ = member_api
    headers = {"Authorization": f"Bearer {owner_token}"}

    update_response = client.patch(
        f"/api/projects/{project_id}/members/{owner_id}",
        headers=headers,
        json={"role": "viewer"},
    )
    assert update_response.status_code == 400

    delete_response = client.delete(
        f"/api/projects/{project_id}/members/{owner_id}",
        headers=headers,
    )
    assert delete_response.status_code == 400


def test_duplicate_member_is_rejected(member_api):
    client, project_id, _, editor_id, _, _, owner_token, _ = member_api
    headers = {"Authorization": f"Bearer {owner_token}"}

    payload = {"user_id": editor_id, "role": "editor"}

    first = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json=payload,
    )
    second = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_member_role_is_rejected(member_api):
    client, project_id, _, editor_id, _, _, owner_token, _ = member_api
    headers = {"Authorization": f"Bearer {owner_token}"}

    response = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json={"user_id": editor_id, "role": "admin"},
    )
    assert response.status_code == 422


def test_nonexistent_user_is_rejected(member_api):
    client, project_id, _, _, _, _, owner_token, _ = member_api
    headers = {"Authorization": f"Bearer {owner_token}"}

    response = client.post(
        f"/api/projects/{project_id}/members",
        headers=headers,
        json={"user_id": "nonexistent-user", "role": "viewer"},
    )
    assert response.status_code == 404
