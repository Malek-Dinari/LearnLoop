"""Expert-in-the-Loop routes: submit, list, approve corrections."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import ExpertCorrection
from app.deps import require_role
from app.models import CorrectionResponse, CorrectionSubmitRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/expert", tags=["expert"])


def _require_db(db: AsyncSession | None) -> AsyncSession:
    if db is None:
        raise HTTPException(503, "Expert features require database — set USE_DATABASE=true")
    return db


def _row_to_response(row: ExpertCorrection) -> CorrectionResponse:
    return CorrectionResponse(
        id=str(row.id),
        original_question=row.original_question,
        corrected_question=row.corrected_question,
        topic_tags=list(row.topic_tags or []),
        expert_id=str(row.expert_id),
        approved=row.approved,
        created_at=row.created_at.isoformat(),
    )


def _validate_corrected(q: dict) -> None:
    if not isinstance(q, dict):
        raise HTTPException(422, "corrected_question must be an object")
    for field in ("question", "correct_answer"):
        if not str(q.get(field, "")).strip():
            raise HTTPException(422, f"corrected_question.{field} is required")


@router.post("/corrections", response_model=CorrectionResponse, status_code=201)
async def submit_correction(
    req: CorrectionSubmitRequest,
    user: dict = Depends(require_role("expert", "admin")),
    db: AsyncSession | None = Depends(get_db),
) -> CorrectionResponse:
    db = _require_db(db)
    _validate_corrected(req.corrected_question)

    tags = sorted({t.strip().lower() for t in req.topic_tags if t.strip()})
    row = ExpertCorrection(
        id=uuid.uuid4(),
        original_question=req.original_question,
        corrected_question=req.corrected_question,
        topic_tags=tags,
        expert_id=uuid.UUID(user["id"]),
        approved=(user["role"] == "admin"),
    )
    db.add(row)
    await db.flush()
    return _row_to_response(row)


@router.get("/corrections", response_model=list[CorrectionResponse])
async def list_corrections(
    approved: bool | None = None,
    user: dict = Depends(require_role("expert", "admin")),
    db: AsyncSession | None = Depends(get_db),
) -> list[CorrectionResponse]:
    db = _require_db(db)
    stmt = select(ExpertCorrection).order_by(ExpertCorrection.created_at.desc())
    # Experts see only their own; admins see all.
    if user["role"] != "admin":
        stmt = stmt.where(ExpertCorrection.expert_id == uuid.UUID(user["id"]))
    if approved is not None:
        stmt = stmt.where(ExpertCorrection.approved.is_(approved))
    rows = (await db.execute(stmt)).scalars().all()
    return [_row_to_response(r) for r in rows]


@router.patch("/corrections/{cid}/approve", response_model=CorrectionResponse)
async def approve_correction(
    cid: str,
    user: dict = Depends(require_role("admin")),
    db: AsyncSession | None = Depends(get_db),
) -> CorrectionResponse:
    db = _require_db(db)
    try:
        row_id = uuid.UUID(cid)
    except ValueError:
        raise HTTPException(404, "Correction not found")

    row = await db.scalar(select(ExpertCorrection).where(ExpertCorrection.id == row_id))
    if row is None:
        raise HTTPException(404, "Correction not found")
    row.approved = True
    await db.flush()
    return _row_to_response(row)
