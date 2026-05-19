from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_user_id
from app.database import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    video_storage_path: str


class JobResponse(BaseModel):
    id: str
    status: str
    video_storage_path: str
    created_at: str
    completed_at: str | None
    error_message: str | None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    body: CreateJobRequest,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    result = (
        db.table("jobs")
        .insert({
            "user_id": user_id,
            "video_storage_path": body.video_storage_path,
            "status": "pending",
        })
        .execute()
    )
    job = result.data[0]
    return {"job_id": job["id"]}


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    result = (
        db.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result.data


@router.get("")
def list_jobs(
    user_id: str = Depends(get_current_user_id),
    limit: int = 20,
    offset: int = 0,
):
    db = get_db()
    result = (
        db.table("jobs")
        .select("id, status, video_storage_path, created_at, completed_at, error_message")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {"jobs": result.data, "total": len(result.data)}


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    result = (
        db.table("jobs")
        .select("id")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.table("jobs").delete().eq("id", job_id).execute()
