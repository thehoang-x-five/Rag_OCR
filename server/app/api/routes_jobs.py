"""
Job management API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse

from app.core.jobs import job_store
from app.models.schemas import JobResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str = Path(..., description="Job ID to check")):
    """
    Get job status and result
    
    - **job_id**: The job ID returned from the extract endpoint
    
    Returns job status, progress, and result (if completed)
    """
    
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(**job.to_dict())


@router.delete("/{job_id}")
async def delete_job(job_id: str = Path(..., description="Job ID to delete")):
    """
    Delete a job and clean up its files
    
    - **job_id**: The job ID to delete
    """
    
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up job files
    from app.utils.files import cleanup_job_files
    cleanup_job_files(job_id)
    
    # Delete job from store
    job_store.delete_job(job_id)
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/")
async def list_jobs():
    """
    List all active jobs
    
    Returns a list of all jobs with their current status
    """
    
    jobs = []
    for job_id, job in job_store.jobs.items():
        jobs.append({
            "jobId": job_id,
            "status": job.status.value,
            "step": job.step.value,
            "percent": job.percent,
            "message": job.message,
            "createdAt": job.created_at.isoformat(),
            "updatedAt": job.updated_at.isoformat()
        })
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }


@router.post("/cleanup")
async def cleanup_old_jobs():
    """
    Manually trigger cleanup of old jobs
    
    Removes jobs older than the configured TTL
    """
    
    initial_count = len(job_store.jobs)
    job_store.cleanup_old_jobs()
    final_count = len(job_store.jobs)
    cleaned_count = initial_count - final_count
    
    return {
        "message": f"Cleaned up {cleaned_count} old jobs",
        "remainingJobs": final_count
    }