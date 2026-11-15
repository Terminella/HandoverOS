import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_engineering.storage.database import Base
from data_engineering.storage.models import ProjectMember, Project, User


@pytest.mark.parametrize("role", ["owner", "editor", "viewer"])
def test_project_member_accepts_valid_roles(role):
    member = ProjectMember(role=role)
    assert member.role == role


@pytest.mark.parametrize("role", ["admin", "", "superuser", "invalid"])
def test_project_member_rejects_invalid_roles(role):
    with pytest.raises(ValueError, match="Invalid project role"):
        ProjectMember(role=role)


def test_project_member_default_role_is_viewer(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'rbac.db'}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        user = User(
            name="RBAC User",
            email="rbac@example.com",
            password_hash="not-used",
        )
        db.add(user)
        db.flush()

        project = Project(
            name="RBAC Project",
            description="",
            owner_id=user.id,
            status="active",
        )
        db.add(project)
        db.flush()

        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
        )
        db.add(member)
        db.flush()

        assert member.role == "viewer"

    engine.dispose()
