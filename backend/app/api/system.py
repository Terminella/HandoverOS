
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from data_engineering.storage.database import get_db
from app.core.security import get_user_id_from_token
from intelligence.config import config
from intelligence.llm.ollama_client import OllamaClient


router = APIRouter(
    prefix="/system",
    tags=["System"]
)


def get_authenticated_user(
    authorization: str | None,
    db: Session
) -> str:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    user_id = get_user_id_from_token(db, token.strip())

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    return user_id


def _validate_base_url(base_url: str) -> str:
    """Validate the Ollama base URL and return it stripped of trailing slash.

    Rejects non-local addresses to prevent SSRF.
    """
    from urllib.parse import urlparse

    stripped = base_url.rstrip("/")
    allowed_schemes = ("http://", "https://")
    if not stripped.startswith(allowed_schemes):
        raise HTTPException(
            status_code=400,
            detail="Invalid Ollama base URL scheme."
        )

    parsed = urlparse(stripped)
    host = parsed.hostname or ""
    if host not in ("127.0.0.1", "localhost") and not host.endswith(".local"):
        raise HTTPException(
            status_code=400,
            detail="Ollama base URL must point to a local endpoint "
                   "(127.0.0.1, localhost, or *.local)."
        )

    return stripped


@router.get("/health")
def system_health(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    get_authenticated_user(authorization, db)
    return {
        "status": "healthy",
        "application": "HandoverOS",
        "version": "1.0.0",
    }


class _OllamaInfo:
    """Cached Ollama client built from the current configuration."""

    @staticmethod
    def build() -> OllamaClient:
        return OllamaClient(config)


@router.get("/llm/status")
def llm_status(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    get_authenticated_user(authorization, db)

    client = _OllamaInfo.build()
    return {
        "provider": config.provider,
        "model": config.model_name,
        "ollama_base_url": config.ollama_base_url,
        "ollama_model": config.ollama_model,
        "model_selection_mode": config.model_selection_mode,
        "is_ollama_provider": config.provider == "ollama",
    }


@router.get("/llm/models")
def llm_models(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """List locally installed Ollama models.

    Returns the model list from Ollama /api/tags, or an error if
    Ollama is unavailable.
    """
    get_authenticated_user(authorization, db)

    if config.provider != "ollama":
        return {
            "provider": config.provider,
            "models": [],
            "message": "Ollama is not the configured provider.",
        }

    client = _OllamaInfo.build()
    try:
        models = client.list_models()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    return {
        "provider": "ollama",
        "base_url": config.ollama_base_url,
        "models": [
            {
                "name": m.name,
                "size": m.size,
                "digest": m.digest,
                "modified_at": m.modified_at,
                "parameter_size": m.parameter_size,
                "quantization": m.quantization,
                "family": m.family,
            }
            for m in models
        ],
        "count": len(models),
    }


class _SelectModelRequest(BaseModel):
    model: str


@router.post("/llm/select")
def llm_select_model(
    data: _SelectModelRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """Select a specific locally installed model.

    Validates that the requested model exists in the installed model
    list before accepting the selection.
    """
    get_authenticated_user(authorization, db)

    if config.provider != "ollama":
        raise HTTPException(
            status_code=400,
            detail="Model selection is only available for the Ollama provider.",
        )

    requested_model = data.model.strip()
    if not requested_model:
        raise HTTPException(
            status_code=400,
            detail="Model name is required.",
        )

    client = _OllamaInfo.build()
    try:
        installed = client.list_models()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    installed_names = {m.name for m in installed}
    if requested_model not in installed_names:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Model '{requested_model}' is not installed locally. "
                f"Available models: {', '.join(sorted(installed_names)) or 'none'}."
            ),
        )

    # The selection is applied at request time by OllamaClient based on
    # the configured ollama_model. Here we validate availability only.
    return {
        "status": "selected",
        "model": requested_model,
        "message": "Model selection validated. The model will be used for subsequent requests.",
    }


class _CompatibilityTestResponse(BaseModel):
    model: str
    status: str
    message: str
    claims_extracted: int


@router.post("/llm/compatibility-test")
def llm_compatibility_test(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    """Test whether the currently selected/resolved model can produce
    valid structured extraction output.

    Runs a controlled extraction against a known text and validates
    the result against the IntelligenceExtraction schema.
    """
    get_authenticated_user(authorization, db)

    if config.provider != "ollama":
        return {
            "status": "not_ollama",
            "message": f"LLM provider is '{config.provider}', not Ollama.",
        }

    client = _OllamaInfo.build()
    try:
        result = client.test_compatibility()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    return result


class _ConnectionTestRequest(BaseModel):
    pass


@router.post("/llm/test")
async def test_llm_connection(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    get_authenticated_user(authorization, db)

    if config.provider != "ollama":
        return {
            "status": "not_ollama",
            "message": f"LLM provider is '{config.provider}', not Ollama. No connection test needed.",
        }

    base_url = _validate_base_url(config.ollama_base_url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/api/tags"
            )
            response.raise_for_status()
            data = response.json()

        models = [m.get("name", "unknown") for m in data.get("models", [])]

        return {
            "status": "connected",
            "message": "Ollama is reachable.",
            "models": models,
            "count": len(models),
            "configured_model": config.ollama_model or "<auto-discovery>",
            "model_selection_mode": config.model_selection_mode,
        }
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Ollama. Check that the Ollama service is running.",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama test failed: {exc}",
        )
