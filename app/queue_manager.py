"""Queue manager for video uploads."""
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import db, Video, UploadJob, VideoStatus
from app.logging_config import log_manager
import logging

logger = log_manager.get_logger(__name__)


class QueueManager:
    """Manages upload queue."""

    def __init__(self):
        """Initialize queue manager."""
        self.session = db.get_session()

    def add_video_to_queue(self, video_id: int, profile_name: str = "default", 
                           scheduled_at: Optional[datetime] = None) -> UploadJob:
        """Add video to upload queue.
        
        Args:
            video_id: ID of video to upload
            profile_name: Browser profile to use
            scheduled_at: When to schedule upload
            
        Returns:
            Created UploadJob
        """
        try:
            # Check if video exists
            video = self.session.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Create upload job
            job = UploadJob(
                video_id=video_id,
                profile_name=profile_name,
                status=VideoStatus.PENDING
            )
            
            if scheduled_at:
                job.scheduled_at = scheduled_at
            
            self.session.add(job)
            self.session.commit()
            
            logger.info(f"Added video {video.filename} to queue (Job {job.id})")
            return job
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding video to queue: {e}")
            raise

    def get_pending_jobs(self, profile_name: str = "default") -> List[UploadJob]:
        """Get pending upload jobs.
        
        Args:
            profile_name: Filter by profile name
            
        Returns:
            List of pending jobs
        """
        jobs = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.PENDING,
            UploadJob.profile_name == profile_name
        ).all()
        return jobs

    def get_next_job(self, profile_name: str = "default") -> Optional[UploadJob]:
        """Get next job to process.
        
        Args:
            profile_name: Filter by profile name
            
        Returns:
            Next UploadJob or None
        """
        job = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.PENDING,
            UploadJob.profile_name == profile_name
        ).order_by(UploadJob.created_at).first()
        return job

    def update_job_status(self, job_id: int, status: VideoStatus, 
                         error_message: Optional[str] = None,
                         result_message: Optional[str] = None,
                         youtube_url: Optional[str] = None):
        """Update job status.
        
        Args:
            job_id: ID of job to update
            status: New status
            error_message: Error message if failed
            result_message: Result message
            youtube_url: URL of uploaded video
        """
        try:
            job = self.session.query(UploadJob).filter(UploadJob.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            job.status = status
            if error_message:
                job.error_message = error_message
            if result_message:
                job.result_message = result_message
            if youtube_url:
                job.youtube_url = youtube_url
            
            if status == VideoStatus.UPLOADING:
                job.started_at = datetime.utcnow()
            elif status in [VideoStatus.COMPLETED, VideoStatus.FAILED]:
                job.completed_at = datetime.utcnow()
            
            self.session.commit()
            logger.info(f"Job {job_id} status updated to {status}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating job status: {e}")
            raise

    def retry_failed_job(self, job_id: int):
        """Retry a failed job.
        
        Args:
            job_id: ID of job to retry
        """
        try:
            job = self.session.query(UploadJob).filter(UploadJob.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            if job.attempt_count < job.max_attempts:
                job.status = VideoStatus.PENDING
                job.error_message = None
                job.attempt_count += 1
                self.session.commit()
                logger.info(f"Job {job_id} retry attempt {job.attempt_count}")
            else:
                logger.warning(f"Job {job_id} exceeded max retries")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error retrying job: {e}")
            raise

    def get_queue_stats(self, profile_name: str = "default") -> dict:
        """Get queue statistics.
        
        Args:
            profile_name: Filter by profile name
            
        Returns:
            Dictionary with queue stats
        """
        pending = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.PENDING,
            UploadJob.profile_name == profile_name
        ).count()
        
        uploading = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.UPLOADING,
            UploadJob.profile_name == profile_name
        ).count()
        
        completed = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.COMPLETED,
            UploadJob.profile_name == profile_name
        ).count()
        
        failed = self.session.query(UploadJob).filter(
            UploadJob.status == VideoStatus.FAILED,
            UploadJob.profile_name == profile_name
        ).count()
        
        return {
            'pending': pending,
            'uploading': uploading,
            'completed': completed,
            'failed': failed,
            'total': pending + uploading + completed + failed
        }

    def clear_completed(self):
        """Clear completed jobs."""
        try:
            self.session.query(UploadJob).filter(
                UploadJob.status == VideoStatus.COMPLETED
            ).delete()
            self.session.commit()
            logger.info("Cleared completed jobs")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing completed jobs: {e}")
            raise

    def pause_job(self, job_id: int):
        """Pause a job.
        
        Args:
            job_id: ID of job to pause
        """
        try:
            job = self.session.query(UploadJob).filter(UploadJob.id == job_id).first()
            if job:
                job.status = VideoStatus.PAUSED
                self.session.commit()
                logger.info(f"Job {job_id} paused")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error pausing job: {e}")
            raise

    def resume_job(self, job_id: int):
        """Resume a paused job.
        
        Args:
            job_id: ID of job to resume
        """
        try:
            job = self.session.query(UploadJob).filter(UploadJob.id == job_id).first()
            if job and job.status == VideoStatus.PAUSED:
                job.status = VideoStatus.PENDING
                self.session.commit()
                logger.info(f"Job {job_id} resumed")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error resuming job: {e}")
            raise

    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
