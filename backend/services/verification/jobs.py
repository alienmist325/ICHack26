"""Background job queue for property verification."""

import asyncio
import uuid
import logging
from datetime import datetime, UTC
from typing import Dict, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationJob:
    """Represents a verification job."""

    def __init__(self, property_id: int):
        self.job_id = str(uuid.uuid4())
        self.property_id = property_id
        self.status = JobStatus.QUEUED
        self.created_at = datetime.now(UTC)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Any = None

    def to_dict(self) -> dict:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "property_id": self.property_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error": self.error,
            "result": self.result,
        }


class JobQueue:
    """In-memory async job queue for property verification."""

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize job queue.

        Args:
            max_concurrent: Maximum concurrent jobs (default: 5)
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, VerificationJob] = {}
        self.max_concurrent = max_concurrent
        self.active_jobs = 0
        self.lock = asyncio.Lock()
        self.worker_task: Optional[asyncio.Task] = None

    async def enqueue(self, property_id: int) -> VerificationJob:
        """
        Enqueue a property for verification.

        Args:
            property_id: Property ID to verify

        Returns:
            VerificationJob object
        """
        job = VerificationJob(property_id)
        self.jobs[job.job_id] = job

        await self.queue.put(job)
        logger.info(f"Job {job.job_id} enqueued for property {property_id}")

        return job

    async def get_job(self, job_id: str) -> Optional[VerificationJob]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            VerificationJob or None if not found
        """
        return self.jobs.get(job_id)

    async def process_jobs(self, job_handler: Callable[[VerificationJob], Any]) -> None:
        """
        Start processing jobs from queue.

        Args:
            job_handler: Async callable that processes a job
                         Should handle exceptions and update job status
        """
        logger.info("Job queue worker started")

        while True:
            try:
                # Wait for a job with timeout to allow graceful shutdown
                try:
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Wait if at max concurrent jobs
                async with self.lock:
                    while self.active_jobs >= self.max_concurrent:
                        await asyncio.sleep(0.1)
                    self.active_jobs += 1

                # Process job in background (don't await here)
                asyncio.create_task(self._process_job(job, job_handler))

            except Exception as e:
                logger.error(f"Error in job queue worker: {e}")
                await asyncio.sleep(1)

    async def _process_job(
        self, job: VerificationJob, job_handler: Callable[[VerificationJob], Any]
    ) -> None:
        """
        Process a single job.

        Args:
            job: Job to process
            job_handler: Handler function
        """
        try:
            async with self.lock:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.utcnow()

            logger.info(f"Processing job {job.job_id} for property {job.property_id}")

            # Call handler (async)
            result = await job_handler(job)
            job.result = result
            job.status = JobStatus.COMPLETED

            logger.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            logger.error(f"Job {job.job_id} failed: {e}")

        finally:
            async with self.lock:
                job.completed_at = datetime.utcnow()
                self.active_jobs -= 1

    async def start(self, job_handler: Callable[[VerificationJob], Any]) -> None:
        """
        Start the job queue worker.

        Args:
            job_handler: Async callable to process jobs
        """
        if self.worker_task and not self.worker_task.done():
            logger.warning("Job queue worker already running")
            return

        self.worker_task = asyncio.create_task(self.process_jobs(job_handler))

    async def stop(self) -> None:
        """Stop the job queue worker."""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Job queue worker stopped")

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        return {
            "queue_size": self.queue.qsize(),
            "total_jobs": len(self.jobs),
            "active_jobs": self.active_jobs,
            "max_concurrent": self.max_concurrent,
        }


# Global job queue instance
_job_queue: Optional[JobQueue] = None


async def get_job_queue() -> JobQueue:
    """Get or create global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue(max_concurrent=5)
    return _job_queue


async def init_job_queue(max_concurrent: int = 5) -> JobQueue:
    """
    Initialize global job queue.

    Args:
        max_concurrent: Maximum concurrent jobs

    Returns:
        JobQueue instance
    """
    global _job_queue
    _job_queue = JobQueue(max_concurrent=max_concurrent)
    return _job_queue
