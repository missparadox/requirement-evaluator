from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.evaluation import EvaluationDetail
from app.services.evaluation_service import CreateEvaluationResult, EvaluationService
from app.storage.evaluation_store import EvaluationStore


router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


def get_service() -> EvaluationService:
    store = EvaluationStore(get_settings().data_dir / "evaluations")
    return EvaluationService(store)


@router.post("")
async def create_evaluation(
    file: UploadFile = File(...),
    service: EvaluationService = Depends(get_service),
) -> CreateEvaluationResult:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return service.create_or_reuse(filename=file.filename or "upload.bin", file_bytes=payload)


@router.get("/{evaluation_id}")
def get_evaluation(
    evaluation_id: str,
    service: EvaluationService = Depends(get_service),
) -> EvaluationDetail:
    try:
        return service.get_detail(evaluation_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Evaluation not found.") from exc
