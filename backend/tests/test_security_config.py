from pathlib import Path


def test_compose_requires_database_password_and_limits_host_binding():
    compose_file = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    compose = compose_file.read_text(encoding="utf-8")

    assert "${POSTGRES_PASSWORD:?" in compose
    assert "127.0.0.1:5432:5432" in compose
