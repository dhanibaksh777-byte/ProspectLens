from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.search_job import SearchJob, SearchJobStatus
from app.schemas.search import SearchJobCreate, SearchJobResponse, SearchProgressResponse
from app.workers.search_worker import run_search_job

router = APIRouter()


@router.post("", response_model=SearchJobResponse, status_code=201)
def create_search(
    payload: SearchJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = SearchJob(
        user_id=current_user.id,
        name=payload.name,
        criteria_json=payload.criteria.model_dump(),
        status=SearchJobStatus.queued,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Runs AFTER this response is sent back to the client — the client gets
    # an instant "queued" response and polls /progress to watch it move.
    background_tasks.add_task(run_search_job, str(job.id), str(current_user.id))

    return job


@router.get("", response_model=list[SearchJobResponse])
def list_searches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(SearchJob)
        .filter(SearchJob.user_id == current_user.id)
        .order_by(SearchJob.created_at.desc())
        .all()
    )


@router.get("/{search_id}", response_model=SearchJobResponse)
def get_search(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == search_id, SearchJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    return job


@router.get("/{search_id}/progress", response_model=SearchProgressResponse)
def get_progress(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == search_id, SearchJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    return job


@router.post("/{search_id}/cancel", response_model=SearchJobResponse)
def cancel_search(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == search_id, SearchJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    if job.status in (SearchJobStatus.completed, SearchJobStatus.failed):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a job that is already {job.status.value}")
    job.status = SearchJobStatus.cancelled
    db.commit()
    db.refresh(job)
    return job
